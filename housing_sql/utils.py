import re
from sqlalchemy.orm import sessionmaker
from progress.bar import FillingCirclesBar
from parsers import parse_datetime, parse_geom, parse_str
from sqlalchemy.types import DateTime, Text
from geoalchemy2.types import Geometry
import urllib
import json
import ui
import warnings

def get_table_name(raw_str):
    """Transform a string into a suitable table name

    Swaps spaces for _s, lowercaes and strips special characters. Ex:
    'Calls to 9-1-1' becomes 'calls_to_911'
    """
    no_spaces = raw_str.replace(' ', '_')
    return re.sub(r'\W', '', no_spaces).lower()

def insert_data(page, session, circle_bar, Binding, srid=4326, socrata=False):
    to_insert = []

    for row in page:
        to_insert.append(Binding(**parse_row(row, Binding, srid)))
        if not socrata:
            circle_bar.next()
    session.add_all(to_insert)
    if socrata:
        circle_bar.next(n=len(to_insert))

    return

def geojson_data(geojson):
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

def convert_types(string):
    '''
    Takes a string and returns the type it represents.
    i.e. '500 w addison st' returns str, '80.4' returns float, '5' returns int.
    '''

    for c in [int, float, str]:
        try:
            return c(val)
        except ValueError:
            pass
    return val

def create_metadata(data, mappings):
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
                    warnings.warn('Unable to map "%s" to a SQL type.' % col_name)
                    break
    return metadata

def spreadsheet_metadata(spreadsheet):
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

