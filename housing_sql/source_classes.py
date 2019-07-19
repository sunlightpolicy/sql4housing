import urllib.request
import json
import utils
import re
from sqlalchemy.types import Boolean, DateTime, Integer, Numeric, Text
from geoalchemy2.types import Geometry
from bs4 import BeautifulSoup
from sodapy import Socrata

class SocrataPortal:
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
        self.num_rows = None
        self.data = None

    #TO DO Add all socrata methods
    def find_metadata(self):
        self.client = Socrata(self.site, self.app_token)
        self.metadata = self.client.get_metadata(self.dataset_id)['columns'] 
        pass

    def default_tbl_name(self):
        self.tbl_name = utils.get_table_name(
            self.client.get_metadata(self.dataset_id)['name']
            )
        pass

    def __get_socrata_data(self, page_size=5000):
        """Iterate over a datasets pages using the Socrata API"""
        page_num = 0
        more_pages = True

        while more_pages:
            api_data = self.client.get(
                self.dataset_id,
                limit=page_size,
                offset=page_size * page_num,
            )


            if len(api_data) < page_size:
                more_pages = False

            page_num += 1
            yield api_data

    def get_data(self):
        count = self.client.get(self.dataset_id, select='COUNT(*) AS count')
        self.num_rows = int(count[0]['count'])
        self.data = self.__get_socrata_data(5000)
        pass

    def insert(self, circle_bar):
        for page in self.data:
            utils.insert_data(page, self.session, circle_bar, self.binding)
        pass

    def format_col(self, col):
        return col['fieldName'].lower(), col['dataTypeName']

class HudPortal:
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
        self.metadata = None
        self.site = site
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.num_rows = None
        self.data = None

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
        self.data = json.loads(response_geojson.read())['features']
        self.data = [x['properties'] for x in self.data]
        self.num_rows = len(self.data)

    def insert(self, circle_bar):
        utils.insert_data(self.data, self.session, circle_bar, self.binding)
        pass
