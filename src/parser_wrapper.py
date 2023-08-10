import argparse
import arguments
from consts import *

class ArgumentParserWrapper:
    def __init__(self):
        self.parser = argparse.ArgumentParser()

    def configure_parser(self):
        self.parser.add_argument("--filename", help="filename of the roofs data", type=str, required=True)
        self.parser.add_argument("--lat", help="location latitude, defaults to 58.378025 (Tartu)", type=float, default=TARTU_LAT)
        self.parser.add_argument("--lon", help="location longitude, defaults to 26.728493 (Tartu)", type=float, default=TARTU_LON)
        self.parser.add_argument("--pv-efficiency", help="efficiency of the PV system, defaults to 0.20", type=float, default=EFFICIENCY)
        self.parser.add_argument("--pv-loss", help="loss in cables, power inverters, dirt, etc., defaults to 14%", type=float, default=LOSS)

    def parse(self):
        args = self.parser.parse_args()
        return arguments.Arguments(args.filename, args.lat, args.lon, args.pv_efficiency, args.pv_loss)