'''
Use this file to store all necessary API keys, hyperlinks, and DB info.
'''

'''
DB_NAME is a database connection string for destination database as 
'diacdlect+driver://username:password@host:port/database'.
'''
DB_NAME = 'postgres:///chi_property_data'

# Optional Socrata app token
SOCRATA_KEY = None

'''
SOCRATA_TABLES is a dictionary in the format 
{'site': <open data portal url>, 'dataset_ids': {<dataset_id>: <optional table name>}}
'''
SOCRATA_TABLES = {'site': 'data.cityofchicago.com',
				  'dataset_ids':
				  {'hgat-td99': 'building_scofflaw_list',
				  'ydr8-5enu':'building_permits',
				  '22u3-xenr':'building_violations',
				  'dip3-ud6z': 'problem_landlords',
				  'hz9b-7nh8': 'building_footprints'}}

GEOJSON_URLS = {}

CSV_URLS = {}

'''
HUD_TABLES is a dictionary in the format
{<GeoService URL>: <optional tabe name>}
'''
HUD_TABLES = {"https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/LIHTC/FeatureServer/0/query?outFields=*&where=PROJ_CTY%20like%20'%25chicago%25'%20AND%20PROJ_ST%20like%20'%25IL%25'": "lihtc_properties",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Multifamily_Properties_Assisted/FeatureServer/0/query?outFields=*&where=HUB_NAME_TEXT%20%3D%20'Chicago'": "multifamily_properties_assisted",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/HUD_Insured_Multifamily_Properties/FeatureServer/0/query?outFields=*&where=HUB_NAME_TEXT%20%3D%20'Chicago'": "hud_insured_multifamily_properties",
			  "https://services.arcgis.com/VTyQ9soqVukalItT/arcgis/rest/services/Public_Housing_Developments/FeatureServer/0/query?outFields=*&where=STD_CITY%20like%20'%25chicago%25'%20AND%20STD_ST%20like%20'%25IL%25'": "public_housing_developments"}

ACS_TABLES = []
