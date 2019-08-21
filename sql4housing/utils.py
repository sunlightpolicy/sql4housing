'''
Utility functions
'''
import re
from sqlalchemy.orm import sessionmaker
from progress.bar import FillingCirclesBar
from sqlalchemy.types import DateTime, Text
from geoalchemy2.types import Geometry
import urllib
import json
import string
import warnings

from sql4housing.parsers import parse_datetime, parse_geom, parse_str
from sql4housing import ui

def get_table_name(raw_str):
    '''
    Transform a string into a suitable table name

    Swaps spaces for _s, lowercaes and strips special characters. Ex:
    'Calls to 9-1-1' becomes 'calls_to_911'
    '''
    no_spaces = raw_str.replace(' ', '_')
    return re.sub(r'\W', '', no_spaces).lower()

def insert_data(page, session, circle_bar, Binding, srid=4326, socrata=False):
    '''
    Inserts data into binding after parsing values in each row. Shows progress
    on circle bar.
    '''
    to_insert = []

    for row in page:
        to_insert.append(Binding(**parse_row(row, Binding, srid)))
        if not socrata:
            circle_bar.next()
    session.add_all(to_insert)
    if socrata:
        circle_bar.next(n=len(to_insert))

    return

def clean_string(sub_str):
    return re.compile('[%s]' % re.escape(string.punctuation)).sub(
                "_", sub_str.lower())

def geojson_data(geojson):
    '''
    Parses ['features'] within geojson data and reformats all variable names.
    '''
    ui.item(
        "Gathering data (this can take a bit for large datasets).")
    new_data = []
    data = geojson['features']
    for row in data:
        output = \
            {k.lower().replace(" ", "_"): v \
            for k, v in row['properties'].items()}
        output['geometry'] = row['geometry']
        new_data.append(output)
    return new_data

def edit_columns(df):
    '''
    Reformats columns of a dataframe.
    '''
    df.columns = \
        [col_name.lower().replace(" ", "_") for col_name in df.columns]
    return df

def parse_row(row, binding, srid):
    """Parse API data into the Python types our binding expects"""
    parsers = {
        # TO DO: move to classes
        # This maps SQLAlchemy types (key) to functions that return their
        # expected Python type from the raw Socrata data.
        DateTime: parse_datetime,
        Geometry: parse_geom,
        Text: parse_str,
    }

    parsed = {}
    binding_columns = binding.__mapper__.columns
    for col_name, col_val in row.items():
        col_name = col_name.lower()

        if col_name not in binding_columns:
            # We skipped this column when creating the binding; skip it now too
            continue

        mapper_col_type = type(binding_columns[col_name].type)
        if mapper_col_type in parsers:
            parsed[col_name] = parsers[mapper_col_type](col_val, srid)
        else:
            parsed[col_name] = col_val

    return parsed

def create_metadata(data, mappings):
    '''
    Given a dictionary of data, maps python types of each value to
    SQLAlchemy types.
    '''
    ui.item("Gathering metadata")
    print()
    metadata = []
    for col_name in data[0].keys():

        for record in data:
            if col_name == 'geometry':
                metadata.append(
                    (col_name, Geometry(geometry_type='GEOMETRY', srid=4326)))
                break
            elif record[col_name]:
                try:        
                    py_type = type(record[col_name])
                    print(col_name, ":", py_type)
                    metadata.append((col_name, mappings[py_type]))
                    break
                except KeyError:
                    warnings.warn(
                        'Unable to map "%s" to a SQL type.' % col_name)
                    break
    return metadata

def spreadsheet_metadata(spreadsheet):
    '''
    Given a spreadsheet object, maps column types as interpreted by pandas into
    SQLAlchemy types.
    '''
    ui.item("Gathering metadata")
    print()
    metadata = []
    for col_name, col_type in dict(spreadsheet.df.dtypes).items():
        print(col_name, ":", col_type)
        try:
            metadata.append((col_name, spreadsheet.col_mappings[col_type]))
        except KeyError:
            warnings.warn('Unable to map "%s" to a SQL type.' % col_name)
            continue
    return metadata
