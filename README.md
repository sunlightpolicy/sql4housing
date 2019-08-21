# sql4housing

## Background

Sql4housing is based on a broader effort to encourage collaboration between civic hackers and housing advocates. Read more about this work on our blog here:

[Hacking for Housing: How open data and civic hacking creates wins for housing advocates](https://sunlightfoundation.com/2019/07/22/hacking-for-housing-how-open-data-and-civic-hacking-creates-wins-for-housing-advocates/) <br>

[Ownership, evictions, and violations: an overview of housing data use cases
](https://sunlightfoundation.com/2019/08/20/ownership-evictions-and-violations-an-overview-of-housing-data-use-cases/)


## Introduction

Sql4housing is based on a cloned copy of Dallas Morning News' [socrata2sql](https://github.com/DallasMorningNews/socrata2sql). Socrata2sql is a tool which allows you to import any dataset on the Socrata API and copy it into a SQL database of your choice using a command line interface. Here, I aim to adapt socrata2sql to be able to import datasets from the following sources:

-[HUD's Open Data Portal](https://hudgis-hud.opendata.arcgis.com/)<br>
-Any locally saved Excel file or Excel download hyperlink<br>
-Any locally saved .csv file or .csv download hyperlink<br>
-Any locally saved .shp file or .zip download hyperlink containing a .shp file<br>
-Any locally saved .geojson file or .geojson download hyperlink<br>
-Any dataset on a Socrata open data portal<br>
-Census variables within the 5-year American Community Survey or Decennial Census

## Requirements

- Python 3.x<br>
- Any database supported by SQLAlchemy<br>
- Download package via: `pip install sql4housing`

## Usage

Changes in usage will be periodically updated and documented within the docstring of [cli.py](https://github.com/sunlightpolicy/sql4housing/blob/master/sql4housing/cli.py)

See [/chicago_examples](https://github.com/sunlightpolicy/sql4housing/tree/master/chicago_example) for a detailed use case.

    """Housing data to SQL database loader

    Load a dataset directly from an API (Socrata, HUD) or file (csv or shp)
    into a SQL database. The loader supports any database supported by SQLalchemy.
    This file is adapted from a forked copy of DallasMorningNews/socrata2sql

    Usage:
      sql4housing bulk_load
      sql4housing hud <site> [--d=<database_url>] [--t=<table_name>]
      sql4housing socrata <site> <dataset_id> [--a=<app_token>] [--d=<database_url>] [--t=<table_name>]
      sql4housing csv <location> [--d=<database_url>] [--t=<table_name>]
      sql4housing excel <location> [--d=<database_url>] [--t=<table_name>]
      sql4housing shp <location> [--d=<database_url>] [--t=<table_name>]
      sql4housing geojson <location> [--d=<database_url>] [--t=<table_name>]
      sql4housing census (decennial2010 | (acs [--y=<year>])) <variables> (--m=<msa> | --c=<csa> | --n=<county> | --s=<state> | --p=<place>) [--l=<level>] [--d=<database_url>] [--t=<table_name>]
      sql4housing (-h | --help)
      sql4housing (-v | --version)

    Options:
      <bulk_load>        Loads all datasets documented within a file entitled bulk_load.yaml.
                         Must be run in the same folder where bulk_load.yaml is saved.
      <site>             The domain for the open data site. For Socrata, this is the
                         URL to the open data portal (Ex: www.dallasopendata.com).
                         For HUD, this is the Query URL as created in the API
                         Explorer portion of each dataset's page on the site
                         https://hudgis-hud.opendata.arcgis.com. See example use cases
                         for detailed instructions.
      <dataset_id>       The ID of the dataset on Socrata's open data site. This is
                         usually a few characters, separated by a hyphen, at the end
                         of the URL. Ex: 64pp-jeba
      <location>         Either the path or download URL where the file can be accessed.
      --d=<database_url> Database connection string for destination database as
                         diacdlect+driver://username:password@host:port/database.
                         Default: "postgresql:///mydb"
      --t=<table_name>   Destination table in the database. Defaults to a sanitized
                         version of the dataset or file's name.
      --a=<app_token>    App token for the Socrata site. Only necessary for
                         high-volume requests. Default: None
      --y=<year>         Optional year specification for the 5-year American Community
                         survey. Defaults to 2017.
      --m=<msa>          The metropolitan statistical area to include. 
                         Ex: --m="new york-newark-jersey city"
      --c=<csa>          The combined statistical area to include.
                         Ex: --c="New York-Newark, NY-NJ-CT-PA"
      --n=<county>       The county to include.
                         Ex: --n="cook county, IL"
      --s=<state>        The state to include.
                         Ex: --s="illinois"
      --p=<place>        The census place to include.
                         Ex: --p="chicago, IL"
      --l=<level>        The geographic level at which to extract data. i.e. tract,
                         block, county, region, division. Reference cenpy documentation
                         to learn more: https://github.com/cenpy-devs/cenpy
      -h --help          Show this screen.
      -v --version       Show version.

    Examples:

      Load the Dallas check register into a local SQLite file (file name chosen
      from the dataset name):
      $ sql4housing socrata www.dallasopendata.com 64pp-jeba

      Load it into a PostgreSQL database called mydb:
      $ sql4housing socrata www.dallasopendata.com 64pp-jeba -d"postgresql:///mydb"

      Load Public Housing Buildings from HUD into a PostgreSQL database called mydb:
      $ sql4housing hud "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Buildings/FeatureServer/0/query?outFields=*&where=1%3D1" -d=postgresql:///mydb

      Load Public Housing Physical Inspection scores into a PostgreSQL database called housingdb:
      $ sql4housing excel "http://www.huduser.org/portal/datasets/pis/public_housing_physical_inspection_scores.xlsx" -d=postgresql:///housingdb
    """

