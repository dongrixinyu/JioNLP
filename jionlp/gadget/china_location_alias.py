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
from jionlp.rule.rule_pattern import MINORITIES_IN_CHINA_PATTERN, \
    CHINA_PROVINCE_SHORT_PATTERN


class GetChinaLocationAlias(object):
    def __init__(self):
        self.china_province_short_pattern = None
        self.china_minorities_pattern = None

    def get_china_province_alias(self, province_name):
        """ 给定一个省级名称，获取其简称，如，输入“山西省”，返回“山西”。

        Args:
            province_name: 省名，一般为全称

        Returns:
            str: 省级简称

        """
        if self.china_province_short_pattern is None:
            self.china_province_short_pattern = re.compile(CHINA_PROVINCE_SHORT_PATTERN)

        matched_res = self.china_province_short_pattern.search(province_name)
        if matched_res:
            province_alias = matched_res.group()
            return province_alias

        else:
            logging.warning('the given `{}` does NOT contain province name.'.format(province_name))
            return None

    def get_china_city_alias(self, city_name):
        """ 给定一个中国市级名称，获取其简称，如，输入“甘孜藏族自治州”，返回“甘孜”。

        Args:
            city_name: 市名，一般为全称

        Returns:
            str: 市级简称

        """
        if city_name.endswith('市'):
            return city_name.replace('市', '')

        if city_name.endswith('地区'):
            return city_name.replace('地区', '')

        if city_name.endswith('盟'):
            return city_name.replace('盟', '')

        if self.china_minorities_pattern is None:
            self.china_minorities_pattern = re.compile(MINORITIES_IN_CHINA_PATTERN)

        matched_res = self.china_minorities_pattern.search(city_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return city_name[:end_offset]

        return

    def get_china_county_alias(self, county_name):
        pass

