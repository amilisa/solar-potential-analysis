class Cache:
    def __init__(self):
        self.cache = {}
    
    def get(self, tilt, azimuth):
        return self.cache.get((tilt, azimuth))
    
    def set(self, tilt, azimuth, value):
        self.cache[(tilt, azimuth)] = value
