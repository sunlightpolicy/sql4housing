import urllib.request
import utils
import json
import re
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Boolean
from sqlalchemy.types import DateTime
from sqlalchemy.types import Integer
from sqlalchemy.types import Numeric
from sqlalchemy.types import Text
from geoalchemy2.types import Geometry
from sqlalchemy import Column
from bs4 import BeautifulSoup
from sqlalchemy import create_engine
import ui
from sqlalchemy.orm import sessionmaker

class Soc:
    def __init__(self, site, dataset_id, app_token):
        self.col_mappings = {
            'checkbox': Boolean,
            'url': Text,
            'text': Text,
            'number': Numeric,
            'calendar_date': DateTime,
            'point': Geometry(geometry_type='POINT', srid=4326),
            'location': Geometry(geometry_type='POINT', srid=4326),
            'multipolygon': Geometry(geometry_type='MULTIPOLYGON', srid=4326)
            }
        self.name = "Socrata"
        self.db_name = "postgres:///kcmo_db"
        self.dataset_id = dataset_id
        self.app_token = app_token
        self.tbl_name = None
        self.client = None
        self.metadata = None
        self.site = site
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
    #TO DO Add all socrata methods

class Hud:
    def __init__(self, site):
        self.col_mappings = {
            'esriFieldTypeString': Text,
            'esriFieldTypeInteger': Integer,
            'esriFieldTypeOID': Integer,
            'esriFieldTypeSmallInteger': Integer,
            'esriFieldTypeDouble': Numeric,
            'esriFieldTypeSingle': Numeric,
            'esriFieldTypeDate': DateTime,
            'esriFieldTypeGeometry': \
                Geometry(geometry_type='GEOMETRY', srid=4326)
            }
        self.name = "HUD"
        self.db_name = "postgres:///kcmo_db"
        self.tbl_name = None
        self.client = None
        self.metadata = None
        self.site = site
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None

    def format_col(self, col):
        return col['name'].lower(), col['type']

    def get_description(self):
        return str(
            urllib.request.urlopen(
                    re.search('.*FeatureServer/', self.site).group()
                ).read()
            )

    def default_tbl_name(self):
        title = BeautifulSoup(
                self.get_description(), 'html.parser'
            ).title.string
        self.tbl_name = utils.get_table_name(title.rstrip(' (FeatureServer)'))

    def find_metadata(self):
        self.metadata = json.loads(
                urllib.request.urlopen(self.site).read()
            )['fields']
        pass

    def get_data(self):
        query = re.search("\?where=\S*f=json", self.site).group()[:-7]
        dataset_code = re.search(
            'Service ItemId:</b> \w*', self.get_description()
        ).group()[20:]
        geojson = 'https://opendata.arcgis.com/datasets/{}_0.geojson{}'.format(
            dataset_code, query
        )
        response_geojson = urllib.request.urlopen(geojson)
        data = json.loads(response_geojson.read())['features']
        data = [x['properties'] for x in data]
        return len(data), data


