import pandas as pd
from consts import *
import numpy as np
import asyncio
import logging
from pvgis_client import PvgisClient
from cache import Cache
import parser_wrapper
from timeit import default_timer as timer


logging.basicConfig(filename = WD.joinpath("app.log"), level=logging.INFO, force=True)


async def process_requests(roofs, cache, api_client, lat, lon, efficiency, loss):
    tasks = []
    batch_counter = 0
    requests_counter = 0
    start = timer()
    try:
        for index, roof in roofs.iterrows():
            tilt = roof[TILT]
            azimuth = roof[AZIMUTH]
            
            result = cache.get(tilt, azimuth)
            if result is not None:
                continue
            
            task = asyncio.create_task(api_client.send_request(index, lat, lon, tilt, azimuth, efficiency, loss))
            tasks.append(task)
            requests_counter += 1

            if len(tasks) == BATCH_SIZE:
                await process_results(tasks, roofs, cache)
                tasks = []
                batch_counter += 1
                logging.info(f"Processed {batch_counter} batches.")
                await asyncio.sleep(TIMEOUT)

        if tasks:
            await process_results(tasks, roofs, cache)
        
        end = timer()
        logging.info(f"Time taken for processing requests: {(end - start) / 60:.2f}min.")
        logging.info(f"Processed {requests_counter} requests.")
    except Exception as e:
        print(f"There was the following exception during the batch {batch_counter}:")
        print(e)


async def process_results(tasks, roofs, cache):
    results = await asyncio.gather(*tasks)
    for index, result in results:
        cache.set(roofs.loc[index, TILT], roofs.loc[index, AZIMUTH], result)


def parse_cache(cache):
    parsed_cache = {}
    for key, value in cache.items():
        outputs = value["outputs"]
        entry = {
            ANNUAL_KWH_PV_M2: outputs["totals"]["fixed"]["E_y"] or 0,
            YY_VARIATION_PV_M2: outputs["totals"]["fixed"]["SD_y"],
            MONTHLY_AVERAGE_KWH_PV_M2: outputs["totals"]["fixed"]["E_m"] or 0,
            TOTAL_LOSS: outputs["totals"]["fixed"]["l_total"] or 0
        }

        for month, abbr in enumerate(MONTHS_ABBR_UNITS_PV_M2):
            monthly_power = outputs["monthly"]["fixed"][month]["E_m"] or 0
            entry[abbr] = monthly_power
        
        parsed_cache[key] = entry

    return parsed_cache


async def main(roofs_data_filename, lat, lon, efficiency, loss):
    api_client = PvgisClient()
    cache = Cache()

    roofs_data = pd.read_csv(roofs_data_filename)

    await api_client.initialize()

    async with api_client.session:
        await process_requests(roofs_data, cache, api_client, lat, lon, efficiency, loss)

    await api_client.close()

    parsed_cache = parse_cache(cache.cache)

    for group_name, group_df in roofs_data.groupby([TILT, AZIMUTH]):
        tilt, azimuth = group_name
        values = parsed_cache.get((tilt, azimuth), {})

        if len(values) == 0:
            for column_name, value in values.items():
                roofs_data.loc[group_df.index, column_name] = np.nan
        else:
            for column_name, value in values.items():
                roofs_data.loc[group_df.index, column_name] = value
    
    roofs_data.to_csv(ROOFS_DIR.joinpath("estimated_production.csv"), index=False)


if __name__ == "__main__":
    parser = parser_wrapper.ArgumentParserWrapper()
    parser.configure_parser()
    args = parser.parse()
    asyncio.run(main(args.filename, args.lat, args.lon, args.pv_efficiency, args.pv_loss))
