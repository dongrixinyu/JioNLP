# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
解析时间周期

本意为 TimeParser 类过于复杂，想按不同解析类型进行分割。
但是目前发现，不同类型的耦合度相当高，很难分割处理。暂时搁置本文件代码。

"""

import re

from jionlp.rule.rule_pattern import DELTA_NUM_STRING
from .money_parser import MoneyParser


class TimeDelta(object):
    def __init__(self):
        self.year = 0
        # self.solar_season = 0
        self.month = 0
        # self.week = 0
        self.day = 0
        self.workday = 0  # 交易日、工作日等
        self.hour = 0
        self.minute = 0
        self.second = 0
        self.millisecond = 0  # 毫秒
        self.microsecond = 0  # 微秒
        self.nanosecond = 0  # 纳秒

        self.infinite = 0  # 无穷大
        self.zero = 0  # 无穷小


class TimePeriodParser(object):

    def __init__(self):
        self._prepare_regular_expression()

        self.money_parser = MoneyParser()

    def _prepare_regular_expression(self):
        # 周期性日期
        self.period_time_pattern = re.compile(
            r'每((间)?隔)?([一二两三四五六七八九十0-9]+|半)?'
            r'(年|(个)?季度|(个)?月|(个)?(星期|礼拜)|(个)?周|日|天|(个)?(小时|钟头)|分(钟)?|秒(钟)?)')

        self.delta_num_pattern = re.compile(DELTA_NUM_STRING)

    def _char_num2num(self, char_num):
        """ 将 三十一 转换为 31，用于月、日、时、分、秒的汉字转换

        :param char_num:
        :return:
        """
        res_num = self.money_parser(char_num, ret_format='str')
        if res_num is None:
            return 0
        else:
            return float(res_num[:-1])

    def __call__(self, time_string):

        return

    def normalize_time_period(self, time_string):
        num_res = self.delta_num_pattern.search(time_string)
        if num_res:
            num = self._char_num2num(num_res.group())
        else:
            if '半' in time_string:
                num = 0.5
            else:
                num = 1

        time_delta = TimeDelta()
        if '年' in time_string:
            time_delta.year = num
        elif '季度' in time_string:
            time_delta.month = num * 3
        elif '月' in time_string:
            time_delta.month = num
        elif '星期' in time_string or '周' in time_string or '礼拜' in time_string:
            time_delta.day = num * 7
        elif '日' in time_string or '天' in time_string:
            time_delta.day = num
        elif '小时' in time_string or '钟头' in time_string:
            time_delta.hour = num
        elif '分' in time_string:
            time_delta.minute = num
        elif '秒' in time_string:
            time_delta.second = num
        else:
            raise ValueError('the given `{}` has no correct time unit.'.format(time_string))

        return TimePeriodParser._cut_zero_key(time_delta.__dict__)

    @staticmethod
    def _cut_zero_key(dict_obj):
        # 删除其中值为 0 的 key
        cut_dict = dict()
        for unit, num in dict_obj.items():
            if num > 0:
                cut_dict.update({unit: num})
        return cut_dict

