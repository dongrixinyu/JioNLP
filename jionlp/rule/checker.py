# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import os
import re

from .rule_pattern import CHINESE_CHAR_PATTERN


class Checker(object):
    """ 特定类型正则检查器 """
    def __init__(self):

        self.chinese_any_char_pattern = None
        self.chinese_all_char_pattern = None
        self.any_arabic_num_pattern = None
        self.all_arabic_num_pattern = None

    def check_any_chinese_char(self, text):
        """ 检查文本中是否包含中文字符，若至少包含一个，则返回 True，否则返回 False。
        若为空字符串，返回 False。

        Args:
            text(str): 输入的文本
        Return:
            bool: 文本中是否包含中文字符

        Examples:
            >>> import jionlp as jio
            >>> print(jio.check_any_chinese_char('【新华社消息】（北京时间）从昨天...'))

            # True

        """
        if text == '':
            return False

        if self.chinese_any_char_pattern is None:
            self.chinese_any_char_pattern = re.compile(CHINESE_CHAR_PATTERN)

        if self.chinese_any_char_pattern.search(text):
            return True

        return False

    def check_all_chinese_char(self, text):
        """ 检查文本中是否全部为中文字符，若全部都是，则返回 True；
        若至少有一个不是中文字符，否则返回 False。
        若为空字符串，返回 False

        Args:
            text(str): 输入的文本
        Return:
            bool: 文本中是否包含中文字符

        Examples:
            >>> import jionlp as jio
            >>> print(jio.check_all_chinese_char('【新华社消息】（北京时间）从昨天...'))

            # False

        """
        if text == '':
            return False

        if self.chinese_all_char_pattern is None:
            self.chinese_all_char_pattern = re.compile(CHINESE_CHAR_PATTERN + '+')

        matched_res = self.chinese_all_char_pattern.search(text)
        if matched_res:
            span = matched_res.span()
            if span[1] - span[0] == len(text):

                return True
            else:
                return False

        return False

    def check_any_arabic_num(self, text):
        """ 检查文本中是否包含阿拉伯数字字符，若至少包含一个，则返回 True，否则返回 False。
        若为空字符串，返回 False。

        Args:
            text(str): 输入的文本
        Return:
            bool: 文本中是否包含阿拉伯字符

        Examples:
            >>> import jionlp as jio
            >>> print(jio.check_any_arabic_num('【新华社消息】（北京时间2022-11-28）...'))

            # True

        """
        if text == '':
            return False

        if self.any_arabic_num_pattern is None:
            self.any_arabic_num_pattern = re.compile(r'(\d|[０１２３４５６７８９])')

        if self.any_arabic_num_pattern.search(text):
            return True

        return False

    def check_all_arabic_num(self, text):
        """ 检查文本中是否全部为阿拉伯数字字符，若全部都是，则返回 True；
        若至少有一个不是，则返回 False。
        若为空字符串，返回 False。

        Args:
            text(str): 输入的文本
        Return:
            bool: 文本中是否全部为阿拉伯数字字符

        Examples:
            >>> import jionlp as jio
            >>> print(jio.check_all_arabic_num('20221128'))

            # True

        """
        if text == '':
            return False

        if self.all_arabic_num_pattern is None:
            self.all_arabic_num_pattern = re.compile(r'(\d|[０１２３４５６７８９])+')

        matched_res = self.all_arabic_num_pattern.search(text)
        if matched_res:
            span = matched_res.span()
            if span[1] - span[0] == len(text):

                return True
            else:
                return False

        return False
