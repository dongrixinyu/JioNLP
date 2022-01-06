# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、检测一个字符串是否为人名
    2、原理：根据百家姓，输入一个字符串，如 ”章家瑞“、”办公室“，依据规则简要判断其是否为一个中国人名

"""

import re

from jionlp.rule.rule_pattern import CHINESE_FAMILY_NAME, TWO_CHAR_CHINESE_FAMILY_NAME


class CheckPersonName(object):
    """ 给定一个字符串，判断其是否为一个中国人名
    原理目前仍非常简陋，即判断该字符串的长度，以及该串首字符是否为姓氏

    """

    def __init__(self):
        self.chinese_family_name = re.compile(CHINESE_FAMILY_NAME)
        self.two_char_chinese_family_name = re.compile(
            '(' + TWO_CHAR_CHINESE_FAMILY_NAME + ')')

    def __call__(self, text):
        text_length = len(text)
        if text_length <= 1:  # 非人名
            return False

        if text_length >= 5:  # 非人名
            return False

        if text_length == 4:
            # 4 字人名，其中包括两种情况：
            # 1、姓氏为二字，如 “欧阳”
            if self.chinese_family_name.search(text[0]) is not None \
                    and self.chinese_family_name.search(text[1]) is not None:
                return True

            # 2、首二字为单字姓氏，如父母姓氏的组合：“刘王晨曦”
            if self.two_char_chinese_family_name.search(text[:2]) is not None:
                return True

            return False

        if text_length == 3:
            # 3 字人名
            # 1、首字为姓氏，如 “张”
            if self.chinese_family_name.search(text[0]) is not None:
                return True

            # 2、姓氏为二字，如 “上官”
            if self.two_char_chinese_family_name.search(text[:2]) is not None:
                return True

            return False

        if text_length == 2:
            if self.chinese_family_name.search(text[0]) is not None:
                return True

            return False
