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
from jionlp.rule.rule_pattern import MINORITIES_IN_CHINA_PATTERN_1, \
    MINORITIES_IN_CHINA_PATTERN_2, CHINA_PROVINCE_SHORT_PATTERN


class GetChinaLocationAlias(object):
    def __init__(self):
        self.china_province_short_pattern = None
        self.china_minorities_pattern_1 = None
        self.china_minorities_pattern_2 = None
        self.china_county_qi = None

    def _prepare_qi_alias_map(self):
        self.china_county_qi = {
            '土默特右旗': '土右旗', '土默特左旗': '土左旗',
            '杭锦后旗': '杭后旗', '杭锦旗': '杭旗',
            '乌拉特后旗': '乌后旗', '乌拉特中旗': '乌中旗',
            '阿鲁科尔沁旗': '阿旗',
            '敖汉旗': '敖旗',
            '巴林右旗': '巴右旗', '巴林左旗': '巴左旗',
            '喀喇沁旗': '喀旗',
            '克什克腾旗': '克旗',
            '翁牛特旗': '翁旗',
            '达拉特旗': '达旗',
            '鄂托克旗': '鄂旗', '鄂托克前旗': '鄂前旗',
            '乌审旗': '乌旗',
            '伊金霍洛旗': '伊旗',
            '准格尔旗': '准旗',
            '阿荣旗': '阿荣旗',
            '陈巴尔虎旗': '陈旗',
            '鄂伦春自治旗': '鄂伦春', '鄂温克族自治旗': '鄂温克',
            '莫力达瓦达斡尔族自治旗': '莫旗',
            '新巴尔虎右旗': '新右旗', '新巴尔虎左旗': '新左旗',
            '科尔沁左翼后旗': '科左后旗', '科尔沁左翼中旗': '科左中旗', '科尔沁右翼前旗': '科右前旗', '科尔沁右翼中旗': '科右中旗',
            '库伦旗': '库旗', '奈曼旗': '奈旗', '扎鲁特旗': '扎旗', '扎赉特旗': '扎赉特旗',
            '察哈尔右翼后旗': '察右后旗', '察哈尔右翼前旗': '察右前旗', '察哈尔右翼中旗': '察右中旗',
            '四子王旗': '四子王旗', '阿巴嘎旗': '阿巴嘎旗',
            '东乌珠穆沁旗': '东乌旗', '西乌珠穆沁旗': '西乌旗',
            '苏尼特右旗': '苏右旗', '苏尼特左旗': '苏左旗', '太仆寺旗': '太仆寺旗',
            '镶黄旗': '镶黄旗', '正蓝旗': '正蓝旗', '正镶白旗': '正镶白旗',
            '阿拉善右旗': '阿右旗', '阿拉善左旗': '阿左旗', '额济纳旗': '额旗',
            '达尔罕茂明安联合旗': '达旗',
        }

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

    def get_china_city_alias(self, city_name, dismiss_diqu=False, dismiss_meng=False):
        """ 给定一个中国地级市级名称，获取其简称，如，输入 “甘孜藏族自治州”，返回 “甘孜” 。

        地级包括 市、地区、盟（内蒙）、民族自治州。

        Args:
            city_name: 市名，一般为全称
            dismiss_diqu: 忽略 `地区`，按原名返回
            dismiss_meng: 忽略 `盟`，按原名返回

        Returns:
            str: 市级简称

        """
        if city_name.endswith('市'):
            return city_name.replace('市', '')

        if not dismiss_diqu:
            if city_name.endswith('地区'):
                return city_name.replace('地区', '')

        if not dismiss_meng:
            if city_name.endswith('盟'):
                return city_name.replace('盟', '')

        # 带 `族` 字，自治州
        if self.china_minorities_pattern_1 is None:
            self.china_minorities_pattern_1 = re.compile(MINORITIES_IN_CHINA_PATTERN_1)

        matched_res = self.china_minorities_pattern_1.search(city_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return city_name[:end_offset]

        # 不带 `族` 字，自治州
        if self.china_minorities_pattern_2 is None:
            self.china_minorities_pattern_2 = re.compile(MINORITIES_IN_CHINA_PATTERN_2)

        matched_res = self.china_minorities_pattern_2.search(city_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return city_name[:end_offset]

        return

    def get_china_county_alias(self, county_name, dismiss_qi=False):
        """ 给定一个中国县级名称，获取其简称，如，输入 “仙桃市”，返回 “仙桃” 。

        县级包括 市、县、区、民族自治县、旗（内蒙）、林区。

        Args:
            county_name: 市名，一般为全称
            dismiss_qi: 处理时，忽略旗，直接按原名返回。

        Returns:
            str: 县级简称

        """
        if county_name.endswith('县'):
            if len(county_name) == 2:
                return county_name
            else:
                return county_name.replace('县', '')

        if county_name.endswith('林区'):
            return county_name.replace('林区', '')

        if county_name.endswith('区'):
            if len(county_name) == 2:
                return county_name
            else:
                return county_name.replace('区', '')

        if county_name.endswith('市'):
            return county_name.replace('市', '')

        # 处理内蒙 旗
        if not dismiss_qi:
            if county_name.endswith('旗'):
                if self.china_county_qi is None:
                    self._prepare_qi_alias_map()

                return self.china_county_qi.get(county_name, county_name)

        # 带 `族` 字，自治县
        if self.china_minorities_pattern_1 is None:
            self.china_minorities_pattern_1 = re.compile(MINORITIES_IN_CHINA_PATTERN_1)

        matched_res = self.china_minorities_pattern_1.search(county_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return county_name[:end_offset]

        # 不带 `族` 字，自治县
        if self.china_minorities_pattern_2 is None:
            self.china_minorities_pattern_2 = re.compile(MINORITIES_IN_CHINA_PATTERN_2)

        matched_res = self.china_minorities_pattern_2.search(county_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return county_name[:end_offset]

        return None

    def get_china_town_alias(self, town_name):
        """ 给定一个中国镇级名称，获取其简称，如，输入 “苏店镇”，返回 “苏店” 。

        镇级包括 镇、乡、街道、地区 等

        Args:
            town_name: 镇级名，一般为全称

        Returns:
            str: 镇级简称

        """
        if town_name.endswith('镇'):
            if len(town_name) == 2:
                return town_name
            else:
                return town_name.replace('镇', '')

        if town_name.endswith('乡'):
            if len(town_name) == 2:
                return town_name
            else:
                return town_name.replace('乡', '')

        if town_name.endswith('地区'):
            return town_name.replace('地区', '')

        if town_name.endswith('街道'):
            return town_name.replace('街道', '')

        # 带 `族` 字，自治县
        if self.china_minorities_pattern_1 is None:
            self.china_minorities_pattern_1 = re.compile(MINORITIES_IN_CHINA_PATTERN_1)

        matched_res = self.china_minorities_pattern_1.search(town_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return town_name[:end_offset]

        # 不带 `族` 字，自治县
        if self.china_minorities_pattern_2 is None:
            self.china_minorities_pattern_2 = re.compile(MINORITIES_IN_CHINA_PATTERN_2)

        matched_res = self.china_minorities_pattern_2.search(town_name)
        if matched_res:
            # '德宏傣族景颇族自治州' ，优先匹配第一个 傣族
            end_offset = matched_res.span()[0]
            return town_name[:end_offset]

        return None
