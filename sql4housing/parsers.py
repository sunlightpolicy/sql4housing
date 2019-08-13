from datetime import datetime
import json
from shapely.geometry import shape
from geomet import wkt
import pandas as pd


def parse_datetime(str_val, srid=None):
    """Parse a Socrata floating timestamp field into a Python datetime

    See https://dev.socrata.com/docs/datatypes/floating_timestamp.html"""

    if type(str_val) == pd.Timestamp:
        return str_val.to_pydatetime()
    if pd.isna(str_val):
        return None
    if str_val == '' or not str_val:
        return None
    if str_val[-1] == "Z":
        str_val = str_val[:-1]

    try:
        # Socrata >=2.1
        return datetime.strptime(str_val, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        # Socrata <2.1
        return datetime.strptime(str_val, "%Y-%m-%dT%H:%M:%S")


def parse_geom(geo_data, srid):
    """
    TO DO: add code to parse other socrata geometry types
    make parsers object oriented
    """

    if geo_data is None:
        return None
    
    if 'latitude' in geo_data and 'longitude' in geo_data:
        return 'SRID=%s;POINT(%s %s)' % (
            srid,
            geo_data['longitude'],
            geo_data['latitude'],
        )
    elif 'human_address' in geo_data and 'latitude' not in geo_data:
        return None
    else:
        wkt_text = shape(geo_data).wkt

        return ";".join(["SRID=%s" % srid, shape(geo_data).wkt])

def parse_str(raw_str, srid=None):
    if raw_str == "nan":
        return None

    if isinstance(raw_str, dict):
        if 'url' in raw_str:
            return raw_str['url']

        return json.dumps(raw_str)

    return raw_str
