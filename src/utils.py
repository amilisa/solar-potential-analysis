import requests
import asyncio
import aiohttp
from consts import *

    
def get_production_estimation(lat, lon, peak_power, loss, angle, aspect, optimize_all=False):
    if optimize_all:
        optimal_angles = True
    else:
        if (angle <= 10):
            optimal_angles = True
        else:
            optimal_angles = False

    payload = {
        LAT: float(lat),
        LON: float(lon),
        "peakpower": float(peak_power),
        "loss": float(loss),
        "mountingplace": MOUNTING_PLACE,
        "angle": float(angle),
        "aspect": float(aspect),
        "outputformat": OUTPUT_FORMAT,
        "raddatabase": RAD_DATABASE,
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

async def fetch_data(session, url, id):
    async with session.get(url) as response:
        data = await response.json()
        return id, data

async def find_metadata(buildings):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for id, building in buildings.iterrows():
            url_with_params = f"{BUILDINGS_METADATA_URL}?ehr_code={building['ehr_code']}"
            task = fetch_data(session, url_with_params, building[ADDRESS_ID])
            tasks.append(task)

        results = await asyncio.gather(*tasks)
        return results

def parse_filename(filename):
    return filename.split("_")

def get_year(filename, index):
    start_date = parse_filename(filename)[index]
    return int(start_date.split("-")[0])

def get_month(filename, index):
    start_date = parse_filename(filename)[index]
    return int(start_date.split("-")[1])