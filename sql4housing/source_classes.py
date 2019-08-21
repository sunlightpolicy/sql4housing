'''
Classes to represent each data source.
'''
import urllib.request
import json
import re
from sqlalchemy.types import \
    Boolean, DateTime, Integer, BigInteger, Numeric, Text
from geoalchemy2.types import Geometry
from geopandas_postgis import PostGIS
from bs4 import BeautifulSoup
from sodapy import Socrata
from cenpy import products
import pandas as pd
import numpy as np
import string
import shapefile
import zipfile
import io
import requests
import time
import warnings
from sql4housing import utils
from sql4housing import ui

class Spreadsheet:
    '''
    Parent class of Excel and Csv.
    Uses pandas to read data and interpret data types.
    '''
    def __init__(self, location):
        self.location = location
        self.col_mappings = {np.dtype(object): Text,
                             np.dtype('int64'): BigInteger,
                             np.dtype('int32'): Integer,
                             np.dtype('int16'): Integer,
                             np.dtype('int8'): Integer,
                             np.dtype(float): Numeric,
                             np.dtype('<M8[ns]'): DateTime,
                             np.dtype('bool'): Boolean}    
        self.db_name = "postgresql:///mydb"
        self.session = None
        self.engine = None
        self.geo = False
        self.binding = None
        self.data = None

    def insert(self, circle_bar):
        utils.insert_data(self.data, self.session, circle_bar, self.binding)

class Excel(Spreadsheet):
    '''
    Stores Excel file data.
    Defaults to reading the first sheet and using the first sheet's name
    as the table name.
    '''
    def __init__(self, location):
        Spreadsheet.__init__(self, location)
        self.xls = pd.ExcelFile(location)
        self.df = utils.edit_columns(self.xls.parse())
        self.name = "Excel File"
        self.tbl_name = self.xls.sheet_names[0].lower()
        self.metadata = utils.spreadsheet_metadata(self)
        self.num_rows = self.df.shape[0]
        self.data = self.df.to_dict(orient='records')

class Csv(Spreadsheet):
    '''
    Stores csv file data.
    Defaults to a sanitized version of the hyperlink or path as the table name.
    '''
    def __init__(self, location):
        Spreadsheet.__init__(self, location)
        self.df = pd.read_csv(location)
        self.name = "CSV file"
        self.tbl_name = self.__create_tbl_name()
        self.metadata = utils.spreadsheet_metadata(self)
        self.num_rows = self.df.shape[0]
        self.data = self.df.to_dict(orient='records')

    def __create_tbl_name(self):


        pattern = "(?:(?<=http://)|(?<=https://))[^\s]+(?=\.csv)"
        sub_str = re.search(pattern, self.location)

        if not sub_str:
            pattern = "[^\s]+(?=\.csv)"
            sub_str = re.search(pattern, self.location).group()
        else:
            sub_str = sub_str.group()

        return utils.clean_string(sub_str)

class SpatialFile:
    '''
    Parent class of Shape and GeoJson
    '''
    def __init__(self, location):
        self.location = location
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.db_name = "postgresql:///mydb"
        self.col_mappings = {
            str: Text,
            int : Integer,
            float: Numeric,
            bool: Boolean}

class Shape(SpatialFile):
    '''
    Stores shapefile data.
    '''
    def __init__(self, location):
        SpatialFile.__init__(self, location)
        self.name = "Shapefile"
        self.tbl_name, self.geojson = self.__extract_file()
        self.data = utils.geojson_data(self.geojson)
        self.metadata = utils.create_metadata(self.data, self.col_mappings)
        self.num_rows = len(self.data)

    def __extract_file(self):
        '''
        Extracts data from zip files if a hyperlink is provided and reads
        the saved shp file. Creates the default table name using a sanitized
        version of the file's name.
        '''
        try:
            z = zipfile.ZipFile(io.BytesIO(requests.get(self.location).content))
            ui.item("Extracting shapefile to folder")
            z.extractall()
            shp = [y for y in sorted(z.namelist()) for ending in \
            ['dbf', 'prj', 'shp', 'shx'] if y.endswith(ending)][2]

        except:
            shp = self.location

        ui.item("Reading shapefile")
        #set default table name
        tbl_name = shp[shp.rfind("/") + 1:-4].lower()
        tbl_name = utils.clean_string(tbl_name)
        return tbl_name, shapefile.Reader(shp).__geo_interface__


    def insert(self, circle_bar):
        utils.insert_data(
            self.data, self.session, circle_bar, self.binding)
        return

class GeoJson(SpatialFile):
    '''
    Stores geojson data
    '''
    def __init__(self, location):
        SpatialFile.__init__(self, location)
        self.name = "GeoJSON"
        self.data = self.__get_data()
        self.metadata = utils.create_metadata(self.data, self.col_mappings)
        self.num_rows = len(self.data)
        self.tbl_name = self.__create_tbl_name()

    def insert(self, circle_bar):
        utils.insert_data(
            self.data, self.session, circle_bar, self.binding)
        return

    def __get_data(self):
        try:
            return utils.geojson_data(json.loads(self.location))
        except:
            
            return utils.geojson_data(
                json.loads(urllib.request.urlopen(self.location).read()))


    def __create_tbl_name(self):
        '''
        Creates the default table name using a sanitized version of the
        hyperlink or file name.
        '''
        pattern = ("(?:(?<=http://)|(?<=https://))[^\s]+(?:" + \
        "(?=geojson)|(?=\?method=export&format=GeoJSON))")

        sub_str = re.search(pattern, self.location)

        if not sub_str:
            pattern = ("[^\s]+(?:" + \
            "(?=\.geojson)|(?=\?method=export&format=GeoJSON))")
            sub_str = re.search(pattern, self.location)
        sub_str = sub_str.group().lower()
        return utils.clean_string(sub_str)

class CenPy:
    '''
    Parent class of Shape and GeoJson
    '''
    def __init__(self, product, year, place_type, place, level, variables):
        self.name = product
        self.tbl_name = "_".join([product, str(year)]).lower().strip()
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.db_name = "postgresql:///mydb"
        self.df = self.create_df(
            product, year, place_type, place, level, variables)
        self.num_rows = self.df.shape[0]

    def create_df(self, product, year, place_type, place, level, variables):
        if product == 'Decennial2010':
            cen_prod = products.Decennial2010()
        elif product == 'ACS' and year:
            cen_prod = products.ACS(year)
        elif product == 'ACS':
            cen_prod = products.ACS()

        place_mapper = {'msa': cen_prod.from_msa,
                        'csa': cen_prod.from_csa,
                        'county': cen_prod.from_county,
                        'state': cen_prod.from_state,
                        'placename': cen_prod.from_place}
        ui.item(("Retrieving variables %s for all %ss in %s. " +
            "This can take some time for large datasets.") % \
            (variables, level, place))
        print()
        print(place, level, variables)
        df = place_mapper[place_type](
            place, level=level, variables=variables)
        df.columns = [utils.clean_string(x) for x in df.columns]
        return df

    def insert(self, circle_bar):
        ui.item("Inserting into PostGIS.")
        self.df.postgis.to_postgis(con=self.engine, table_name=self.tbl_name,
            geometry='geometry', if_exists='replace')


class Portal:
    '''
    Parent class of SocrataPortal and HudPortal.
    '''
    def __init__(self, site):
        self.site = site
        self.engine = None
        self.session = None
        self.geo = None
        self.binding = None
        self.db_name = "postgresql:///mydb"


class SocrataPortal(Portal):
    '''
    Stores SODA data.
    '''
    def __init__(self, site, dataset_id, app_token, tbl_name=None):
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
            ).lower() if not tbl_name else tbl_name
        self.metadata = self.__get_metadata()
        self.srid = 4326

        self.num_rows = int(
            self.client.get(
                self.dataset_id, select='COUNT(*) AS count'))[0]['count']
        self.data = self.__get_socrata_data(5000)

    def __get_metadata(self):
        '''
        Uses provided metadata to map column types to SQLAlchemy.
        '''
        ui.item("Gathering metadata")
        print()
        metadata = []
        for col in self.client.get_metadata(self.dataset_id)['columns']:
            print(col['fieldName'], ":", col['dataTypeName'])
            try:
                metadata.append(
                    (col['fieldName'], self.col_mappings[col['dataTypeName']]))
            except KeyError:
                warnings.warn(
                    'Unable to map "%s" to a SQL type.' % col['fieldName'])
                continue
        return metadata



    def __get_socrata_data(self, page_size=5000):
        '''
        Iterate over a datasets pages using the Socrata API
        '''
        ui.item(
            "Gathering data (this can take a bit for large datasets).")
        page_num = 0
        more_pages = True

        while more_pages:
            try:

                api_data = self.client.get(
                    self.dataset_id,
                    limit=page_size,
                    offset=page_size * page_num,
                )

                if len(api_data) < page_size:
                    more_pages = False
                page_num += 1
                yield api_data

            except:
                ui.item("Sleeping for 10 seconds to avoid timeout")
                time.sleep(10)

    def insert(self, circle_bar):
        for page in self.data:
            utils.insert_data(
                page, self.session, circle_bar, self.binding, srid=self.srid, \
                socrata=True)
        pass


class HudPortal(Portal):
    '''
    Stores HUD data
    '''
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
        '''
        Parses the GeoService URL to obtain the geojson download URL and uses
        the geojson to obtain data.
        '''
        def load_geojson(self):
            return json.loads(urllib.request.urlopen(
                'https://opendata.arcgis.com/datasets/%s_0.geojson%s' %
                (self._dataset_code, '?' + self._query)).read())

        geojson = load_geojson(self)

        return utils.geojson_data(geojson)

    def __get_metadata(self):
        '''
        Maps provided esriFieldTypes to sqlalchemy types.
        '''
        ui.item("Gathering metadata")
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
        utils.insert_data(
            self.data, self.session, circle_bar, self.binding, srid=self.srid)
        return
