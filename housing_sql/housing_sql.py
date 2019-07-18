"""Housing data to SQL database loader

Load a dataset directly from an API (Socrata, HUD, Census) or file (csv or shp) 
into a SQL database. The loader supports any database supported by SQLalchemy.
This file is adapted from a forked copy of DallasMorningNews/socrata2sql

Usage:
  housing_sql.py hud <site> [-d=<database_url>] [-t=<table_name>]
  housing_sql.py Socrata <site> <dataset_id> [-a=<app_token>] [-d=<database_url>] [-t=<table_name>]
  housing_sql.py Census <dataset> <year> <table> <geography> <api_key> [-d=<database_url>] [-t=<table_name>]
  housing_sql.py csv (<location> | <site>) [-d=<database_url>] [-t=<table_name>]
  housing_sql.py shp (<location> | <site>) [-d=<database_url>] [-t=<table_name>]
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

  Load Sandy Damage Estimates from HUD into a PostgreSQL database called mydb:
  $ housing_sql.py HUD "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/FemaDamageAssessmnts_01172013_new/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json" -d=postgresql:///mydb
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
import source_classes as sc
from exceptions import CLIError
from parsers import parse_datetime
from parsers import parse_geom
from parsers import parse_str
from sources import socrata, hud
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

    for col in source.metadata:
        col_name, col_type = source.format_col(col)

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

            try:
                record_fields[col_name] = Column(
                    source.col_mappings[col_type]
                )
            except KeyError:
                msg = 'Unable to map %s type "%s" to a SQL type.' % (
                    source.name, col_data_type
                )
                raise NotImplementedError(msg)

        except NotImplementedError as e:
            ui.item('%s' % str(e))
            continue

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
    gis_q = 'SELECT PostGIS_version();'
    try:
        source.session.execute(gis_q)
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

    arguments = docopt(__doc__)

    print(arguments)


    try:

        #Get metadata to create binding      
        if arguments['Socrata']:
            source = socrata
            client, metadata = source.find_metadata(
                arguments['<site>'], arguments['<dataset_id>'], arguments['-a']
                )
            dataset_id = arguments['<dataset_id>']

        if arguments['hud']:
            source = sc.Hud(arguments['<site>'])

        source.find_metadata()

        #get defaults
        if arguments['-d']:
            source.db_name = arguments['-d'][1:]

        if arguments['-t']:
            source.tbl_name = arguments['-t'][1:]
        else:
            source.default_tbl_name()

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

        num_rows, data = source.get_data()
        bar = FillingCirclesBar('  ▶ Loading from source', max=num_rows)

        # Iterate the dataset and INSERT each page

        if arguments['Socrata']:
            for page in data:
                insert_data(page, session, bar, Binding)

        if arguments['hud']:
            insert_data(data, source.session, bar, source.binding)

        bar.finish()

        ui.item(
            'Committing rows (this can take a bit for large datasets).'
        )
        source.session.commit()

        success = 'Successfully imported %s rows.' % (
            num_rows
        )
        ui.header(success, color='\033[92m')
        if source.client:
            source.client.close()
    except CLIError as e:
        ui.header(str(e), color='\033[91m')


if __name__ == '__main__':
    main()
