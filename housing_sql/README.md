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

Suppose we would like to build a database for a housing app in the city of Chicago. There are a number of datasets available via open data portals such as [Chicago's open data portal](https://data.cityofchicago.org/), [Cook County's open data portal](https://datacatalog.cookcountyil.gov/), and [HUD's open data portal](https://hudgis-hud.opendata.arcgis.com/).

The Chicago open data portal provides us with geospatial files of [building footprints](https://data.cityofchicago.org/Buildings/Building-Footprints-current-/hz9b-7nh8) and [neighborhood boundaries](https://data.cityofchicago.org/Facilities-Geographic-Boundaries/Boundaries-Neighborhoods/bbvz-uum9), along with Socrata APIs for building [permits](https://data.cityofchicago.org/Buildings/Building-Permits/ydr8-5enu/data) and [violations](https://data.cityofchicago.org/Buildings/Building-Violations/22u3-xenr/data), a [building code scofflaw list](https://data.cityofchicago.org/Buildings/Building-Code-Scofflaw-List-Map/hgat-td99), and a [problem landlord list](https://data.cityofchicago.org/Buildings/Problem-Landlord-List-Map/dip3-ud6z). We may also be interested in gathering geospatial files on [parcel maps](https://datacatalog.cookcountyil.gov/GIS-Maps/Historical-ccgisdata-Parcels-2016/a33b-b59u), [street midlines](https://datacatalog.cookcountyil.gov/GIS-Maps/Historical-ccgisdata-Street-Midlines-2015/73aw-3v3w), and [address points](https://datacatalog.cookcountyil.gov/GIS-Maps/Historical-ccgisdata-Address-Points-for-Area-13-20/6y64-fiuv) provided by Cook County. If our app aims to provide information on federally funded housing, we may wish to incorporate [Low-Income Housing Tax Credit (LIHTC) properties](http://hudgis-hud.opendata.arcgis.com/datasets/low-income-housing-tax-credit-properties), [HUD assisted](http://hudgis-hud.opendata.arcgis.com/datasets/multifamily-properties-assisted) and [HUD insured](http://hudgis-hud.opendata.arcgis.com/datasets/hud-insured-multifamily-properties/data) multifamily properties, and [public housing developments](http://hudgis-hud.opendata.arcgis.com/datasets/public-housing-developments). Suppose we are also interested in HUD's [physical inspection score data](https://www.hud.gov/program_offices/housing/mfh/rems/remsinspecscores/remsphysinspscores) as available via an Excel file download. We have then filtered the dataset for inspections in Chicago, IL and saved the file locally.

We can load all of the above datasets at once by utilizing the command:
    
    python housing_sql.py bulk_load

In order to do so, we must fill out the file [bulk_load.py](https://github.com/sunlightpolicy/Housing_Data/blob/master/housing_sql/bulk_load.py) All datasets listed above are filled out within the current example of bulk_load.py.

NOTE:
Key values in the HUD_TABLES dictionary must be GeoService URLs. This URL can be obtained in the 'APIs' dropdown located on the upper right hand corner of each dataset's page. To pre-filter the dataset, click on the 'Data' tab as shown below.

![Alt text](images/data_tab.png "Public Housing Buildings")

After applying filters to the dataset, the 'APIs' dropdown will include a 'Filtered Dataset' option. In the example below, I filtered the "Public Housing Developments" dataset to only include developments within Chicago, IL. I then copied the GeoService URL under 'Filtered Dataset' into bulk_load.py.

![Alt text](images/hud_example.png "Public Housing Buildings")