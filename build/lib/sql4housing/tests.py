import pytest
import os.path
import housing_sql as hs
import source_classes as sc
from sqlalchemy.engine.base import Engine
from sqlalchemy.orm.session import Session
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.engine.default import DefaultDialect 
from sqlalchemy.sql.sqltypes import Text, BigInteger, DateTime, Numeric
import pandas as pd
import yaml
from yaml import CLoader as Loader
import utils


def test_yaml():
	output = yaml.load(open('bulk_load.yaml'), Loader=Loader) 
	assert list(output.keys()) == ['DATABASE', 'GEOJSONS', 'SHAPEFILES', \
		'CSVS', 'EXCELS', 'HUD_TABLES', 'SOCRATA', 'CENSUS']

def test_get_connection():
	e = sc.Excel("chicago_data/Chicago MF Inspection.xlsx")
	hs.get_connection(e)
	assert isinstance(e.session, Session)
	assert isinstance(e.engine, Engine)

def test_get_binding():
	e = sc.Excel("chicago_data/Chicago MF Inspection.xlsx")
	hs.get_connection(e)
	hs.get_binding(e)
	assert isinstance(e.binding, DeclarativeMeta)

def test_spreadsheet_metadata():
	e = sc.Excel("chicago_data/Chicago MF Inspection.xlsx")
	assert utils.spreadshseet_metadata(e) == [('unnamed:_0', BigInteger),
 ('property_name', Text),
 ('state_name_text', Text),
 ('city', Text),
 ('state_code', Text),
 ('rems_property_id', BigInteger),
 ('inspection_id_1', BigInteger),
 ('inspection_score1', Text),
 ('release_date_1', DateTime),
 ('inspection_id_2', Numeric),
 ('inspection_score2', Text),
 ('release_date_2', DateTime),
 ('inspection_id_3', Numeric),
 ('inspection_score3', Text),
 ('release_date_3', DateTime)]
 
def test_edit_columns():
	df = pd.DataFrame.from_dict(
		{"Fake Column": [2, 3, 4], "Another fake column 123": [5, 6, 7]}) 
	df = utils.edit_columns(df)
	assert all(df.columns == ['fake_column', 'another_fake_column_123'])


