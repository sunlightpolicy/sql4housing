import urllib.request
import json
import utils
import re
from sqlalchemy.types import \
    Boolean, DateTime, Integer, BigInteger, Numeric, Text
from geoalchemy2.types import Geometry
from bs4 import BeautifulSoup
from sodapy import Socrata
import pandas as pd
import xlrd
import numpy as np
import string
import shapefile
import zipfile
import io
import requests

class Spreadsheet:
    def __init__(self, location, has_url):
        self.location = location
        self.has_url = has_url
        self.col_mappings = {np.dtype(object): Text,
            np.dtype('int64'): BigInteger,
            np.dtype('int32'): Integer,
            np.dtype('int16'): Integer,
            np.dtype('int8'): Integer,
            np.dtype(float): Numeric,
            np.dtype('<M8[ns]'): DateTime}       
        self.db_name = "postgres:///kcmo_db"
        self.session = None
        self.engine = None
        self.geo = False
        self.binding = None 

    def insert(self, circle_bar):
        utils.insert_data(self.data, self.session, circle_bar, self.binding)
        return 

class Excel(Spreadsheet):
    '''
    defaults to reading the first sheet
    '''
    def __init__(self, location, has_url):
        Spreadsheet.__init__(self, location, has_url)
        self.xls = pd.ExcelFile(urllib.request.urlopen(location)) if has_url \
            else pd.ExcelFile(location)
        self.df = utils.edit_columns(self.xls.parse())
        self.name = "Excel File"
        self.tbl_name = self.xls.sheet_names[0].lower()
        self.metadata = utils.spreadsheet_metadata(self)
        self.num_rows = self.df.shape[0]
        self.data = self.df.to_dict(orient='records')

class Csv(Spreadsheet):
    def __init__(self, location, has_url):
        Spreadsheet.__init__(self, location, has_url)
        self.df = utils.edit_columns(
            pd.read_csv(urllib.request.urlopen(location)) if has_url \
            else pd.read_csv(location))
        self.name = "CSV file"
        self.tbl_name = self.__create_tbl_name()
        self.metadata = utils.spreadsheet_metadata(self)
        self.num_rows = self.df.shape[0]
        self.data = self.df.to_dict(orient='records')

    def __create_tbl_name(self):
        pattern = "(?:(?<=http://)|(?<=https://))[^\s]+(?=.csv)" if \
            self.has_url else "[^\s]+(?=.csv)"
        sub_str = re.search(pattern, self.location).group().lower()
        return \
            re.compile('[%s]' % re.escape(string.punctuation)).sub("_", sub_str)

class SpatialFile:
    def __init__(self, location, has_url):
        self.location = location
        self.has_url = has_url
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.db_name = "postgres:///kcmo_db"

class Shape(SpatialFile):
    def __init__(self, location, has_url):
        Spatial.__init__(self, location, has_url)
        self.geo_json = self.__extract_file() if has_url \
            else shapefile.Reader(location).__geo_interface__
        self.data = [{k.lower().replace(' ', '_'): v} for k, v in \
            self.geo_json['features'].items()]
        #self.metadata = 

    def __extract_file(self):
        r = requests.get(self.location)
        z = zipfile.ZipFile(io.BytesIO(r.content))
        print("Extracting shapefile to folder")
        z.extractall()
        shp = [y for y in sorted(z.namelist()) for ending in \
            ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)][2]
        return shapefile.Reader(shp).__geo_interface__


class Portal:
    def __init__(self, site):
        self.site = site
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.db_name = "postgres:///kcmo_db"


class SocrataPortal(Portal):
    def __init__(self, site, dataset_id, app_token):
        Portal.__init__(self, site)
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
        self.dataset_id = dataset_id
        self.app_token = app_token
        self.client = Socrata(self.site, self.app_token)
        self.tbl_name = utils.get_table_name(
            self.client.get_metadata(self.dataset_id)['name']
            ).lower()
        self.metadata = self.__get_metadata()
        self.srid=4326

        self.num_rows = int(
            self.client.get(
                self.dataset_id, select='COUNT(*) AS count')[0]['count'])
        self.data = self.__get_socrata_data(5000)

    def __get_metadata(self):

        print("Gathering metadata")
        print() 
        metadata = []
        for col in self.client.get_metadata(self.dataset_id)['columns']:
            print(col['fieldName'], ":", col['dataTypeName'])
            metadata.append(
                (col['fieldName'], self.col_mappings[col['dataTypeName']]))
        return metadata



    def __get_socrata_data(self, page_size=5000):
        """Iterate over a datasets pages using the Socrata API"""
        print("Gathering data")
        print()
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
            utils.insert_data(
                page, self.session, circle_bar, self.binding, self.srid)
        pass


class HudPortal(Portal):
    def __init__(self, site):
        Portal.__init__(self, site)
        self.name = "HUD"
        self.description = str(
            urllib.request.urlopen(
                re.search('.*FeatureServer/', self.site).group()
                ).read()
            )        
        self.tbl_name = utils.get_table_name(BeautifulSoup(
            self.description, 'html.parser'
            ).title.string.rstrip(' (FeatureServer)')).lower()        
        self.data_info = json.loads(
            urllib.request.urlopen(
                self.site + "&outFields=*&outSR=4326&f=json").read())
        self.srid = self.data_info['spatialReference']['wkid']
        self._query = '' if "1%3D1" in \
            re.search("where=\S*", self.site).group() else \
            re.search("where=\S*", self.site).group()
        self._dataset_code = re.search(
            '(?<=Service ItemId:</b> )\w*', self.description).group()      
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
        self.metadata = self.__get_metadata()

    def _get_data(self):
        print("Gathering data")
        print()
        data = json.loads(
            urllib.request.urlopen(
                'https://opendata.arcgis.com/datasets/%s_0.geojson%s' %
                    (self._dataset_code, '?' + self._query)
            ).read())['features']
        new_data = []
        for row in data:
            output = \
                {k.lower().replace(" ", "_"): v \
                for k, v in row['properties'].items()}
            output['geometry'] = row['geometry']
            new_data.append(output)
        return new_data

    def __get_metadata(self):
        print("Gathering metadata")
        print()
        metadata = []
        for col in self.data_info['fields']:
            col_name = col['name'].lower().replace(" ", "_")
            print(col_name, ": ", col['type'])
            metadata.append((col_name, self.col_mappings[col['type']]))
        metadata.append(('geometry', \
            Geometry(geometry_type='GEOMETRY', srid=self.srid)))
        return metadata

    def insert(self, circle_bar):
        print("Inserting data")
        utils.insert_data(
            self.data, self.session, circle_bar, self.binding, self.srid)
        return
