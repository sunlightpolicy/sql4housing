This folder is based on a forked copy of Dallas Morning News' [socrata2sql](https://github.com/DallasMorningNews/socrata2sql). Socrata2sql is a tool which allows you to import any dataset on the Socrata API and copy it into a SQL database of your choice using a command line interface. Here, I aim to adapt socrata2sql to be able to import datasets from the following sources:

-[HUD's Open Data Portal](https://hudgis-hud.opendata.arcgis.com/)<br>
-Any locally saved .csv file or .csv hyperlink<br>
-Any locally saved .shp file or .zip hyperlink containing a .shp file<br>
-Any locally saved .geojson file of .geojson hyperlink

## Requirements

- Python 3.x

## Usage

Changes in usage will be periodically updated and documented within the docstring of [housing_sql.py](https://github.com/sunlightpolicy/Housing_Data/blob/master/housing_sql/housing_sql.py)

## Example Use Case: Chicago

Suppose we would like to build a database for a housing app in the city of Chicago using data from [Chicago's open data portal](https://data.cityofchicago.org/), [Cook County's open data portal](https://datacatalog.cookcountyil.gov/), and [HUD's open data portal](https://hudgis-hud.opendata.arcgis.com/). The Chicago open data portal provides us with geospatial files of [building footprints](https://data.cityofchicago.org/Buildings/Building-Footprints-current-/hz9b-7nh8) and [neighborhood boundaries](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Neighborhoods/bbvz-uum9), along with Socrata APIs for building [permits](https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu/data) and [violations](https://data.cityofchicago.org/Buildings/Building-Violations/22u3-xenr/data), a [building code scofflaw list](https://data.cityofchicago.org/Buildings/Building-Code-Scofflaw-List-Map/hgat-td99), [and a problem landlord list](https://data.cityofchicago.org/Buildings/Problem-Landlord-List-Map/dip3-ud6z).

![Alt text](images/hud_example.png "Public Housing Buildings")