# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re

from jionlp.util.funcs import bracket, bracket_absence
from jionlp.rule.rule_pattern import *
from .time_utility import TimeUtility


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


class TimeDeltaParser(TimeUtility):
    """ 时间长度解析器

    """

    def __init__(self):
        # 实际上是初始化
        super(TimeDeltaParser, self).__call__()

        # ----- TIME DELTA -----
        # 对时间段的描述
        # 其中，年、日、秒 容易引起歧义，如 `21年`，指`二十一年` 还是 `2021年`。
        # `18日`，指`18号`，还是`18天`。这里严格规定，日指时间点，天指时间段。
        # `58秒`，指`五十八秒`的时间，还是`58秒`时刻。
        self.exception_standard_delta_pattern = re.compile(
            r'(([12]\d{3}|[一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4})年'
            r')')
        self.ambivalent_delta_point_pattern = re.compile(
            r'(' + DAY_NUM_STRING + '日|'
                                    r'\d{2}年)')  # 满足该正则，说明既符合 point，又符合 delta；若非明确指定，默认按 point 处理
        self.delta_num_pattern = re.compile(DELTA_NUM_STRING)

        self.year_delta_pattern = re.compile(bracket(YEAR_DELTA_STRING))
        self.solar_season_delta_pattern = re.compile(bracket(SOLAR_SEASON_DELTA_STRING))
        self.month_delta_pattern = re.compile(bracket(MONTH_DELTA_STRING))
        self.workday_delta_pattern = re.compile(bracket(WORKDAY_DELTA_STRING))
        self.day_delta_pattern = re.compile(bracket(DAY_DELTA_STRING))
        self.week_delta_pattern = re.compile(bracket(WEEK_DELTA_STRING))
        self.hour_delta_pattern = re.compile(bracket(HOUR_DELTA_STRING))
        self.quarter_delta_pattern = re.compile(bracket(QUARTER_DELTA_STRING))
        self.minute_delta_pattern = re.compile(bracket(MINUTE_DELTA_STRING))
        self.second_delta_pattern = re.compile(bracket(SECOND_DELTA_STRING))

        self.standard_delta_pattern = re.compile(
            ''.join(['^(', bracket(YEAR_DELTA_STRING), I,
                     bracket(SOLAR_SEASON_DELTA_STRING), I,
                     bracket(MONTH_DELTA_STRING), I,
                     bracket(WORKDAY_DELTA_STRING), I,
                     bracket(DAY_DELTA_STRING), I,
                     bracket(WEEK_DELTA_STRING), I,
                     bracket(HOUR_DELTA_STRING), I,
                     bracket(QUARTER_DELTA_STRING), I,
                     bracket(MINUTE_DELTA_STRING), I,
                     bracket(SECOND_DELTA_STRING), ')+$']))

        standard_delta_string = ''.join(
            ['(', bracket(YEAR_DELTA_STRING), I,
             bracket(SOLAR_SEASON_DELTA_STRING), I,
             bracket(MONTH_DELTA_STRING), I,
             bracket(WORKDAY_DELTA_STRING), I,
             bracket(DAY_DELTA_STRING), I,
             bracket(WEEK_DELTA_STRING), I,
             bracket(HOUR_DELTA_STRING), I,
             bracket(MINUTE_DELTA_STRING), I,
             bracket(SECOND_DELTA_STRING), ')+'])

        self.weilai_delta2span_pattern = re.compile(
            ''.join(['(未来|今后)(的)?', standard_delta_string, '[里内]?']))

        self.guoqu_delta2span_pattern = re.compile(
            ''.join(['((过去)(的)?|(最)?近)', standard_delta_string, '[里内]?']))

        self.guo_delta2span_pattern = re.compile(
            ''.join(['(再)?(过)', standard_delta_string]))

        self.law_delta_pattern = re.compile(
            ''.join([DELTA_NUM_STRING, '(年|个月|日|天)(以[上下])',
                     bracket_absence(''.join(['[、,，]?', DELTA_NUM_STRING, '(年|个月|日|天)(以下)']))]))

        # 将时间段转换为时间点
        self.year_delta_point_pattern = re.compile(''.join([bracket(YEAR_DELTA_STRING), DELTA_SUB]))
        self.solar_season_delta_point_pattern = re.compile(''.join([bracket(SOLAR_SEASON_DELTA_STRING), DELTA_SUB]))
        self.month_delta_point_pattern = re.compile(''.join([bracket(MONTH_DELTA_STRING), DELTA_SUB]))
        self.workday_delta_point_pattern = re.compile(''.join([bracket(WORKDAY_DELTA_STRING), DELTA_SUB]))
        self.day_delta_point_pattern = re.compile(''.join([bracket(DAY_DELTA_STRING), DELTA_SUB]))
        self.week_delta_point_pattern = re.compile(''.join([bracket(WEEK_DELTA_STRING), DELTA_SUB]))
        self.hour_delta_point_pattern = re.compile(''.join([bracket(HOUR_DELTA_STRING), DELTA_SUB]))
        self.quarter_delta_point_pattern = re.compile(''.join([bracket(QUARTER_DELTA_STRING), DELTA_SUB]))
        self.minute_delta_point_pattern = re.compile(''.join([bracket(MINUTE_DELTA_STRING), DELTA_SUB]))
        self.second_delta_point_pattern = re.compile(''.join([bracket(SECOND_DELTA_STRING), DELTA_SUB]))

        self.year_order_delta_point_pattern = re.compile(''.join([r'第', DELTA_NUM_STRING, r'年']))
        self.day_order_delta_point_pattern = re.compile(''.join([r'第', DELTA_NUM_STRING, r'[天日]']))

        # 由于 time_span 格式造成的时间单位缺失的检测
        # 如：`9~12个月`、 `8——10个星期`
        self.time_span_delta_compensation = re.compile(
            r'[\d一两二三四五六七八九十百千万零]{1,10}(到|至|——|－－|--|~~|～～|—|－|-|~|～)'
            r'([\d一两二三四五六七八九十百千万零]{1,10}(年|个月|周|(个)?(星期|礼拜)|日|天|(个)?(小时|钟头)|分钟|秒))')
        self.time_delta_exception_pattern = re.compile(
            r'(' + bracket(YEAR_STRING) + I + bracket(DAY_STRING) + r')')


        # for delta span pattern
        self.first_delta_span_pattern = re.compile(r'([^到至\-—~～]+)(?=(——|--|~~|～～|－－|到|至|－|—|-|~|～))')
        self.second_1_delta_span_pattern = re.compile(r'(?<=(——|--|~~|～～|－－))([^到至\-—~～]+)')
        self.second_2_delta_span_pattern = re.compile(r'(?<=[到至－—\-~～])([^到至－\-—~～]+)')

        # 特殊时间表述
        self.special_time_delta_pattern = re.compile(
            r'(' + SINGLE_NUM_STRING + r'天' + SINGLE_NUM_STRING + '[夜晚]|' + \
            SINGLE_NUM_STRING + '+[个载度]春秋|一年四季|大半(天|年|(个)?(月|小时|钟头)))')
        self.special_time_span_pattern = re.compile(
            r'(今明两[天年]|全[天月年])')

    def _compensate_delta_string(self, time_string, first_time_string, second_time_string):
        """ 补全 time_delta 时间字符串缺失部分 """
        time_compensation = self.time_span_delta_compensation.search(time_string)
        time_compensation_exception = self.time_delta_exception_pattern.search(time_string)
        if time_compensation and (time_compensation_exception is None):
            time_compensation = time_compensation.group()

            # compensate the first
            if '年' in time_compensation:
                first_time_string = ''.join([first_time_string, '年'])
            elif '个月' in time_compensation:
                first_time_string = ''.join([first_time_string, '个月'])
            elif '星期' in time_compensation or '周' in time_compensation or '礼拜' in time_compensation:
                first_time_string = ''.join([first_time_string, '个星期'])
            elif '日' in time_compensation or '天' in time_compensation:
                first_time_string = ''.join([first_time_string, '天'])
            elif '小时' in time_compensation or '钟头' in time_compensation:
                first_time_string = ''.join([first_time_string, '个小时'])
            elif '秒' in time_compensation:
                first_time_string = ''.join([first_time_string, '秒钟'])
            elif '分' in time_compensation:
                first_time_string = ''.join([first_time_string, '分钟'])

            return first_time_string, second_time_string
        else:
            return first_time_string, second_time_string

    def parse_delta_span_2_2_delta(self, time_string):
        """时间段存在范围型表示，如 `6到9天`，`3个月到3年` 等。
        但有一些是较为特殊的，如`两三分钟`、`七八个小时` 等等。中间的介词被省略了。
        """

        if self.first_delta_span_pattern.search(time_string):
            first_string = self.first_delta_span_pattern.search(time_string).group()
        else:
            first_string = None

        if self.second_1_delta_span_pattern.search(time_string):
            second_string = self.second_1_delta_span_pattern.search(time_string).group()
        elif self.second_2_delta_span_pattern.search(time_string):
            second_string = self.second_2_delta_span_pattern.search(time_string).group()
        else:
            second_string = None

        return first_string, second_string

    def parse_time_delta_span(self, time_string, time_type=None):
        first_time_string, second_time_string = self.parse_delta_span_2_2_delta(time_string)
        if first_time_string is not None and second_time_string is not None:
            time_type = 'time_delta'
            first_time_string, second_time_string = self._compensate_delta_string(
                time_string, first_time_string, second_time_string)
            first_delta_dict, _, _ = self.parse_time_delta(first_time_string, time_type=time_type)
            second_delta_dict, _, _ = self.parse_time_delta(second_time_string, time_type=time_type)

            if first_delta_dict != dict() and second_delta_dict != dict():
                return {'type': time_type,
                        'definition': 'blur',
                        'time': [first_delta_dict, second_delta_dict]}
            else:
                return None
        else:
            # 非 time span delta，按 time_delta 解析
            delta_dict, time_type, blur_time = self.parse_time_delta(time_string, time_type=time_type)
            if delta_dict != {}:
                return {'type': 'time_delta',
                        'definition': blur_time,
                        'time': delta_dict}
            else:
                return None

    def parse_time_delta(self, time_string, time_type=None):
        """判断字符串是否为时间段。
        解析时间段，若可以解析，返回解析后的结果，若不可解析，则返回 None，跳转到其它类型解析 """

        # time_point pattern & norm_func
        delta_pattern_norm_funcs = [
            [self.standard_delta_pattern, self.normalize_standard_time_delta],
            [self.law_delta_pattern, self.normalize_law_delta],
            [self.special_time_delta_pattern, self.normalize_special_time_delta],
        ]

        cur_func = None
        cur_string = ''
        for delta_pattern, delta_func in delta_pattern_norm_funcs:
            delta_string = TimeUtility.parse_pattern(time_string, delta_pattern)

            if len(delta_string) > len(cur_string):
                cur_func = delta_func
                cur_string = delta_string

            if cur_string == time_string:
                break
            else:
                continue

        if len(cur_string) < len(time_string):
            return {}, time_type, 'blur'

        time_delta, time_type, blur_time = \
            cur_func(time_string, time_type=time_type)

        if type(time_delta) is list:
            delta_dict = [TimeUtility._cut_zero_key(i.__dict__) for i in time_delta]
        else:
            delta_dict = TimeUtility._cut_zero_key(time_delta.__dict__)

        return delta_dict, time_type, blur_time

    def normalize_standard_time_delta(self, time_string, time_type=None):
        """解析时间段，并根据 time_type 处理模糊情况 """

        time_delta = TimeDelta()

        # 对异常的时间做处理，如 `2014年`，不能按 time_delta 解析，必须为 time_span
        exception_res = self.exception_standard_delta_pattern.search(time_string)
        if exception_res is None:  # 未匹配到形如 `2014年` 的字符串
            ambi_res = self.ambivalent_delta_point_pattern.search(time_string)
            if ambi_res:
                if time_type in [None, 'time_point', 'time_span', 'time_period']:
                    return time_delta, 'time_point', 'blur'
                elif time_type == 'time_delta':
                    pass
        else:
            return time_delta, 'time_span', 'blur'

        time_definition = 'accurate'

        unit_list = [['second', 1, self.second_delta_pattern],
                     ['minute', 1, self.minute_delta_pattern],
                     ['minute', 15, self.quarter_delta_pattern],
                     ['hour', 1, self.hour_delta_pattern],
                     ['day', 1, self.day_delta_pattern],
                     ['workday', 1, self.workday_delta_pattern],
                     ['day', 7, self.week_delta_pattern],
                     ['month', 1, self.month_delta_pattern],
                     ['month', 3, self.solar_season_delta_pattern],
                     ['year', 1, self.year_delta_pattern]]

        for unit, multi, pattern in unit_list:
            time_delta_num, _time_definition = self._normalize_delta_unit(time_string, pattern)
            time_delta.__setattr__(unit, time_delta.__getattribute__(unit) + time_delta_num * multi)
            if time_delta_num > 0:
                time_definition = _time_definition

        return time_delta, 'time_delta', time_definition

    def normalize_law_delta(self, time_string, time_type=None):
        # 3年以上，7年以下

        if '以上' in time_string and '以下' in time_string:
            first_string, second_string = time_string.split('以上', 1)
            first_delta = self._normalize_law_delta_base(first_string)
            second_delta = self._normalize_law_delta_base(second_string)
            return [first_delta, second_delta], 'time_delta', 'blur'
        elif '以上' in time_string:
            time_delta = self._normalize_law_delta_base(time_string)
            second_delta = TimeDelta()
            second_delta.infinite = True
            return [time_delta, second_delta], 'time_delta', 'blur'
        elif '以下' in time_string:
            time_delta = self._normalize_law_delta_base(time_string)
            first_delta = TimeDelta()
            first_delta.zero = True
            return [first_delta, time_delta], 'time_delta', 'blur'
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

    def _normalize_law_delta_base(self, time_string):
        # 3年以上 或 7年以下
        time_delta = TimeDelta()
        delta_num = self.delta_num_pattern.search(time_string)
        if delta_num:
            delta_num_string = delta_num.group()
            time_delta_num = self._char_num2num(delta_num_string)

            if '年' in time_string:
                time_delta.year = time_delta_num
            elif '个月' in time_string:
                time_delta.month = time_delta_num
            elif '日' in time_string or '天' in time_string:
                time_delta.day = time_delta_num
            else:
                raise ValueError('the given `{}` is illegal.'.format(time_string))
            return time_delta
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

    def normalize_special_time_delta(self, time_string, time_type=None):
        """ 解析特殊的时间字符串 """
        # (r'(\d天\d夜|\d+个春秋|一年四季|大半[天年个月])')
        if '天' in time_string and ('夜' in time_string or '晚' in time_string):
            searched_num = self.single_num_pattern.search(time_string)
            if searched_num:
                time_delta = TimeDelta()
                time_delta.day = self._char_num2num(searched_num.group())
                return time_delta, 'time_delta', 'accurate'

        elif '春秋' in time_string:
            searched_num = self.single_num_pattern.search(time_string)
            if searched_num:
                time_delta = TimeDelta()
                time_delta.year = self._char_num2num(searched_num.group())
                return time_delta, 'time_delta', 'blur'

        elif '一年四季' in time_string:
            time_delta = TimeDelta()
            time_delta.year = 1
            return time_delta, 'time_delta', 'blur'

        elif '大半' in time_string:
            first_delta = TimeDelta()
            second_delta = TimeDelta()
            if '年' in time_string:
                first_delta.year = 0.5
                second_delta.year = 0.9
            elif '月' in time_string:
                first_delta.month = 0.5
                second_delta.month = 0.9
            elif '天' in time_string:
                first_delta.day = 0.5
                second_delta.day = 0.9
            elif '小时' in time_string or '钟头' in time_string:
                first_delta.hour = 0.5
                second_delta.hour = 0.9
            else:
                raise ValueError('the given `{}` is illegal.'.format(time_string))
            return [first_delta, second_delta], 'time_delta', 'blur'

        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

    def _normalize_delta_unit(self, time_string, pattern):
        """ 将 time_delta 归一化 """
        # 处理字符串的问题
        time_string = time_string.replace('俩', '两个')
        time_string = time_string.replace('仨', '三个')

        delta = pattern.search(time_string)
        time_delta = 0
        time_definition = 'accurate'

        if delta:
            delta_string = delta.group()
            delta_num = self.delta_num_pattern.search(delta_string)
            if delta_num:
                delta_num_string = delta_num.group()
                time_delta = float(self._char_num2num(delta_num_string))
            if '半' in time_string:
                if time_delta > 0:
                    time_delta += 0.5
                else:
                    time_delta = 0.5
                time_definition = 'blur'

            if '多' in time_string or '余' in time_string:
                time_definition = 'blur'

        return time_delta, time_definition
