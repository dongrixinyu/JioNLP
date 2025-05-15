# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com

import re
import time
import datetime
import traceback

from jionlp.rule.rule_pattern import *
from ..money_parser import MoneyParser


class TimeUtility(object):
    """
    时间解析的助手类，主要包括时间比较函数，等等。
    """

    @staticmethod
    def _compare_handler(first_handler, second_handler):
        """ 比较两个 handler 的时间先后

        Args:
            first_handler: 第一个 handler
            second_handler: 第二个 handler

        Returns:
            若第一个时间和第二个时间相同，返回 0
            若第一个时间早于第二个时间，返回 -1
            若第一个时间晚于第二个时间，返回 1
        """
        for f, s in zip(first_handler, second_handler):
            if f == -1 or s == -1:
                break
            if f == s:
                continue
            elif f > s:
                return 1
            elif f < s:
                return -1

        return 0

    @staticmethod
    def _cut_zero_key(dict_obj):
        # 删除其中值为 0 的 key
        return dict([item for item in dict_obj.items() if item[1] > 0])

    @property
    def time_unit_names(self):
        return ['year', 'month', 'day', 'hour', 'minute', 'second']

    def __call__(self):
        # 实际上是父类的初始化，为了避免 jionlp 初次加载耗时，而放入 __call__ 方法
        chinese_num = '零〇一二三四五六七八九'
        arabic_num = '00123456789'
        self.chinese_num_2_arabic_num = str.maketrans(chinese_num, arabic_num)

        self.single_num_pattern = re.compile(SINGLE_NUM_STRING)

        self.big_moon = {1, 3, 5, 7, 8, 10, 12}
        self.small_moon = {4, 6, 9, 11}

        self.future_time = 'inf'
        self.past_time = '-inf'

        self.money_parser = MoneyParser()

    @staticmethod
    def parse_pattern(time_string, pattern):
        """ 公共解析函数 """
        searched_res = pattern.search(time_string)
        if searched_res:
            # logging.info(''.join(['matched: ', searched_res.group(),
            #                       '\torig: ', time_string]))
            return searched_res.group()
        else:
            return ''

    def _char_num2num(self, char_num):
        """ 将 三十一 转换为 31，用于月、日、时、分、秒的汉字转换

        :param char_num:
        :return: float 类型的数字
        """
        res_num = self.money_parser(char_num, ret_format='str')
        if res_num is None:
            return 0
        else:
            return float(res_num[:-1])

    def chinese_year_char_2_arabic_year_char(self, char_year):
        """ 将 二零一九 年份转化为 2019 """
        arabic_year_char = char_year.translate(self.chinese_num_2_arabic_num)
        return arabic_year_char

    @staticmethod
    def time_completion(time_handler, time_base_handler):
        """根据时间基，补全 time_handler，即把 time_handler 前部 -1 部分补齐

        :param time_handler:
        :param time_base_handler:
        :return:
        """
        if time_handler in ['inf', '-inf']:
            return time_handler

        for i in range(len(time_handler)):
            if time_handler[i] > -1:
                break
            time_handler[i] = time_base_handler[i]

        return time_handler

    @staticmethod
    def check_handler(time_handler):
        """
        字符串合法校验，形如 [-1, 11, 29, -1, 23, -1] ，即中间部位有未指明时间，为非法时间字符串，
        左侧未指明时间须根据 base_time 补充完整，右侧未指明时间可省略，或按时间段补全
        """
        if time_handler in ['inf', '-inf']:
            return True

        assert len(time_handler) == 6
        # 未识别出任何时间串，即全部为 -1：[-1, -1, -1, -1, -1, -1]
        if set(time_handler) == {-1}:
            return False

        first = False
        second = False
        for i in range(5):
            if time_handler[i] > -1 and time_handler[i + 1] == -1:
                first = True
            if time_handler[i] == -1 and time_handler[i + 1] > -1:
                if first:
                    second = True

        if first and second:
            return False
        return True

    @staticmethod
    def _convert_time_base2handler(time_base):
        """将 time_base 转换为 handler,"""

        # if type(time_base) is arrow.arrow.Arrow:
        #     time_base_handler = [
        #         time_base.year, time_base.month, time_base.day,
        #         time_base.hour, time_base.minute, time_base.second]
        if type(time_base) in [float, int]:
            # 即 timestamp
            time_array = datetime.datetime.fromtimestamp(time_base)
            time_base_handler = [
                time_array.year, time_array.month, time_array.day,
                time_array.hour, time_array.minute, time_array.second]
        elif type(time_base) is datetime.datetime:
            time_base_handler = [
                time_base.year, time_base.month, time_base.day,
                time_base.hour, time_base.minute, time_base.second]
        elif type(time_base) is list:
            assert len(time_base) <= 6, 'length of time_base must be less than 6.'
            for i in time_base:
                assert type(i) is int, 'type of element of time_base must be `int`.'
            if len(time_base) < 6:
                time_base.extend([-1 for _ in range(6 - len(time_base))])
            time_base_handler = time_base
        elif type(time_base) is dict:
            time_base_handler = [
                time_base.get('year', -1), time_base.get('month', -1),
                time_base.get('day', -1), time_base.get('hour', -1),
                time_base.get('minute', -1), time_base.get('second', -1)]
        elif type(time_base) is str:
            time_array = time.strptime(time_base, "%Y-%m-%d %H:%M:%S")
            time_base_handler = [
                time_array.tm_year, time_array.tm_mon, time_array.tm_mday,
                time_array.tm_hour, time_array.tm_min, time_array.tm_sec]
        elif time_base is None:
            time_base_handler = None
        else:
            raise ValueError('the given time_base is illegal.')

        return time_base_handler

    @staticmethod
    def _convert_handler2datetime(handler):
        """将 time handler 转换为 datetime 类型

        :param handler:
        :return:
        """
        new_handler = []
        for idx, i in enumerate(handler):
            if i > -1:
                new_handler.append(i)
            else:
                if idx in [0, 1, 2]:
                    new_handler.append(1)  # 月、日 从 1 开始计数
                elif idx in [3, 4, 5]:
                    new_handler.append(0)  # 时分秒从 0 开始计数

        return datetime.datetime(*new_handler)

    @staticmethod
    def _cleansing(time_string):
        return time_string.strip()  # .replace(' ', '')

    def time_handler2standard_time(self, first_time_handler, second_time_handler):
        """ 将 time handler 转换为标准时间格式字符串
        复杂点在于需要控制解析 -1 的情况

        :param first_time_handler:
        :param second_time_handler:
        :return:
        """
        first_handler = []
        second_handler = []
        if first_time_handler == self.past_time:
            first_time_string = self.past_time
        else:
            for idx, f in enumerate(first_time_handler):
                if f > -1:
                    first_handler.append(f)
                elif f == -1:
                    if idx in [1, 2]:
                        first_handler.append(1)
                    elif idx in [3, 4, 5]:
                        first_handler.append(0)
                    else:
                        raise ValueError('first time handler {} illegal.'.format(first_handler))
                else:
                    raise ValueError('before Christ {} can not be converted to standard time pattern.'.format(
                        first_time_handler))

            try:
                first_time_string = TimeUtility._convert_handler2datetime(first_handler)
            except Exception:
                raise ValueError('the given time string is illegal.\n{}'.format(
                    traceback.format_exc()))

            first_time_string = first_time_string.strftime('%Y-%m-%d %H:%M:%S')

        if second_time_handler == self.future_time:
            second_time_string = self.future_time
        else:
            for idx, s in enumerate(second_time_handler):
                if s > -1:
                    second_handler.append(s)
                elif s == -1:
                    if idx == 1:
                        second_handler.append(12)
                    elif idx == 2:
                        if second_handler[1] in self.big_moon:
                            second_handler.append(31)
                        elif second_handler[1] in self.small_moon:
                            second_handler.append(30)
                        else:
                            if (second_handler[0] % 100 != 0 and second_handler[0] % 4 == 0) \
                                    or (second_handler[0] % 100 == 0 and second_handler[0] % 400 == 0):
                                second_handler.append(29)
                            else:
                                second_handler.append(28)
                    elif idx == 3:
                        second_handler.append(23)
                    elif idx == 4:
                        second_handler.append(59)
                    elif idx == 5:
                        second_handler.append(59)
                    else:
                        raise ValueError('second time handler {} illegal.'.format(second_handler))
                else:
                    raise ValueError('before Christ {} can not be converted to standard time pattern.'.format(
                        second_time_handler))

            try:
                second_time_string = TimeUtility._convert_handler2datetime(second_handler)
            except Exception:
                raise ValueError('the given time string is illegal.\n{}'.format(
                    traceback.format_exc()))

            second_time_string = second_time_string.strftime('%Y-%m-%d %H:%M:%S')

        return first_time_string, second_time_string

    def map_time_unit(self, destination_time_handler, source_time_handler, unit=None):
        """代码中有大量的时间的赋值，很啰嗦，因此制此函数方便函数的映射赋值

        我们约定，destination_time_handler 和 source_time_handler
        都具备 year/month/day/hour/minite/second 等属性，

        函数即根据 source 的指定属性赋值在  destination 上面。
        """
        if unit is None:
            return destination_time_handler

        for u in unit:
            value = getattr(source_time_handler, u)
            setattr(destination_time_handler, u, value)

        return destination_time_handler
