import json
import pandas as pd
from consts import *
from shapely.geometry import Point, Polygon
import seaborn as sns
import matplotlib.pyplot as plt
import math
import numpy as np
import requests
import asyncio
import aiohttp
import logging

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

def plot_heatmap(dataframe: pd.DataFrame, columns: list, figsize: tuple) -> None:
    corr_matrix = dataframe[columns].corr()
    sns.set(rc={'figure.figsize': figsize})
    sns.heatmap(
        corr_matrix, 
        xticklabels=corr_matrix.columns, 
        yticklabels=corr_matrix.columns, 
        annot=True,
        cmap=sns.diverging_palette(220, 20, as_cmap=True)
    )
    plt.show()

def calculate_pv_area(roof_area: float, roof_area_pv_ratio: float) -> float:
    return roof_area * roof_area_pv_ratio

def calculate_annual_kwh_pv_m2(annual_kwh: float, pv_area: float) -> float:
    return annual_kwh / pv_area

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

def create_polygon(row):
    points = row[POINTS]
    return Polygon([(point[1], point[0]) for point in points])

def plot_roofs(groups, color_column_name, orientation_column_name, figsize=(4,4)):
    for id, group in groups:
        fig, axes = plt.subplots()
        fig.set_size_inches(figsize)
        group.plot(ax=axes, color=group[color_column_name], alpha=0.5, legend=True)
        axes.set_title(f"{group[ADDRESS].iloc[0]}")
        axes.ticklabel_format(useOffset=False, style='plain')
        axes.set_xlabel("Y, m")
        axes.set_ylabel("X, m")
        axes.tick_params(axis='x', labelrotation=45)

        handles = []
        labels = []
        for item in group.iterrows():
            name = item[1][orientation_column_name]
            color = item[1][color_column_name]
            if (name not in labels):
                handles.append(plt.Rectangle((0, 0), 1, 1, fc=color, alpha=0.5))
                labels.append(name)
        
        fig.legend(handles, labels, title='Orientation', frameon=True)

        plt.show()

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
        
# def filter_roofs_by_coordnates(group):
#     if len(group) == 1:
#         return group
#     else:
#         try:
#             sorted_group = group.sort_values(ROOF_AREA, ascending=False)
#             index_to_compare = sorted_group.index[0]
#             polygon_to_compare = sorted_group[POLYGON].iloc[0]
#             for index, row in sorted_group.iterrows():
#                 if (index != index_to_compare):
#                     polygon = row[POLYGON]
#                     if (polygon_to_compare.intersects(polygon) or 
#                         polygon_to_compare.contains(polygon) or 
#                         polygon_to_compare.touches(polygon)):
#                         continue
#                     else:
#                         group = group.drop(index)
#             return group
#         except:
#             print(f"{group[ETAK_ID].iloc[0]}")
    
def get_production_estimation(lat, lon, peak_power, loss, angle, aspect, optimize_all=False):
    mounting_place = "building"
    output_format = "json"
    db = "PVGIS-SARAH2"
    if optimize_all:
        optimal_angles = True
    else:
        if (angle <= 10):
            optimal_angles = True
        else:
            optimal_angles = False

    payload = {
        "lat": float(lat),
        "lon": float(lon),
        "peakpower": float(peak_power),
        "loss": float(loss),
        "mountingplace": mounting_place,
        "angle": float(angle),
        "aspect": float(aspect),
        "outputformat": output_format,
        "raddatabase": db,
        "optimalangles": int(optimal_angles)
    }

    response = requests.get(PVGIS_URL, params=payload)
    return response.json()["outputs"]

def create_entry(roof, outputs, azimuth_column_name, orientation_column_name):
    entry = {
        ETAK_ID: roof[ETAK_ID],
        ROOF_ID: roof[ROOF_ID],
        AZIMUTH: roof[azimuth_column_name],
        ORIENTATION: roof[orientation_column_name],
        ANNUAL_KWH: outputs["totals"]["fixed"]["E_y"] or 0,
        MONTHLY_AVERAGE_KWH: outputs["totals"]["fixed"]["E_m"] or 0,
        "y-y_variation": outputs["totals"]["fixed"]["SD_y"]
    }
    
    for month, abbr in enumerate(MONTHS_ABBR_UNITS):
        monthly_power = outputs["monthly"]["fixed"][month]["E_m"] or 0
        entry[abbr] = monthly_power

    return entry

def plot_hist(data, title, xlabel, ylabel, figsize=(10, 5), bins=20):
    plt.figure(figsize=figsize)
    sns.histplot(data, bins=bins)
    plt.title(title, fontsize=14)
    plt.xlabel(xlabel, fontsize=12)
    plt.ylabel(ylabel, fontsize=12)
    plt.show()

async def fetch_data(session, url, id):
    async with session.get(url) as response:
        data = await response.json()
        return id, data

async def find_metadata(buildings):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for id, building in buildings.iterrows():
            url_with_params = f"{BUILDINGS_METADATA_URL}?ehr_code={building['ehr_code']}"
            task = fetch_data(session, url_with_params, building["address_id"])
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results
    
# async def process_requests(roofs, cache, api_client, lat, lon, efficiency, loss):
#     tasks = []
#     counter = 0
#     for index, roof in roofs.iterrows():
#         tilt = roof.tilt
#         azimuth = roof.azimuth
        
#         result = cache.get(tilt, azimuth)
#         if result is not None:
#             continue
#         task = asyncio.ensure_future(api_client.send_request(index, lat, lon, tilt, azimuth, efficiency, loss))
#         tasks.append(task)

#         if (len(tasks) == BATCH_SIZE):
#             results = await asyncio.gather(*tasks)
#             for index, result in results:
#                 cache.set(roofs.loc[index, TILT], roofs.loc[index, AZIMUTH], result)
            
#             tasks = []
#             asyncio.sleep(TIMEOUT)
#             counter += 1
#             logging.info(f"Processed {counter} batches.")

#     if tasks:
#         results = await asyncio.gather(*tasks)
#         for index, result in results:
#             cache.set(roofs.loc[index, TILT], roofs.loc[index, AZIMUTH], result)

# def parse_cache(cache):
#     parsed_cache = {}
#     for key, value in cache.items():
#         outputs = value["outputs"]
#         entry = {
#             ANNUAL_KWH: outputs["totals"]["fixed"]["E_y"] or 0,
#             "y-y_variation": outputs["totals"]["fixed"]["SD_y"],
#             MONTHLY_AVERAGE_KWH: outputs["totals"]["fixed"]["E_m"] or 0,
#             "total_loss": outputs["totals"]["fixed"]["l_total"] or 0

#         }

#         for month, abbr in enumerate(MONTHS_ABBR_UNITS):
#             monthly_power = outputs["monthly"]["fixed"][month]["E_m"] or 0
#             entry[abbr] = monthly_power
        
#         parsed_cache[key] = entry

#     return parsed_cache