import json
import pandas as pd
from consts import *
from shapely.geometry import Point, Polygon
import math
import numpy as np


def flatten_json(fina_path: str, months_abbr_units: list) -> pd.DataFrame:
    with open(fina_path, 'r') as file:
        data = json.loads(file.read())

    flattened_data = []
    for key in data.keys():
        etak_id = key
        building = data[key]
        total_roof_area = building[TOTAL_ROOF_AREA]
        lat = building[LAT]
        lon = building[LON]

        for roof in building["roofs"]:
            roof_id = roof["id"]
            annual_kwh = roof["yearly_kwh"]
            monthly_average_kwh = roof[MONTHLY_AVERAGE_KWH]
            roof_area = roof["area"]
            azimuth = roof[AZIMUTH]
            tilt = roof[TILT]
            orientation = roof[ORIENTATION]
            monthly_kwh = roof[MONTHLY_KWH]
            points = roof["points_epsg_3301"]
            
            entry = {
                ETAK_ID: etak_id,
                ROOF_ID: roof_id,
                ANNUAL_KWH: annual_kwh,
                MONTHLY_AVERAGE_KWH: monthly_average_kwh,
                ROOF_AREA: roof_area,
                AZIMUTH: azimuth,
                TILT: tilt,
                ORIENTATION: orientation,
                TOTAL_ROOF_AREA: total_roof_area,
                LAT: lat,
                LON: lon,
                "points": points
            }
            
            for i in range(12):
                entry[months_abbr_units[i]] = monthly_kwh[i]
            
            flattened_data.append(entry)
    return pd.DataFrame(flattened_data)


def map_coordinates_to_district(lat: float, lon: float, districts: dict) -> str:
    location = Point(lon, lat)
    for key in districts.keys():
        district = Polygon(districts[key][0])
        if location.within(district):
            return key
      
        
def get_closest_district(row, districts_gdf):
    point = row[GEOMETRY]
    closest_district = districts_gdf.to_crs(3301).distance(point).idxmin()
    return districts_gdf.loc[closest_district][NAME]


def calculate_pv_area(roof_area: float, roof_area_pv_ratio: float) -> float:
    return roof_area * roof_area_pv_ratio


def calculate_annual_kwh_pv_m2(annual_kwh: float, pv_area: float) -> float:
    return annual_kwh / pv_area


# https://github.com/boroma4/Mapping-Solar-Potential-of-Tartu/blob/main/pipeline/lib/util/geometry.py
def get_angles(normal):
    """Get the azimuth and altitude from the normal vector."""
    # -- Convert from polar system to azimuth
    azimuth = 90 - math.degrees(math.atan2(normal[1], normal[0]))
    if azimuth >= 360.0:
        azimuth -= 360.0
    elif azimuth < 0.0:
        azimuth += 360.0
    # Azimuth is [0, 360], 0 is North direction, East is 90, West is -90
    # Converting to [-180, 180], 0 is South direction to be compatible with PVGIS API, East must be -90, West 90
    azimuth -= 180

    #[0, 90]
    t = math.sqrt(normal[0]**2 + normal[1]**2)
    if t == 0:
        tilt = 0.0
    else:
        # 0 for flat roof, 90 for wall
        tilt = 90 - abs(math.degrees(math.atan(normal[2] / t)))
    tilt = round(tilt, 3)

    return azimuth, tilt


# https://github.com/boroma4/Mapping-Solar-Potential-of-Tartu/blob/main/pipeline/lib/util/geometry.py
def unit_normal(a, b, c):
    x = np.linalg.det([[1, a[0], a[2]],
                       [1, b[0], b[2]],
                       [1, c[0], c[2]]])
    y = np.linalg.det([[a[1], 1, a[2]],
                       [b[1], 1, b[2]],
                       [c[1], 1, c[2]]])
    z = np.linalg.det([[a[1], a[0], 1],
                       [b[1], b[0], 1],
                       [c[1], c[0], 1]])
    magnitude = (x**2 + y**2 + z**2)**.5
    return (x / magnitude, y / magnitude, z / magnitude)


# https://github.com/boroma4/Mapping-Solar-Potential-of-Tartu/blob/3e068d28455958ff3dde7ce96dfd27de066f0e6c/pipeline/lib/citygml/surface.py
def get_orientation(x, azimut_column_name=AZIMUTH_NEW):
        if x.tilt <= 10:
            return NONE
        if -45 <= x[azimut_column_name] <= 45:
            return SOUTH
        if -135 <= x[azimut_column_name] <= -45:
            return EAST
        if 45 <= x[azimut_column_name] <= 135:
            return WEST
        return NORTH
    
    
def filter_roofs_by_orientation(group, orientation_column, real_roofs_measures):
    etak_id = group[ETAK_ID].iloc[0]
    return group[group[orientation_column].isin(real_roofs_measures[real_roofs_measures[ETAK_ID] == etak_id][ORIENTATION].values)]


def filter_roofs_by_coordnates(group):
    if len(group) == 1 and (group[ROOF_AREA].iloc[0] > 4):
        return group
    else:
        sorted_group = group.sort_values(ROOF_AREA, ascending=False)
        index_to_compare = sorted_group.index[0]
        polygon_to_compare = sorted_group[POLYGON].iloc[0]
        if sorted_group[ROOF_AREA].iloc[0] > 4:
            for index, row in sorted_group.iterrows():
                if (index != index_to_compare):
                    polygon = row[POLYGON]
                    if (polygon_to_compare.intersects(polygon) or 
                        polygon_to_compare.contains(polygon) or 
                        polygon_to_compare.touches(polygon) or
                        row[ROOF_AREA] > 4):
                        continue
                    else:
                        group = group.drop(index)
            return group
        

def create_polygon(row):
    points = row[POINTS]
    return Polygon([(point[1], point[0]) for point in points])