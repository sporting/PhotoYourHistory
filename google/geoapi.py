# -*- coding: UTF-8 -*-
import googlemaps
from functools import reduce

class GeoHelper():
    def __init__(self,key):
        self.gmaps = googlemaps.Client(key=key)

    def getNearAddress(self,gps):
        try:
            data = self.gmaps.reverse_geocode(gps,result_type=['street_address'])
            if len(data)>0:
                d = reduce(lambda x, y: x if len(x['formatted_address'])>len(y['formatted_address']) else y, data)
                return d['formatted_address']
        except Exception as e:
            print(e)

    