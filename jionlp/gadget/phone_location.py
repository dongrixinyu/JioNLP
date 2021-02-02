# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
DESCRIPTION:
    1、手机号搜索地名，仅取前三位作为基准，如 1702 电信虚拟 1703 移动虚拟 1704 联通虚拟 不予考虑
    2、运营商信息不全，如 190 号段未加入
    3、携号转网，会造成具体的某个电话号码误判

"""


import re

from jionlp.rule.rule_pattern import CELL_PHONE_CHECK_PATTERN, \
    LANDLINE_PHONE_CHECK_PATTERN, LANDLINE_PHONE_AREA_CODE_PATTERN
from jionlp.dictionary.dictionary_loader import phone_location_loader, \
    telecom_operator_loader
from jionlp.gadget.trie_tree import TrieTree


class PhoneLocation(object):
    """ 对于给定的电话号码，返回其归属地、区号、运营商等信息。
    该方法与 jio.extract_phone_number 配合使用。

    Args:
        text(str): 电话号码文本。若输入为 jio.extract_phone_number 返回的结果，效果更佳。
            注意，仅输入电话号码文本，如 "86-17309729105"、"13499013052"、"021 60128421" 等，
            而 "81203432" 这样的电话号码则没有对应的归属地。
            若输入 "343981217799212723" 这样的文本，会造成误识别，须首先从中识别电话号码，再进行
            归属地、区号、运营商的识别

    Returns:
        dict: 该电话号码的类型，归属地，手机运营商

    Examples:
        >>> import jionlp as jio
        >>> text = '联系电话：13288568202. (021)32830431'
        >>> num_list = jio.extract_phone_number(text)
        >>> print(num_list)
        >>> res = [jio.phone_location(item['text']) for item in num_list]
        >>> print(res)

        # [{'text': '13288568202', 'offset': (5, 16), 'type': 'cell_phone'},
           {'text': '(021)32830431', 'offset': (18, 31), 'type': 'landline_phone'}]

        # {'number': '(021)32830431', 'province': '上海', 'city': '上海', 'type': 'landline_phone'}
        # {'number': '13288568202', 'province': '广东', 'city': '揭阳',
           'type': 'cell_phone', 'operator': '中国联通'}

    """
    def __init__(self):
        self.cell_phone_location_trie = None

    def _prepare(self):
        """ 加载词典 """
        cell_phone_location, zip_code_location, area_code_location = phone_location_loader()
        self.zip_code_location = zip_code_location
        self.area_code_location = area_code_location

        self.cell_phone_location_trie = TrieTree()
        for num, loc in cell_phone_location.items():
            self.cell_phone_location_trie.add_node(num, loc)

        self.cell_phone_pattern = re.compile(CELL_PHONE_CHECK_PATTERN)
        self.landline_phone_pattern = re.compile(LANDLINE_PHONE_CHECK_PATTERN)
        self.landline_area_code_pattern = re.compile(LANDLINE_PHONE_AREA_CODE_PATTERN)

        # 运营商词典
        telecom_operator = telecom_operator_loader()
        self.telecom_operator_trie = TrieTree()
        for num, loc in telecom_operator.items():
            self.telecom_operator_trie.add_node(num, loc)

    def __call__(self, text):
        """ 输入一段电话号码文本，返回其结果 """
        if self.cell_phone_location_trie is None:
            self._prepare()

        res = self.cell_phone_pattern.search(text)
        if res is not None:  # 匹配至手机号码
            cell_phone_number = res.group()
            first_seven = cell_phone_number[:7]
            _, location = self.cell_phone_location_trie.search(first_seven)
            province, city = location.split(' ')
            # print(province, city)

            _, operator = self.telecom_operator_trie.search(cell_phone_number[:4])

            return {'number': text, 'province': province, 'city': city,
                    'type': 'cell_phone', 'operator': operator}

        res = self.landline_phone_pattern.search(text)
        if res is not None:  # 匹配至固话号码
            # 抽取固话号码的区号
            res = self.landline_area_code_pattern.search(text)
            if res is not None:
                area_code = res.group(1)
                province, city = self.area_code_location.get(area_code, ' ').split(' ')
                if province == '':
                    province, city = None, None

                return {'number': text, 'province': province,
                        'city': city, 'type': 'landline_phone'}
            else:
                return {'number': text, 'province': None,
                        'city': None, 'type': 'landline_phone'}

        return {'number': text, 'province': None,
                'city': None, 'type': 'unknown'}

    def landline_phone_location(self, phone_num):
        """ 检索固定电话号码城市区号并返回，即已知输入是固话号码 """
        if self.cell_phone_location_trie is None:
            self._prepare()

        # 抽取固话号码的区号
        res = self.landline_area_code_pattern.search(phone_num)
        if res is not None:
            area_code = res.group(1)
            province, city = self.area_code_location.get(area_code, ' ').split(' ')
            if province == '':
                province, city = None, None

            return {'number': phone_num, 'province': province,
                    'city': city, 'type': 'landline_phone'}
        else:
            return {'number': phone_num, 'province': None,
                    'city': None, 'type': 'landline_phone'}

    def cell_phone_location(self, phone_num):
        """ 检索手机号码城市区号并返回，即已知输入是手机号 """
        if self.cell_phone_location_trie is None:
            self._prepare()

        res = self.cell_phone_pattern.search(phone_num)
        cell_phone_number = res.group()
        first_seven = cell_phone_number[:7]
        _, location = self.cell_phone_location_trie.search(first_seven)
        province, city = location.split(' ')

        _, operator = self.telecom_operator_trie.search(cell_phone_number[:4])

        return {'number': phone_num, 'province': province, 'city': city,
                'type': 'cell_phone', 'operator': operator}

