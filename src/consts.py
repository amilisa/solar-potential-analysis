import calendar
from pathlib import Path


WD = Path(__file__).parent.parent
DATA_DIR = WD.joinpath("data")

# Buildings data paths
BUILDINGS_DIR = DATA_DIR.joinpath("buildings")
BUILDINGS_PATH = BUILDINGS_DIR.joinpath("buildings.csv")
MONTHLY_REAL_PROD = BUILDINGS_DIR.joinpath("monthly_production_by_building.csv")
ANNUAL_REAL_PROD = BUILDINGS_DIR.joinpath("annual_production_by_building.csv")
BUILDINGS_MAPPED_PATH = BUILDINGS_DIR.joinpath("est_prod_buildings_mapped.csv")

# Roofs data paths
ROOFS_DIR = DATA_DIR.joinpath("roofs")
ROOFS_PATH = ROOFS_DIR.joinpath("roofs.csv")
NEW_ROOFS_PROD_PATH = ROOFS_DIR.joinpath("new_roofs_prod.csv")
RECALCULATED_ROOFS_PATH = ROOFS_DIR.joinpath("recalculated_roofs.csv")
ROOFS_FILTERED_PATH = ROOFS_DIR.joinpath("roofs_filtered.csv")

# Common
DISTRICTS_PATH = DATA_DIR.joinpath("districts.json")
DEVICES_MAPPED_PATH = DATA_DIR.joinpath("devices_mapped.csv")

# URLs
DISTRICTS_URL = "https://gis.tartulv.ee/arcgis/rest/services/Planeeringud/GI_linnaosad/MapServer/0/query"
PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_2/PVcalc"
BUILDINGS_METADATA_URL = 'https://devkluster.ehr.ee/api/building/v2/buildingData'

# Column names
FILENAME = "filename"
SOURCE = "source"
KWH = "kwh"
M2 = "m2"
PV_M2 = "/pv_" + M2
ETAK_ID = "etak_id"
VALUE_KWH = "value_kwh"
TOTAL_ROOF_AREA = "total_roof_area"
PV_AREA_M2 = "pv_area_" + M2
LAT = "lat"
LON = "lon"
ROOF_ID = "roof_id"
ANNUAL_KWH = "annual_" + KWH
MONTHLY_KWH = "monthly_" + KWH
MONTHLY_AVERAGE_KWH = "monthly_average_" + KWH
ROOF_AREA = "roof_area"
AZIMUTH = "azimuth"
TILT = "tilt"
ORIENTATION = "orientation"
DISTRICT = "district"
YY_VARIATION_PV_M2 = "y-y_variation" + PV_M2
TOTAL_LOSS = "total_loss"
ANNUAL_KWH_PV_M2 = ANNUAL_KWH + PV_M2
MONTHLY_AVERAGE_KWH_PV_M2 = MONTHLY_AVERAGE_KWH + PV_M2
MONTHS_ABBR = list(calendar.month_abbr)[1:]
MONTHS_ABBR_UNITS = [MONTHS_ABBR[i] + "_" + KWH for i in range(12)]
MONTHS_ABBR_UNITS_PV_M2 = [item + PV_M2 for item in MONTHS_ABBR_UNITS]
OBJECT_TYPE = "object_type"
OBJECT_CODE = "object_code"
OBJECT_ADDRESS = "object_address"
ADDRESS = "address"
ADDRESS_ID = "address_id"
EHR_CODE = "ehr_code"
SOURCE = "source"
YEAR = "year"
MONTH = "month"
NAME = "NIMI"
GEOMETRY = "geometry"
POINTS = "points"
POLYGON = "polygon"

# Orientations
NORTH = "north"
SOUTH = "south"
EAST = "east"
WEST = "west"
NONE = "none"

# Auxiliary
ROOF_AREA_PV_RATIO = 0.9
SUFFIX_NEW = "_new"
SUFFIX_REAL = "_real"
SUFFIX_ESTIMATED = "_estimated"
ORIENTATION_NEW = ORIENTATION + SUFFIX_NEW
AZIMUTH_NEW = AZIMUTH + SUFFIX_NEW
ANNUAL_KWH_NEW = ANNUAL_KWH + SUFFIX_NEW
COLOR = "color"
COLOR_NEW = COLOR + SUFFIX_NEW

# API consts
MOUNTING_PLACE = "building"
OUTPUT_FORMAT = "json"
RAD_DATABASE = "PVGIS-SARAH2"
BATCH_SIZE = 30
TIMEOUT = 1
TARTU_LAT = 58.378025
TARTU_LON = 26.728493
EFFICIENCY = 0.18
LOSS = 14