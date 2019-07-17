This folder is based on a forked copy of Dallas Morning News' [socrata2sql](https://github.com/DallasMorningNews/socrata2sql). Socrata2sql is a tool which allows you to import any dataset on the Socrata API and copy it into a SQL database of your choice using a command line interface. Here, I aim to adapt socrata2sql to be able to import datasets from the following sources:

-[HUD's Open Data Portal](https://hudgis-hud.opendata.arcgis.com/)<br>
-The Census Bureau's [American Community Survey APIs](https://www.census.gov/data/developers/data-sets.html)<br>
-Any locally saved .csv file<br>
-Any locally saved .shp file

## Requirements

- Python 3.x