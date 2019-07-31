This folder is based on a forked copy of Dallas Morning News' [socrata2sql](https://github.com/DallasMorningNews/socrata2sql). Socrata2sql is a tool which allows you to import any dataset on the Socrata API and copy it into a SQL database of your choice using a command line interface. Here, I aim to adapt socrata2sql to be able to import datasets from the following sources:

-[HUD's Open Data Portal](https://hudgis-hud.opendata.arcgis.com/)<br>
-Any locally saved .csv file or .csv hyperlink<br>
-Any locally saved .shp file or .zip hyperlink containing a .shp file<br>
-Any locally saved .geojson file of .geojson hyperlink

## Requirements

- Python 3.x

## Usage

Changes in usage will be periodically updated and documented within the docstring of [housing_sql.py](https://github.com/sunlightpolicy/Housing_Data/blob/master/housing_sql/housing_sql.py)

	"""Housing data to SQL database loader

	Load a dataset directly from an API (Socrata, HUD, Census) or file (csv or shp) 
	into a SQL database. The loader supports any database supported by SQLalchemy.
	This file is adapted from a forked copy of DallasMorningNews/socrata2sql

	Usage:
	  housing_sql.py bulk_load
	  housing_sql.py hud <site> [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py socrata <site> <dataset_id> [-a=<app_token>] [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py csv (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py excel (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py shp (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py geojson (-p=<path> | -u=<url>) [-d=<database_url>] [-t=<table_name>]
	  housing_sql.py (-h | --help)
	  housing_sql.py (-v | --version)

	Options:
	  <bulk_load>        Loads all datasets documented within the file bulk_load.py.
	  <site>             The domain for the open data site. For Socrata, this is the
	                     URL to the open data portal (Ex: www.dallasopendata.com).
	                     For HUD, this is the Query URL as created in the API
	                     Explorer portion of each dataset's page on the site
	                     https://hudgis-hud.opendata.arcgis.com.
	  <dataset_id>       The ID of the dataset on Socrata's open data site. This is 
	                     usually a few characters, separated by a hyphen, at the end 
	                     of the URL. Ex: 64pp-jeba
	  -p=<path>          Path to the location where the file is stored.
	  -u=<url>           URL hyperlink where file can be downloaded.
	  -d=<database_url>  Database connection string for destination database as
	                     diacdlect+driver://username:password@host:port/database.
	                     Default: sqlite:///<source name>.sqlite
	  -t=<table_name>    Destination table in the database. Defaults to a sanitized
	                     version of the dataset or file's name.
	  -a=<app_token>     App token for the Socrata site. Only necessary for
	                     high-volume requests. Default: None
	  -h --help          Show this screen.
	  -v --version       Show version.

	Examples:

	  Load the Dallas check register into a local SQLite file (file name chosen
	  from the dataset name):
	  $ housing_sql.py socrata www.dallasopendata.com 64pp-jeba

	  Load it into a PostgreSQL database called mydb:
	  $ housing_sql.py socrata www.dallasopendata.com 64pp-jeba -d"postgresql:///mydb"

	  Load Public Housing Buildings from HUD into a PostgreSQL database called mydb:
	  $ housing_sql.py hud "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Buildings/FeatureServer/0/query?outFields=*&where=1%3D1" -d=postgresql:///mydb

	  Load Public Housing Physical Inspection scores into a PostgreSQL database called mydb:
	  $ housing_sql.py excel "http://www.huduser.org/portal/datasets/pis/public_housing_physical_inspection_scores.xlsx" -d=postgresql:///mydb
	"""

## Example Use Case: Chicago

![Alt text](hud_example.png "Public Housing Buildings")