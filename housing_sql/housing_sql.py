"""Housing data to SQL database loader

Load a dataset directly from an API (Socrata, HUD, Census) or file (csv or shp) 
into a SQL database. The loader supports any database supported by SQLalchemy.
This file is adapted from a forked copy of DallasMorningNews/socrata2sql

Usage:
  housing_sql.py hud <site> [-d=<database_url>] [-t=<table_name>]
  housing_sql.py socrata <site> <dataset_id> [-a=<app_token>] [-d=<database_url>] [-t=<table_name>]
  housing_sql.py census <dataset> <year> <table> <geography> <api_key> [-d=<database_url>] [-t=<table_name>]
  housing_sql.py csv (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
  housing_sql.py excel (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
  housing_sql.py shp (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
  housing_sql.py (-h | --help)
  housing_sql.py (-v | --version)

Options:
  <site>             The domain for the open data site. For Socrata, this is the
                     URL to the open data portal (Ex: www.dallasopendata.com).
                     For HUD, this is the Query URL as created in the API
                     Explorer portion of each dataset's page on the site
                     https://hudgis-hud.opendata.arcgis.com.
  <dataset_id>       The ID of the dataset on Socrata's open data site. This is 
                     usually a few characters, separated by a hyphen, at the end 
                     of the URL. Ex: 64pp-jeba
  -p=<path>          Path to the location where the file is stored.
  -u=<url>           URL hyperlink where file can be downloaded.
  -d=<database_url>  Database connection string for destination database as
                     diacdlect+driver://username:password@host:port/database.
                     Default: sqlite:///<source name>.sqlite
  -t=<table_name>    Destination table in the database. Defaults to a sanitized
                     version of the dataset or file's name.
  -a=<app_token>     App token for the Socrata site. Only necessary for
                     high-volume requests. Default: None
  -h --help          Show this screen.
  -v --version       Show version.

Examples:

  Load the Dallas check register into a local SQLite file (file name chosen
  from the dataset name):
  $ housing_sql.py Socrata www.dallasopendata.com 64pp-jeba

  Load it into a PostgreSQL database called mydb:
  $ housing_sql.py Socrata www.dallasopendata.com 64pp-jeba -d"postgresql:///mydb"

  Load Public Housing Buildings from HUD into a PostgreSQL database called mydb:
  $ housing_sql.py hud "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Buildings/FeatureServer/0/query?outFields=*&where=1%3D1" -d=postgresql:///mydb
"""
from docopt import docopt
from progress.bar import FillingCirclesBar
from sqlalchemy import Column
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError, ProgrammingError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.types import Integer

#from socrata2sql.socrata2sql import __version__
import source_classes as sc
from exceptions import CLIError
import ui


def get_binding(source):
    """Translate the Socrata API metadata into a SQLAlchemy binding

    This looks at each column type in the Socrata API response and creates a
    SQLAlchemy binding with columns to match. For now it fails loudly if it
    encounters a column type we've yet to map to its SQLAlchemy type."""

    record_fields = {
        '__tablename__': source.tbl_name,
        '_pk_': Column(Integer, primary_key=True)
    }

    ui.header(
        'Setting up new table, "%s", from %s source fields' % (source.tbl_name, source.name)
    )

    geo_types = ('location', 'point', 'multipolygon', 'esriFieldTypeGeometry')

    for col_name, col_type in source.metadata:
        
        if col_type in geo_types and source.geo is False:
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
          assert (col_type), 'Unable to map %s type to a SQL type.' % (
                  source.name)

          record_fields[col_name] = Column(col_type)

        except NotImplementedError as e:
            ui.item('%s' % str(e))

    source.binding = type('DataRecord', (declarative_base(),), record_fields)


def get_connection(source):
    """Get a DB connection from the CLI args and Socrata API metadata

    Uess the DB URL passed in by the user to generate a database connection.
    By default, returns a local SQLite database."""
    source.engine = create_engine(source.db_name)
    ui.header('Connecting to database')


    Session = sessionmaker()
    Session.configure(bind=source.engine)

    source.session = Session()

    # Check for PostGIS support
    try:
        source.session.execute('SELECT PostGIS_version();')
        source.geo = True
    except OperationalError:
        source.geo = False
    except ProgrammingError:
        source.geo = False
    finally:
        source.session.commit()

    if source.geo:
        ui.item(
            'PostGIS is installed. Geometries will be imported '
            'as PostGIS geoms.'
        )
    else:
        ui.item('Query "%s" failed. Geometry columns will be skipped.' % gis_q)


def main():

    arguments = docopt(__doc__)

    print(arguments)

    try:

        #Create source objects    
        if arguments['socrata']:
            source = sc.SocrataPortal(
                arguments['<site>'], arguments['<dataset_id>'], \
                (arguments['-a'][1:] if arguments['-a'] else None)
            )

        if arguments['hud']:
            source = sc.HudPortal(arguments['<site>'])

        #get defaults
        if arguments['-d']:
            source.db_name = arguments['-d'][1:]

        if arguments['-t']:
            source.tbl_name = arguments['-t'][1:]

        get_connection(source)
        get_binding(source)

        # Create the table
        try:
            source.binding.__table__.create(source.engine)
        except ProgrammingError as e:
            # Catch these here because this is our first attempt to
            # actually use the DB
            if 'already exists' in str(e):
                raise CLIError(
                    'Destination table already exists. Specify a new table'
                    ' name with -t.'
                )
            raise CLIError('Error creating destination table: %s' % str(e))

        circle_bar = FillingCirclesBar('  ▶ Loading from source', max=source.num_rows)

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
    except CLIError as e:
        ui.header(str(e), color='\033[91m')


if __name__ == '__main__':
    main()
