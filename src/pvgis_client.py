import aiohttp
import consts

class PvgisClient:
    def __init__(self):
        self.api_url = consts.PVGIS_URL
        self.session = None
    
    async def send_request(self, index, lat, lon, tilt, azimuth, efficiency, loss):
        if (tilt <= 10):
            optimal_angles = True
        else:
            optimal_angles = False

        params = {
            "lat": float(lat),
            "lon": float(lon),
            "peakpower": float(efficiency),
            "loss": float(loss),
            "mountingplace": consts.MOUNTING_PLACE,
            "angle": float(tilt),
            "aspect": float(azimuth),
            "outputformat": consts.OUTPUT_FORMAT,
            "raddatabase": consts.RAD_DATABASE,
            "optimalangles": int(optimal_angles)
        }

        async with self.session.get(self.api_url, params=params) as response:
            data = await response.json()
            return index, data
    
    async def initialize(self):
        self.session = aiohttp.ClientSession()
        
    async def close(self):
        await self.session.close()
