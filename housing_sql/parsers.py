from datetime import datetime
import json
from shapely.geometry import shape
from geomet import wkt


def parse_datetime(str_val, srid=None):
    """Parse a Socrata floating timestamp field into a Python datetime

    See https://dev.socrata.com/docs/datatypes/floating_timestamp.html"""
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
    """Parse a variety of Socrata location types into EWKT strings

    See https://dev.socrata.com/docs/datatypes/location.html and
    https://dev.socrata.com/docs/datatypes/point.html
    """
    if geo_data is None:
        return None
    '''
    if 'latitude' in geo_data and 'longitude' in geo_data:
        return 'SRID=4326;POINT(%s %s)' % (
            geo_data['latitude'],
            geo_data['longitude'],
        )
    elif 'human_address' in geo_data and 'latitude' not in geo_data:
        return None

    if geo_data['type'] == 'Point':
        return 'SRID=4326;POINT(%s %s)' % (
            geo_data['coordinates'][0],
            geo_data['coordinates'][1],
        )
    '''

    #try:

    '''
    if geo_data['type'] == 'MultiPolygon':
        wkt_text = wkt.dumps(geo_data)
    else:
        wkt_text = shape(geo_data).wkt
    if geo_data['type'] == 'Polygon':
        wkt_text = wkt_text.replace('POLYGON', 'MULTIPOLYGON(') + ')'
    '''
    return ";".join(["SRID=%s" % srid, shape(geo_data).wkt])
    #except:

    #   raise NotImplementedError('%s are not yet supported' % geo_data['type'])


def parse_str(raw_str, srid=None):
    if isinstance(raw_str, dict):
        if 'url' in raw_str:
            return raw_str['url']

        return json.dumps(raw_str)

    return raw_str
