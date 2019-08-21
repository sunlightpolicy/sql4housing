"""Housing data to SQL database loader

Load a dataset directly from an API (Socrata, HUD) or file (csv or shp)
into a SQL database. The loader supports any database supported by SQLalchemy.
This file is adapted from a forked copy of DallasMorningNews/socrata2sql

Usage:
  sql4housing bulk_load
  sql4housing hud <site> [--d=<database_url>] [--t=<table_name>]
  sql4housing socrata <site> <dataset_id> [--a=<app_token>] [--d=<database_url>] [--t=<table_name>]
  sql4housing csv <location> [--d=<database_url>] [--t=<table_name>]
  sql4housing excel <location> [--d=<database_url>] [--t=<table_name>]
  sql4housing shp <location> [--d=<database_url>] [--t=<table_name>]
  sql4housing geojson <location> [--d=<database_url>] [--t=<table_name>]
  sql4housing census (decennial2010 | (acs [--y=<year>])) <variables> (--m=<msa> | --c=<csa> | --n=<county> | --s=<state> | --p=<place>) [--l=<level>] [--d=<database_url>] [--t=<table_name>]
  sql4housing (-h | --help)
  sql4housing (-v | --version)

Options:
  <bulk_load>        Loads all datasets documented within a file entitled bulk_load.yaml.
                     Must be run in the same folder where bulk_load.yaml is saved.
  <site>             The domain for the open data site. For Socrata, this is the
                     URL to the open data portal (Ex: www.dallasopendata.com).
                     For HUD, this is the Query URL as created in the API
                     Explorer portion of each dataset's page on the site
                     https://hudgis-hud.opendata.arcgis.com. See example use cases
                     for detailed instructions.
  <dataset_id>       The ID of the dataset on Socrata's open data site. This is
                     usually a few characters, separated by a hyphen, at the end
                     of the URL. Ex: 64pp-jeba
  <location>         Either the path or download URL where the file can be accessed.
  <variables>.       Census variable codes to be retrieved. (i.e. ['B19013, 'B25064']).
                     Variable codes can be determined via American FactFinder or
                     censusreporter.org.
  --d=<database_url> Database connection string for destination database as
                     diacdlect+driver://username:password@host:port/database.
                     Default: "postgresql:///mydb"
  --t=<table_name>   Destination table in the database. Defaults to a sanitized
                     version of the dataset or file's name.
  --a=<app_token>    App token for the Socrata site. Only necessary for
                     high-volume requests. Default: None
  --y=<year>         Optional year specification for the 5-year American Community
                     survey. Defaults to 2017.
  --m=<msa>          The metropolitan statistical area to include. 
                     Ex: --m="new york-newark-jersey city"
  --c=<csa>          The combined statistical area to include.
                     Ex: --c="New York-Newark, NY-NJ-CT-PA"
  --n=<county>       The county to include.
                     Ex: --n="cook county, IL"
  --s=<state>        The state to include.
                     Ex: --s="illinois"
  --p=<place>        The census place to include.
                     Ex: --p="chicago, IL"
  --l=<level>        The geographic level at which to extract data. i.e. tract,
                     block, county, region, division. Reference cenpy documentation
                     to learn more: https://github.com/cenpy-devs/cenpy
  -h --help          Show this screen.
  -v --version       Show version.

Examples:

  Load the Dallas check register into a local SQLite file (file name chosen
  from the dataset name):
  $ sql4housing socrata www.dallasopendata.com 64pp-jeba

  Load it into a PostgreSQL database called mydb:
  $ sql4housing socrata www.dallasopendata.com 64pp-jeba -d"postgresql:///mydb"

  Load Public Housing Buildings from HUD into a PostgreSQL database called mydb:
  $ sql4housing hud "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Buildings/FeatureServer/0/query?outFields=*&where=1%3D1" -d=postgresql:///mydb

  Load Public Housing Physical Inspection scores into a PostgreSQL database called housingdb:
  $ sql4housing excel "http://www.huduser.org/portal/datasets/pis/public_housing_physical_inspection_scores.xlsx" -d=postgresql:///housingdb
"""
import warnings
from docopt import docopt
from progress.bar import FillingCirclesBar
from sqlalchemy import Column, create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from geoalchemy2.types import Geometry
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Integer
from sqlalchemy_utils import database_exists, create_database
import yaml
from yaml import CLoader as Loader
from requests.exceptions import SSLError

from sql4housing import source_classes as sc
from sql4housing import ui
from sql4housing.exceptions import CLIError
from sql4housing import utils


def get_binding(source):
    '''
    Translate the source's metadata into a SQLAlchemy binding

    This looks at each column type in the metadata and creates a
    SQLAlchemy binding with columns to match. For now it fails loudly if it
    encounters a column type we've yet to map to its SQLAlchemy type.
    '''

    record_fields = {
        '__tablename__': source.tbl_name,
        '_pk_': Column(Integer, primary_key=True)
    }

    ui.header(
        'Setting up new table, "%s", from %s source fields' % (
            source.tbl_name, source.name)
    )

    for col_name, col_type in source.metadata:

        if isinstance(col_type, type(Geometry())) and not source.geo:
            try:
                source.session.execute("CREATE EXTENSION POSTGIS;")
                ui.item(
                    "Adding PostGIS extension to support %s column." \
                    % col_name)
                source.session.commit()
                source.geo = True
            except:
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

            col_name = utils.clean_string(col_name)

            assert (col_type), 'Unable to map %s type to a SQL type.' % (
                source.name)
            record_fields[col_name] = Column(col_type)

        except NotImplementedError as e:
            ui.item('%s' % str(e))

    source.binding = type('DataRecord', (declarative_base(),), record_fields)


def get_connection(source):
    '''
    Get a DB connection from the CLI args or defaults to postgres:///mydb

    '''
    source.engine = create_engine(source.db_name)
    ui.header('Connecting to database %s' % source.db_name)

    if not database_exists(source.engine.url):
        create_database(source.engine.url)
        ui.item("Creating database %s" % source.db_name)

    Session = sessionmaker()
    Session.configure(bind=source.engine)

    source.session = Session()

    gis_q = 'SELECT PostGIS_version();'
    # Check for PostGIS support
    try:
        source.session.execute(gis_q)
        source.geo = True
    except OperationalError:
        source.geo = False
    except ProgrammingError:
        source.geo = False
    source.session.commit()

    if source.geo:
        ui.item(
            'PostGIS is installed. Geometries will be imported '
            'as PostGIS geoms.')


def insert_source(source):
    '''
    Gets the connection and binding and inserts data.
    '''

    get_connection(source)

    if not isinstance(source, sc.CenPy):
        get_binding(source)

    if source.engine.dialect.has_table(source.engine, source.tbl_name):
        print()
        warnings.warn(("Destination table already exists. Current table " +
                       "will be dropped and replaced."))
        print()
        if not isinstance(source, sc.CenPy):
            source.binding.__table__.drop(source.engine)


    try:
        if not isinstance(source, sc.CenPy):
            source.binding.__table__.create(source.engine)
    except ProgrammingError as e:

        raise CLIError('Error creating destination table: %s' % str(e))


    circle_bar = FillingCirclesBar(
        '  ▶ Loading from source', max=source.num_rows)

    source.insert(circle_bar)

    circle_bar.finish()

    ui.item(
        'Committing rows (this can take a bit for large datasets).'
    )
    source.session.commit()

    success = 'Successfully imported %s rows.' % (
        source.num_rows
    )
    ui.header(success, color='\033[92m')
    if source.name == "Socrata" and source.client:
        source.client.close()

    return

def load_yaml():
    output = yaml.load(open('bulk_load.yaml'), Loader=Loader)

    db_name = output['DATABASE']

    source_mapper = {'GEOJSONS': sc.GeoJson,
              'SHAPEFILES': sc.Shape,
              'CSVS': sc.Csv,
              'EXCELS': sc.Excel,
              'HUD_TABLES':sc.HudPortal}

    def parse_items(output_dict):
        try:

            for dataset in output[output_dict]:
                if dataset:
                    location, tbl_name = list(dataset.items())[0]
                    source = source_mapper[output_dict](location)
                    if tbl_name:
                        source.tbl_name = tbl_name
                    if db_name:
                        source.db_name = db_name
                    insert_source(source)
                else:
                    continue
        except Exception as e:

            ui.item(("Skipping %s load due to error: \"%s\". Double check " +
                "formatting of bulk_load.yaml if this was " +
                "unintentional.") % (output_dict, e))
            print()
            pass

    for output_dict in source_mapper.keys():
        parse_items(output_dict)

    try:
        socrata_sites = output.get('SOCRATA').get('sites')
        app_token = output.get('SOCRATA').get('app_token')
        if socrata_sites:
            for site in socrata_sites:
                url = site['url']
                for dataset in site['datasets']:
                    dataset_id, tbl_name = list(dataset.items())[0]
                    source = sc.SocrataPortal(
                        url, dataset_id, app_token, tbl_name)
                    if db_name:
                        source.db_name = db_name
                    if tbl_name:
                        source.tbl_name = tbl_name
                    insert_source(source)
    except Exception as e:
        ui.item(("Skipping Socrata load due to error: \"%s\". Double check " +
            "formatting of bulk_load.yaml if this is was " +
            "unintentional.") \
            % e)
        print()
        pass


    try:
        place_type = output['CENSUS'].get('place_type')
        place_name = output['CENSUS'].get('place_name')
        level = output['CENSUS'].get('level')
        for dataset in output['CENSUS']['datasets']:
            if dataset.get('ACS'):
                product = 'ACS'
            if dataset.get('DECENNIAL2010'):
                product = 'Decennial2010'
            year = dataset[product].get('year')  
            tbl_name = dataset[product]['tbl_name']
            variables = dataset[product]['variables']
            source = sc.CenPy(
                product, year, place_type, place_name, level, variables)
            if db_name:
                source.db_name = db_name
            if tbl_name:
                source.tbl_name = tbl_name
            insert_source(source)
    except Exception as e:        
        ui.item(("Skipping Census load due to error: \"%s\". Double check " +
            "formatting of bulk_load.yaml if this was unintentional.") % e)
        print()
        pass


def main():

    arguments = docopt(__doc__)

    try:

        if arguments['bulk_load']:

            load_yaml()

        else:

        #Create source objects
            if arguments['socrata']:
                source = sc.SocrataPortal(
                    arguments['<site>'], \
                    arguments['<dataset_id>'], \
                    arguments['--a'])

            if arguments['hud']:
                source = sc.HudPortal(arguments['<site>'])

            if arguments['excel']:
                source = sc.Excel(arguments['<location>'])

            if arguments['csv']:
                source = sc.Csv(arguments['<location>'])

            if arguments['shp']:
                source = sc.Shape(arguments['<location>'])

            if arguments['geojson']:
                source = sc.GeoJson(arguments['<location>'])

            if arguments['census']:
                place_mappings = {'--m': 'msa',
                                  '--c': 'csa',
                                  '--n': 'county',
                                  '--s': 'state',
                                  '--p': 'placename'}
                for abb, place in place_mappings.items():
                    if arguments.get(abb):
                        place_type = place_mappings[abb]
                        place_arg = arguments[abb]
                        break
                if arguments['--l']:
                    level = arguments['--l']
                else:
                    level = 'tract'
                if arguments['decennial2010']:
                    source = sc.CenPy(
                        'Decennial2010', None, place_type, place_arg,
                        level, arguments['<variables>'])
                elif arguments['acs']:
                    if arguments['--y']:
                        year = int(arguments['--y'])
                    else:
                        year = None
                    source = sc.CenPy(
                        'ACS', year, place_type,
                        place_arg, level,
                        arguments['<variables>'])

            if arguments['--d']:
                source.db_name = arguments['--d']

            if arguments['--t']:
                source.tbl_name = arguments['--t']

            assert(source), "Source has not been defined."

            insert_source(source)

    except CLIError as e:
        ui.header(str(e), color='\033[91m')



if __name__ == '__main__':
    main()
