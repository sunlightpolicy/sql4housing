import re
from sqlalchemy.orm import sessionmaker
from progress.bar import FillingCirclesBar
from parsers import parse_datetime, parse_geom, parse_str
from sqlalchemy.types import DateTime, Text
from geoalchemy2.types import Geometry

def get_table_name(raw_str):
    """Transform a string into a suitable table name

    Swaps spaces for _s, lowercaes and strips special characters. Ex:
    'Calls to 9-1-1' becomes 'calls_to_911'
    """
    no_spaces = raw_str.replace(' ', '_')
    return re.sub(r'\W', '', no_spaces).lower()

def insert_data(page, session, circle_bar, Binding, srid=None):
    to_insert = []
    for row in page:
        to_insert.append(Binding(**parse_row(row, Binding, srid)))
    session.add_all(to_insert)
    circle_bar.next(n=len(to_insert))

    return

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
    for col_name, col_val in row.items():
        col_name = col_name.lower()
        binding_columns = binding.__mapper__.columns
        if col_name not in binding_columns:
            # We skipped this column when creating the binding; skip it now too

            continue

        mapper_col_type = type(binding_columns[col_name].type)

        if mapper_col_type in parsers:
            parsed[col_name] = parsers[mapper_col_type](col_val, srid)
        else:
            parsed[col_name] = col_val

    return parsed
