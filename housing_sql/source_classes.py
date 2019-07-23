import urllib.request
import json
import utils
import re
from sqlalchemy.types import Boolean, DateTime, Integer, Numeric, Text
from geoalchemy2.types import Geometry
from bs4 import BeautifulSoup
from sodapy import Socrata
import pandas as pd
import xlrd
import numpy as np

class ExcelFile:
    #TO BE COMPLETED
    def __init__(self, location):
        self.location = location
        self.name = "Excel File"
        self.tbl_name = utils.get_table_name(
            self.xls).sheet_names[0]
        self.db_name = "postgres:///kcmo_db"
        self.session = None
        self.engine = None
        self.geo = None
        self.xls = pd.ExcelFile(urllib.request.urlopen(location))
        self.metadata = [(col_name.lower().replace(" ", "_"), col_type) \
            for (col_name, col_type) in \
            dict(self.xls.parse(self.xls.sheet_names[0]).dtypes).items()]
        self.col_mappings = {np.dtype(object): Text,
            np.dtype(int): Integer,
            np.dtype(float): Numeric,
            np.dtype('<M8[ns]'): DateTime}
        self.binding = None
        self.num_rows = pd.read_excel(self.xls).shape[0]
        self.data = None


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
        self.site = site
        self.name = "Socrata"
        self.db_name = "postgres:///kcmo_db"
        self.dataset_id = dataset_id
        self.app_token = app_token
        self.client = Socrata(self.site, self.app_token)
        self.tbl_name = utils.get_table_name(
            self.client.get_metadata(self.dataset_id)['name']
            )
        self.metadata = [(
            col['fieldName'].lower(), self.col_mappings[col['dataTypeName']]) \
            for col in self.client.get_metadata(self.dataset_id)['columns']]
        self.srid=4326
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.num_rows = int(
            self.client.get(
                self.dataset_id, select='COUNT(*) AS count')[0]['count'])
        self.data = self.__get_socrata_data(5000)

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

    def insert(self, circle_bar):
        for page in self.data:
            utils.insert_data(page, self.session, circle_bar, self.binding, self.srid)
        pass


class HudPortal:
    def __init__(self, site):
        self.site = site
        self.name = "HUD"
        self.db_name = "postgres:///kcmo_db"
        self.description = str(
            urllib.request.urlopen(
                re.search('.*FeatureServer/', self.site).group()
                ).read()
            )        
        self.tbl_name = utils.get_table_name(BeautifulSoup(
            self.description, 'html.parser'
            ).title.string.rstrip(' (FeatureServer)'))        
        self.data_info = json.loads(
            urllib.request.urlopen(
                self.site + "&outFields=*&outSR=4326&f=json").read())
        self.srid = self.data_info['spatialReference']['wkid']
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self._query = '' if "1%3D1" in \
            re.search("where=\S*", self.site).group() else \
            re.search("where=\S*", self.site).group()
        self._dataset_code = re.search(
            'Service ItemId:</b> \w*', self.description).group()[20:]       
        self.data = self._get_data()
        self.num_rows = len(self.data)
        self.col_mappings = {
            'esriFieldTypeString': Text,
            'esriFieldTypeInteger': Integer,
            'esriFieldTypeOID': Integer,
            'esriFieldTypeSmallInteger': Integer,
            'esriFieldTypeDouble': Numeric,
            'esriFieldTypeSingle': Numeric,
            'esriFieldTypeDate': DateTime,
            'esriFieldTypeGlobalID': Text}
        self.metadata = [(col['name'].lower(), self.col_mappings[col['type']]) \
            for col in self.data_info['fields']] + \
                [('geometry', Geometry(
                    geometry_type='GEOMETRY', srid=self.srid))]
    
    def _get_data(self):
        data = json.loads(
            urllib.request.urlopen(
                'https://opendata.arcgis.com/datasets/%s_0.geojson%s' %
                    (self._dataset_code, '?' + self._query)
            ).read())['features']
        new_data = []
        for row in data:
            output = row['properties']
            output['geometry'] = row['geometry']
            new_data.append(output)
        return new_data

    def insert(self, circle_bar):

        utils.insert_data(self.data, self.session, circle_bar, self.binding, self.srid)
        return
