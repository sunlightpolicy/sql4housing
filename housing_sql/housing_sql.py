"""Housing data to SQL database loader

Load a dataset from the Socrata API or HUD's open data portal into a SQL database.
The loader supports any database supported by SQLalchemy.
This file is adapted from a forked copy of DallasMorningNews/socrata2sql

Usage:
  housing_sql.py insert (--HUD <site> | --Socrata <site> <dataset_id> [-a=<app_token>]) [-d=<database_url>] [-t=<table_name>]
  housing_sql.py ls <site> [-a=<app_token>]
  housing_sql.py (-h | --help)
  housing_sql.py(-v | --version)

Options:
  <site>             The domain for the open data site. Ex: www.dallasopendata.com
  <dataset_id>       The ID of the dataset on Socrata's open data site. This is usually
                     a few characters, separated by a hyphen, at the end of the
                     URL. Ex: 64pp-jeba
  -d=<database_url>  Database connection string for destination database as
                     diacdlect+driver://username:password@host:port/database.
                     Default: sqlite:///<dataset name>.sqlite
  -t=<table_name>    Destination table in the database. Defaults to a sanitized
                     version of the dataset's name on Socrata.
  -a=<app_token>     App token for the site. Only necessary for high-volume
                     requests. Default: None
  -h --help          Show this screen.
  -v --version       Show version.

Examples:
  List all datasets on the Dallas open data portal:
  $ housing_sql.py ls www.dallasopendata.com

  Load the Dallas check register into a local SQLite file (file name chosen
  from the dataset name):
  $ housing_sql.py insert --Socrata www.dallasopendata.com 64pp-jeba

  Load it into a PostgreSQL database called mydb:
  $ housing_sql.py insert --Socrata www.dallasopendata.com 64pp-jeba -d"postgresql:///mydb"

  Load Sandy Damage Estimates from HUD into a PostgreSQL database called mydb:
  $ housing_sql.py insert --HUD "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/FemaDamageAssessmnts_01172013_new/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json" -d"postgresql:///mydb"
"""
from os import path
import re
import json
import urllib.request

from docopt import docopt
from geoalchemy2.types import Geometry
from progress.bar import FillingCirclesBar
from sodapy import Socrata
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Numeric
from sqlalchemy.types import Text
from tabulate import tabulate

#from socrata2sql.socrata2sql import __version__
from exceptions import CLIError
from parsers import parse_datetime
from parsers import parse_geom
from parsers import parse_str
import ui


def get_sql_col(col_data_type, api):
    """Map a Socrata column or esriFieldType type to a SQLalchemy column class"""
    col_mappings = {
        "Socrata": {
            'checkbox': Boolean,
            'url': Text,
            'text': Text,
            'number': Numeric,
            'calendar_date': DateTime,
            'point': Geometry(geometry_type='POINT', srid=4326),
            'location': Geometry(geometry_type='POINT', srid=4326),
            'multipolygon': Geometry(geometry_type='MULTIPOLYGON', srid=4326)
        },
        "HUD": {
            'esriFieldTypeString': Text,
            'esriFieldTypeInteger': Integer,
            'esriFieldTypeOID': Integer,
            'esriFieldTypeSmallInteger': Integer,
            'esriFieldTypeDouble': Numeric,
            'esriFieldTypeSingle': Numeric,
            'esriFieldTypeDate': DateTime,
            'esriFieldTypeGeometry': \
                Geometry(geometry_type='GEOMETRY', srid=4326),
        }
    }

    try:
        return Column(col_mappings[api][col_data_type])
    except KeyError:
        msg = 'Unable to map %s type "%s" to a SQL type.' % (api, col_data_type)
        raise NotImplementedError(msg)


def get_table_name(raw_str):
    """Transform a string into a suitable table name

    Swaps spaces for _s, lowercaes and strips special characters. Ex:
    'Calls to 9-1-1' becomes 'calls_to_911'
    """
    no_spaces = raw_str.replace(' ', '_')
    return re.sub(r'\W',  '', no_spaces).lower()


def default_db_str(dataset_metadata):
    """Create connection string to a local SQLite database from dataset name"""
    dataset_slug = get_table_name(dataset_metadata['name'])
    db_filename = '%s.sqlite' % dataset_slug

    if path.isfile(db_filename):
        msg_tpl = (
            '%s already exists. Specify a unique database name with -d. '
            'Example: -d sqlite:///unique_name.sqlite'
        )
        raise CLIError(msg_tpl % db_filename)

    return 'sqlite:///%s' % db_filename


def get_binding(dataset_metadata, geo, dest, api):
    """Translate the Socrata API metadata into a SQLAlchemy binding

    This looks at each column type in the Socrata API response and creates a
    SQLAlchemy binding with columns to match. For now it fails loudly if it
    encounters a column type we've yet to map to its SQLAlchemy type."""
    if dest:
        table_name = dest        
    elif api == "Socrata":
        table_name = get_table_name(dataset_metadata['name'])

    record_fields = {
        '__tablename__': table_name,
        '_pk_': Column(Integer, primary_key=True)
    }

    ui.header(
        'Setting up new table, "%s", from %s API fields' % (table_name, api)
    )

    geo_types = ('location', 'point', 'multipolygon', 'esriFieldTypeGeometry')

    for col in dataset_metadata:
        if api == "Socrata":
            col_name = col['fieldName'].lower()
            col_type = col['dataTypeName']
        elif api == "HUD":
            col_name = col['name'].lower()
            col_type = col['type']

        if col_type in geo_types and geo is False:
            msg = (
                '"%s" is a %s column but your database doesn\'t support '
                'PostGIS so it\'ll be skipped.'
            ) % (col_name, col_type,)
            ui.item(msg)
            continue

        if col_name.startswith(':@computed'):
            ui.item('Ignoring computed column "%s".' % col_name)
            continue

        try:
            print(col_name, ": ", col_type)
            record_fields[col_name] = get_sql_col(col_type, api)

        except NotImplementedError as e:
            ui.item('%s' % str(e))
            continue

    return type('SocrataRecord', (declarative_base(),), record_fields)


def get_connection(db_str, dataset_metadata):
    """Get a DB connection from the CLI args and Socrata API metadata

    Uess the DB URL passed in by the user to generate a database connection.
    By default, returns a local SQLite database."""
    if db_str:
        engine = create_engine(db_str)
        ui.header('Connecting to database')
    else:
        default = default_db_str(dataset_metadata)
        ui.header('Connecting to database')
        engine = create_engine(default)
        ui.item('Using default SQLite database "%s".' % default)

    Session = sessionmaker()
    Session.configure(bind=engine)

    session = Session()

    # Check for PostGIS support
    gis_q = 'SELECT PostGIS_version();'
    try:
        session.execute(gis_q)
        geo_enabled = True
    except OperationalError:
        geo_enabled = False
    except ProgrammingError:
        geo_enabled = False
    finally:
        session.commit()

    if geo_enabled:
        ui.item(
            'PostGIS is installed. Geometries will be imported '
            'as PostGIS geoms.'
        )
    else:
        ui.item('Query "%s" failed. Geometry columns will be skipped.' % gis_q)

    return engine, session, geo_enabled


def get_data(api, dataset_id, socrata_client=None):
    """Get the row count of a dataset and the dataset itself"""
    if api == "Socrata":
        count = socrata_client.get(
           dataset_id,
            select='COUNT(*) AS count'
        )
        return int(count[0]['count']), \
               get_socrata_data(socrata_client, dataset_id)

    if api == "HUD":
        response_text = str(
            urllib.request.urlopen(
                re.search('.*FeatureServer/', dataset_id).group()
            ).read()
        )
        dataset_code = re.search(
            'Service ItemId:</b> \w*', response_text
        ).group()[20:]
        geojson = 'https://opendata.arcgis.com/datasets/{}_0.geojson'.format(
            dataset_code
        )
        print(geojson)
        response_geojson = urllib.request.urlopen(geojson)
        data = json.loads(response_geojson.read())['features']
        data = [x['properties'] for x in data]
        return len(data), data


def get_socrata_data(socrata_client, dataset_id, page_size=5000):
    """Iterate over a datasets pages using the Socrata API"""
    page_num = 0
    more_pages = True

    while more_pages:
        api_data = socrata_client.get(
            dataset_id,
            limit=page_size,
            offset=page_size * page_num,
        )

        if len(api_data) < page_size:
            more_pages = False

        page_num += 1
        yield api_data


def list_datasets(socrata_client, domain):
    """List all datasets on a portal using the Socrata API"""
    all_metadata = socrata_client.datasets(domains=[domain], only=['dataset'])

    key_fields = []
    for dataset in all_metadata:
        # Simplify the metadata returned by the API
        key_fields.append({
            'Name': dataset['resource']['name'],
            'Category': dataset['classification'].get('domain_category'),
            'ID': dataset['resource']['id'],
            'URL': dataset['permalink']
        })

    return sorted(key_fields, key=lambda _: _['Name'].lower())


def parse_row(row, binding):
    """Parse API data into the Python types our binding expects"""
    parsers = {
        # This maps SQLAlchemy types (key) to functions that return their
        # expected Python type from the raw Socrata data.
        DateTime: parse_datetime,
        Geometry: parse_geom,
        Text: parse_str,
    }

    parsed = {}
    for col_name, col_val in row.items():
        col_name = col_name.lower()
        binding_columns = binding.__mapper__.columns

        if col_name not in binding_columns:
            # We skipped this column when creating the binding; skip it now too
            continue

        mapper_col_type = type(binding_columns[col_name].type)

        if mapper_col_type in parsers:
            parsed[col_name] = parsers[mapper_col_type](col_val)
        else:
            parsed[col_name] = col_val

    return parsed

def insert_data(page, session, bar, Binding):
    to_insert = []
    for row in page:
        to_insert.append(Binding(**parse_row(row, Binding)))
    session.add_all(to_insert)
    bar.next(n=len(to_insert))
    return


def main():

    # TO DO Set up CLI in docopt. For now, pass a dictionary.
    arguments = docopt(__doc__)

    if arguments['--HUD']:
        api = "HUD"
    if arguments['--Socrata']:
        api = "Socrata"

    site = arguments['<site>']
    if api == "Socrata":
        client = Socrata(site, arguments.get('-a'))
    if api == "HUD":
        dataset_id = site
        client = None

    try:
        if arguments.get('ls'):
            datasets = list_datasets(client, arguments['<site>'])
            print(tabulate(datasets, headers='keys', tablefmt='psql'))
        elif arguments.get('insert'):        
            if api == "Socrata":
                assert(arguments['<dataset_id>']), \
                    "Dataset ID is required on the Socrata API"
                dataset_id = arguments['<dataset_id>']
                metadata = client.get_metadata(dataset_id)['columns']
            if api == "HUD":
                metadata = json.loads(
                    urllib.request.urlopen(site).read())['fields']

            engine, session, geo = get_connection(arguments['-d'], metadata)
            
            print("getting binding")
            Binding = get_binding(
                metadata, geo, arguments['-t'], api
            )

            # Create the table
            try:
                Binding.__table__.create(engine)
            except ProgrammingError as e:
                # Catch these here because this is our first attempt to
                # actually use the DB
                if 'already exists' in str(e):
                    raise CLIError(
                        'Destination table already exists. Specify a new table'
                        ' name with -t.'
                    )
                raise CLIError('Error creating destination table: %s' % str(e))

            num_rows, data = get_data(api, dataset_id, client)
            bar = FillingCirclesBar('  ▶ Loading from API', max=num_rows)

            # Iterate the dataset and INSERT each page
            if api == "Socrata":
                for page in data:
                    insert_data(page, session, bar, Binding)

            if api == "HUD":
                insert_data(data, session, bar, Binding)

            bar.finish()

            ui.item(
                'Committing rows (this can take a bit for large datasets).'
            )
            session.commit()

            success = 'Successfully imported %s rows.' % (
                num_rows
            )
            ui.header(success, color='\033[92m')
        if client:
            client.close()
    except CLIError as e:
        ui.header(str(e), color='\033[91m')


if __name__ == '__main__':
    main()
