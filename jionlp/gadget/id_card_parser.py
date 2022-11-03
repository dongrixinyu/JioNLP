# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re
from jionlp import logging

from jionlp.dictionary.dictionary_loader import china_location_loader
from jionlp.rule.rule_pattern import ID_CARD_CHECK_PATTERN


class IDCardParser(object):
    """ 身份证号码解析器，给定一个身份证号码，解析其对应的省、市、县、出生年月、性别、校验码。

    Args:
        None

    Returns:
        dict: 身份证号解析结果字段

    Examples:
        >>> import jionlp as jio
        >>> text = '52010320171109002X'
        >>> res = jio.parse_id_card(text)
        >>> print(res)

        # {'province': '贵州省',
        #  'city': '贵阳市',
        #  'county': '云岩区',
        #  'birth_year': '2017',
        #  'birth_month': '11',
        #  'birth_day': '09',
        #  'gender': '女',
        #  'check_code': 'x'}

    """
    def __init__(self):
        self.china_locations = None
        self.id_card_check_pattern = re.compile(ID_CARD_CHECK_PATTERN)
        
    def _prepare(self):
        china_loc = china_location_loader()
        china_locations = dict()
        for prov in china_loc:
            if not prov.startswith('_'):
                china_locations.update(
                    {china_loc[prov]['_admin_code']: 
                     [prov, None, None]})
                for city in china_loc[prov]:
                    if not city.startswith('_'):
                        china_locations.update(
                            {china_loc[prov][city]['_admin_code']: 
                             [prov, city, None]})
                        for county in china_loc[prov][city]:
                            if not county.startswith('_'):
                                china_locations.update(
                                    {china_loc[prov][city][county]['_admin_code']: 
                                     [prov, city, county]})
        self.china_locations = china_locations
        
    def __call__(self, id_card):
        if self.china_locations is None:
            self._prepare()
            
        # 检查是否是身份证号
        match_flag = self.id_card_check_pattern.match(id_card)

        if match_flag is None:
            logging.error('the id card is wrong.')
            return None

        if id_card[:6] in self.china_locations.keys():
            prov, city, county = self.china_locations[id_card[:6]]
        elif id_card[:4] + '0' * 2 in self.china_locations.keys():
            prov, city, county = self.china_locations[id_card[:4] + '0' * 2]
        elif id_card[:2] + '0' * 4 in self.china_locations.keys():
            prov, city, county = self.china_locations[id_card[:2] + '0' * 4]
        else:
            # 前六位行政区划全错
            logging.error('the administration code of id card is wrong.')
            return None

        gender = '男' if int(id_card[-2]) % 2 else '女'
        check_code = id_card[-1]
        if check_code == 'X':
            check_code = 'x'
        
        return {'province': prov, 'city': city, 
                'county': county, 
                'birth_year': id_card[6:10],
                'birth_month': id_card[10:12],
                'birth_day': id_card[12:14],
                'gender': gender,
                'check_code': check_code}

