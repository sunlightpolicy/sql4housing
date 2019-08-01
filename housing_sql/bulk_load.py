'''
Use this file to store all necessary API keys, hyperlinks, and DB info.
'''

'''
DB_NAME is a database connection string for destination database as 
'diacdlect+driver://username:password@host:port/database'.
'''
DB_NAME = 'postgres:///chi_property_data'

'''
GEOJSONS is a dictionary in the format
{<file path or download url>: <optional table name>}
'''
GEOJSONS = {"https://datacatalog.cookcountyil.gov/api/geospatial/a33b-b59u?method=export&format=GeoJSON": "parcels",
			"https://datacatalog.cookcountyil.gov/api/geospatial/73aw-3v3w?method=export&format=GeoJSON": "street_midlines",
			"https://datacatalog.cookcountyil.gov/api/geospatial/6y64-fiuv?method=export&format=GeoJSON": "address_points_area_13",
			"https://data.cityofchicago.org/api/geospatial/hz9b-7nh8?method=export&format=GeoJSON": "building_footprints"}

'''
SHAPEFILES is a dictionary in the format
{<file path or download url>: <optional table name>}
'''
SHAPEFILES = {"https://data.cityofchicago.org/api/geospatial/bbvz-uum9?method=export&format=Shapefile": "neighborhood_boundaries"}


'''
CSVS is a dictionary in the format
{<file path or download url>: <optional table name>}
'''
CSVS = {}

'''
EXCELS is a dictionary in the format
{<file path or download URL>: <optional table name>}
'''
EXCELS = {"chicago_data/Chicago MF Inspection.xlsx": "reac_scores"}

'''
HUD_TABLES is a dictionary in the format
{<GeoService URL>: <optional tabe name>}
See instructions for obtaining <GeoService URL> in README.md.
'''
HUD_TABLES = {"https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/LIHTC/FeatureServer/0/query?outFields=*&where=PROJ_CTY%20like%20'%25chicago%25'%20AND%20PROJ_ST%20like%20'%25IL%25'": "lihtc_properties",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Multifamily_Properties_Assisted/FeatureServer/0/query?outFields=*&where=HUB_NAME_TEXT%20%3D%20'Chicago'": "multifamily_properties_assisted",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/HUD_Insured_Multifamily_Properties/FeatureServer/0/query?outFields=*&where=HUB_NAME_TEXT%20%3D%20'Chicago'": "hud_insured_multifamily_properties",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Developments/FeatureServer/0/query?outFields=*&where=STD_CITY%20like%20'%25chicago%25'%20AND%20STD_ST%20like%20'%25IL%25'": "public_housing_developments"}

'''
SOCRATA_KEY is an optional Socrata app token. Including an app token
is recommended if you wish to upload large datasets. Instructions
for obtaining an app token are available at https://dev.socrata.com/docs/app-tokens.html.
'''
SOCRATA_KEY = None

'''
SOCRATA_TABLES is a dictionary in the format 
{'site': <open data portal url>, 'dataset_ids': {<dataset_id>: <optional table name>}}
'''
SOCRATA_TABLES = {'site': 'data.cityofchicago.org',
				  'dataset_ids':
				  {'hgat-td99': 'building_scofflaw_list',				  
				  'dip3-ud6z': 'problem_landlords',
				  'ydr8-5enu':'building_permits',
				  '22u3-xenr':'building_violations'}}

