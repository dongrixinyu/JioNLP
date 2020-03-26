# -*- coding=utf-8 -*-


import os

from jionlp.dictionary.dictionary_loader import china_location_loader


class IDCardParser(object):
    ''' 身份证号码解析器 '''
    def __init__(self):
        self.china_locations = None
        
    def _prepare(self):
        china_loc = china_location_loader()
        china_locations = dict()
        for prov in china_loc:
            if not prov.startswith('_'):
                for city in china_loc[prov]:
                    if not city.startswith('_'):
                        for county in china_loc[prov][city]:
                            if not county.startswith('_'):
                                china_locations.update(
                                    {china_loc[prov][city][county]['_admin_code']: 
                                     [prov, city, county]})
        self.china_locations = china_locations
        
    def __call__(self, id_card):
        if self.china_locations is None:
            self._prepare()

        prov, city, county = self.china_locations[id_card[:6]]
        gender = '男' if int(id_card[-2]) % 2 else '女'
        return {'province': prov, 'city': city, 
                'county': county, 
                'birth_year': id_card[6:10],
                'birth_month': id_card[10:12],
                'birth_day': id_card[12:14],
                'gender': gender,
                'check_code': id_card[-1]}





