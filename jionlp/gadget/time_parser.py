# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com

"""
TODO:
    2、时间段的解析中的问题：
    3、时分秒解析中的问题：
        1、9点到半夜1点，其中1点已经属于第二天，需要对其 day 做调整
        2、8点到中午12点，一般来讲，12点指12:00，而非 12:59，与年月日的默认规则有区别
        3、9号半夜2点，一般指第二天的半夜2点，即10号的 02:00
        4、昨晚2点半，究竟指今天2点半，还是昨天的2点半
    4、时间类型的定义、时间表达模糊程度的定义存在误差
    5、时间范围存在的模糊与歧义
        1、下周二起，仅表明起始时间，未表明结束时间，而 time_base 为此时此刻，
        2、两三年后，七八个小时前，模糊性较强
        3、两年前，究竟指，（两年前为时间范围的结束，而起始未知），还是（两年前的那一整年）
        4、
    6、时间修饰词
        “春天的时候”，其中，“的时候” 仅为时间修饰词，不具有任何含义，
        此时，时间无意义修饰词应当被包含在时间实体当中，应当被抽取，但不被解析

TODO unresolved:
    1、中秋节前后两个周末
    2、几十天后
    5、2016财年  => 财年
    6、两年间  => 间
    7、36天5小时30分后  => 多单位 time_delta to time_span
    8、晚上8点到上午10点之间
    9、明天下午3点至8点  => 自动将 8点识别为晚上 8点
    前个礼拜 => 上个，而非 上上个，与前天不同
    36天5小时30分后
    2021.2.1.24：00
    2021-09-09T09:09
    2020.01.2.24：00
    20.1.2十二点
    20.1.2八点十五分
    公告之日起至2020年1月15日17时30分，未知时间“公告之日”
    2008年内
    一两天 => 1~2 day
    本周二和周三 => 不应当拆分为两个日期
    北京时间今天（10月11日）17时59分
    08年04-03
    2021年09月23
    年前
    腊月18 => 农历日期存在小写
    此时
    2.15 => 既可解析为小数 二点一五，也可解析为 二月十五日

Problem:
    礼拜1 => 是否支持此种类型？一般地，星期不支持阿拉伯数字，容易在 extract_time 中产生歧义
    今天是12月16日，星期四，农历十一月十三 => 所有日期都指向同一个时间，不应当分开解析。抑或，应当分别解析为相同的时间
    "20201110" => 是否应当解析
    在签署本合同30日之前 => 30日被解析为当月 30号
    "本月10号-20号 10点-20点" => 双 span 构成 period
    每年阴历4月3日 元月25号和元月30号 => 这种 公农历 交错的日期应该如何解析
    2021年12月29日 至 2021年12月31日，每天上午9:00至11:30，下午14:30至17:00。时间周期
    订单日期在2019-10-11和2019-11-11之间的销售金额 => time_span 由 和 字连接
    2021年近期1个季度
    2020年农历二月初 => 扩展农历日期的描述
    未来十天 => 从现在起计算的十天
    最近3天 => 过去的三天  or 从现在起计算的三天
    去年中秋节前后 => 模糊时间

"""

import re
import time
import datetime
import traceback

from jionlp import logging
from jionlp.util.funcs import bracket, bracket_absence, absence
from .lunar_solar_date import LunarSolarDate
from jionlp.rule.rule_pattern import *
from .time_parser_new.time_utility import TimeUtility
from .time_parser_new.time_delta import TimeDeltaParser, TimeDelta


class TimePoint(object):
    def __init__(self):
        self.year, self.month, self.day = -1, -1, -1
        self.hour, self.minute, self.second = -1, -1, -1

    def handler(self):
        return [self.year, self.month, self.day,
                self.hour, self.minute, self.second]

    def __repr__(self):
        return 'TimePoint: {},{},{}  {},{},{}'.format(
            self.year, self.month, self.day, self.hour, self.minute, self.second)

    def assign(self, *args):
        args_num = len(args)
        if args_num >= 1:
            self.year = args[0]
        if args_num >= 2:
            self.month = args[1]
        if args_num >= 3:
            self.day = args[2]
        if args_num >= 4:
            self.hour = args[3]
        if args_num >= 5:
            self.minute = args[4]
        if args_num >= 6:
            self.second = args[5]


class TimeParser(TimeUtility):
    """将时间表达式转换为标准的时间，
    分为 time_point, time_span, time_period, time_delta, 后期还包括 time_query, time_virtual,
    分别表示 询问时间，如 “多少个月”，虚拟时间，如 “第十天”。

    解析步骤：
        1、将时间做预处理，形成标准可解析字符串
        2、对标准可解析字符串做解析，形成标准的时间

    注意事项：
        1、该工具一般情况下需要保证时间字符串（又称时间实体）中不包含噪音，如 “就在今天上午9点半，” 中的 “就在” 和 “，”，易造成解析错误。
            因此，若输入的文本是一篇文章，首先第一步需要从中抽取出时间字符串，此功能可以通过 实体识别模型 完成，或使用
            jio.ner.extract_time 方法进行抽取。
        2、时间语义 99% 可通过正则解决，但有一些复杂时间表达很难通过正则完成，例如 “今年中秋节前后两个双休日”，
            本工具暂不支持超复杂时间字符串。后续考虑别的办法优化解决。
        3、该工具持续更新，需要经过实践考验，如有解析错误非常正常，请提 issue 或拉 PR。

    Args:
        time_string(str): 时间字符串，该时间字符串尽量不要包含噪声，如 “就在今天上午9点半，” 中的 “就在” 和 “，”，易造成解析错误
        time_base(float|int|str|list|dict|Datetime): 时间基，默认为当前调用时间 time.time()，此外还支持 时间戳 (float, int)，
            datetime、标准时间 str（如：2021-08-15 10:48:00）、list、dict 等类型。
            充分方便输入对接。
        time_type(str|None): 时间类型，包括上述若干时间类型字符串，默认为 None。该参数用于指定模糊性字符串的处理类型，
            如：“30日”，既可按 time_point 解析，也可按 time_delta 解析，此时 time_type 参数生效，否则按其中一个类型返回结果。
        ret_typr(str): 包括 'str' 和 'int' 两种， 默认为 'str'，返回结果为标准时间字符串，若为 'int' 返回时间戳。
        strict(bool): 该参数检查时间字符串是否包含噪声，若包含噪声，则直接报错。默认为 False，一般不建议设为 True。
        ret_future(bool): 返回偏向未来的时间，如 `周一` 可按 `下周一` 进行解析。
        period_results_num(int): 当返回类型为 time_period 时，可以指定返回多少个具体的时间点。默认为 None。
            该参数设置的原因在于，时间周期的结构化描述非常困难，例如 `每个工作日上午9点`，包含了 每周 7 天，每周工作日 5天，每天上午 9 点
            三重周期，想要以结构化方式表示这三重信息非常困难。并且，时间周期，更加常用于表达从 time_base 起之后的时间。因此，直接采用
            返回时间周期实例的方式进行返回。该参数表示返回多少个实例，其中，第一个实例为最靠近传输 time_base 的实例。按时间顺序以此类推。

    Returns:
        见 Examples

    Examples:
        >>> import time
        >>> import jionlp as jio
        >>> res = jio.parse_time('今年9月', time_base={'year': 2021})
        >>> res = jio.parse_time('零三年元宵节晚上8点半', time_base=time.time())
        >>> res = jio.parse_time('一万个小时')
        >>> res = jio.parse_time('100天之后', time.time())
        >>> res = jio.parse_time('每周五下午4点', time.time(), peroid_results_num=2)
        >>> print(res)

        # {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-09-01 00:00:00', '2021-09-30 23:59:59']}
        # {'type': 'time_point', 'definition': 'accurate', 'time': ['2003-02-15 20:30:00', '2003-02-15 20:30:59']}
        # {'type': 'time_delta', 'definition': 'accurate', 'time': {'hour': 10000.0}}
        # {'type': 'time_span', 'definition': 'blur', 'time': ['2021-10-22 00:00:00', 'inf']}
        # {'type': 'time_period', 'definition': 'accurate', 'time': {'delta': {'day': 7},
        #  'point': {'time': [['2021-07-16 16:00:00', '2021-07-16 16:59:59'],
                              ['2021-07-23 16:00:00', '2021-07-23 16:59:59']], 'string': '周五下午4点'}}}

    """
    def __init__(self):

        self.time_point = None
        self.time_base_handler = None
        self.future_time = None

    def _preprocess(self):
        super(TimeParser, self).__call__()
        self.time_delta = TimeDeltaParser()

        # 20世纪 key值
        _20_century_solar_terms_key = [
            6.11, 20.84, 4.6295, 19.4599, 6.3826, 21.4155, 5.59, 20.888, 6.318, 21.86, 6.5, 22.2,
            7.928, 23.65, 8.35, 23.95, 8.44, 23.822, 9.098, 24.218, 8.218, 23.08, 7.9, 22.6]
        _21_century_solar_terms_key = [
            5.4055, 20.12, 3.87, 18.73, 5.63, 20.646, 4.81, 20.1, 5.52, 21.04, 5.678, 21.37, 7.108,
            22.83, 7.5, 23.13, 7.646, 23.042, 8.318, 23.438, 7.438, 22.36, 7.18, 21.94]

        def get_solar_terms(st_key):
            # 二十四节气字典-- key值, 月份，(特殊年份，相差天数)
            solar_terms = {
                '小寒': [st_key[0], '1', (2019, -1), (1982, 1)],
                '大寒': [st_key[1], '1', (2082, 1)],
                '立春': [st_key[2], '2', (None, 0)],
                '雨水': [st_key[3], '2', (2026, -1)],
                '惊蛰': [st_key[4], '3', (None, 0)],
                '春分': [st_key[5], '3', (2084, 1)],
                '清明': [st_key[6], '4', (None, 0)],
                '谷雨': [st_key[7], '4', (None, 0)],
                '立夏': [st_key[8], '5', (1911, 1)],
                '小满': [st_key[9], '5', (2008, 1)],
                '芒种': [st_key[10], '6', (1902, 1)],
                '夏至': [st_key[11], '6', (None, 0)],
                '小暑': [st_key[12], '7', (2016, 1), (1925, 1)],
                '大暑': [st_key[13], '7', (1922, 1)],
                '立秋': [st_key[14], '8', (2002, 1)],
                '处暑': [st_key[15], '8', (None, 0)],
                '白露': [st_key[16], '9', (1927, 1)],
                '秋分': [st_key[17], '9', (None, 0)],
                '寒露': [st_key[18], '10', (2088, 0)],
                '霜降': [st_key[19], '10', (2089, 1)],
                '立冬': [st_key[20], '11', (2089, 1)],
                '小雪': [st_key[21], '11', (1978, 0)],
                '大雪': [st_key[22], '12', (1954, 1)],
                '冬至': [st_key[23], '12', (2021, -1), (1918, -1)]
            }
            return solar_terms

        self._20_century_solar_terms = get_solar_terms(_20_century_solar_terms_key)
        self._21_century_solar_terms = get_solar_terms(_21_century_solar_terms_key)

        lunar_solar_date = LunarSolarDate()
        self.lunar2solar = lunar_solar_date.to_solar_date
        self.solar2lunar = lunar_solar_date.to_lunar_date

        self._preprocess_regular_expression()

        # 依次是，模糊时间词，first_time_point.hour, second_time_point.hour
        self.blur_time_info_map = [
            [['清晨'], 5, 7], [['清早'], 5, 8],
            [['早上', '早晨', '一早', '一大早'], 6, 9],
            [['黎明'], 4, 6], [['白天'], 6, 18], [['上午'], 7, 11],
            [['中午'], 12, 13], [['午后'], 13, 14],
            [['下午'], 13, 17], [['傍晚'], 17, 18],
            [['晚', '晚上'], 18, 23], [['晚间', '夜间', '夜里'], 20, 23], [['深夜'], 23, 23],
            [['上半夜', '前半夜'], 0, 2], [['下半夜', '后半夜'], 2, 4],
            [['半夜', '凌晨'], 0, 4], [['午夜'], 0, 0]
        ]

        self.string_strict = False
        self.ymd_pattern_norm_funcs = None
        self.hms_pattern_norm_funcs = None

    def _preprocess_regular_expression(self):
        # 未来时间扩展 单元基，合并或分开是个问题
        self.future_time_unit_pattern = re.compile('(年|月|周|星期|礼拜|日|号|节|时|点)')
        self.future_time_unit_hms_pattern = re.compile('(时|点|分)')

        # 中文字符判定
        self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)

        # --------------- 超模糊模式 -----------------

        # 超模糊 两 模式
        self.super_blur_two_ymd_pattern = re.compile('^前两(天|(个)?月|年)$')
        self.super_blur_two_hms_pattern = re.compile('^前两((个)?(小时|钟头)|分钟|秒(钟)?)$')

        # -------------- TIME SPAN SEG -------------
        # 1997.02-2020.12 此类须强制拆分
        self.time_span_seg_standard_year_month_to_year_month = re.compile(
            r'((17|18|19|20|21)\d{2})[./](1[012]|[0]?\d)[\-]((17|18|19|20|21)\d{2})([./](1[012]|[0]?\d))?')

        self.time_span_no_seg_standard_year_month_day = re.compile(
            r'((17|18|19|20|21)\d{2})\-(1[012]|[0]?\d)[\-./](30|31|[012]?\d)|'
            r'((17|18|19|20|21)\d{2})[\-./](1[012]|[0]?\d)\-(30|31|[012]?\d)|'
            r'(^\d)(1[012]|[0]?\d)\-(30|31|[012]?\d)(^\d)')

        # --------- TIME POINT & TIME SPAN ---------
        # `标准数字 年、月、日`：`2016-05-22`、`1987.12-3`
        self.standard_year_month_day_pattern = re.compile(
            r'((17|18|19|20|21)\d{2})[\-./](1[012]|[0]?\d)([\-./](30|31|[012]?\d))?[ \t\u3000\-./]?|'
            r'((17|18|19|20|21)\d{2} (1[012]|[0]?\d) (30|31|[012]?\d))|'
            r'(1[012]|[0]?\d)[·\-/](30|31|[012]?\d)')

        # 无分隔符的8位 时间年、月、日： `20031204`
        self.standard_2_year_month_day_pattern = re.compile(
            r'((18|19|20)\d{2})(1[012]|0\d)(3[01]|[012]\d)')

        # `标准数字 年`：`2018`
        self.standard_year_pattern = re.compile(r'(17|18|19|20|21)\d{2}')

        # `年、月、日`：`2009年5月31日`、`一九九二年四月二十五日`
        self.year_month_day_pattern = re.compile(
            ''.join([bracket(YEAR_STRING), bracket_absence(MONTH_STRING), bracket_absence(DAY_STRING),
                     absence(TIME_POINT_SUFFIX), I,
                     bracket(MONTH_STRING), bracket_absence(DAY_STRING), absence(TIME_POINT_SUFFIX),
                     I, bracket(DAY_STRING), absence(TIME_POINT_SUFFIX)]))

        # `年、季度`：`2018年前三季度`
        self.year_solar_season_pattern = re.compile(
            ''.join([bracket_absence(YEAR_STRING), r'(([第前后头Qq]?[一二三四1-4两]|首)(个)?季度[初中末]?)']))

        # `限定年、季度`：`2018年前三季度`
        self.limit_year_solar_season_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), r'(([第前后头Qq]?[一二三四1-4两]|首)(个)?季度[初中末]?)']))

        # `限定季度`：`上季度`
        self.limit_solar_season_pattern = re.compile(r'([上下]+(一)?(个)?|本|这)季度[初中末]?')

        # `年、范围月`：`2018年前三个月`
        self.year_span_month_pattern = re.compile(
            ''.join([bracket_absence(YEAR_STRING),
                     r'(([第前后头]', MONTH_NUM_STRING, r'|首)(个)?月(份)?)']))

        # `年、范围月`：`2018年前三个月`
        self.limit_year_span_month_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING),
                     r'(([第前后头]', MONTH_NUM_STRING, r'|首)(个)?月(份)?)']))

        # `年、模糊月 时间段`：`1988年末`、`07年暑假`
        self.year_blur_month_pattern = re.compile(
            ''.join([bracket(YEAR_STRING), r'(年)?(初|[一]开年|伊始|末|尾|终|底)|',
                     bracket_absence(YEAR_STRING), r'([上|下]半年|[暑寒][假期]|[前中后]期)']))

        # `限定月、日`： `下个月9号`
        self.limit_month_day_pattern = re.compile(
            ''.join([bracket(LIMIT_MONTH_STRING), bracket_absence(DAY_STRING)]))

        # `限定月、模糊日`： `下个月末`
        self.limit_month_blur_day_pattern = re.compile(''.join([bracket(LIMIT_MONTH_STRING), BLUR_DAY_STRING]))

        # `限定月`： `下个月`
        self.limit_month_pattern = re.compile(LIMIT_MONTH_STRING)

        # `模糊年、模糊月 时间段`：`1988年末`、`07年暑假`
        self.limit_year_blur_month_pattern = re.compile(
            ''.join(['(', bracket(LIMIT_YEAR_STRING), '(年)?|年)', BLUR_MONTH_STRING]))

        # `指代年、月、日`：`今年9月`、`前年9月2日`
        self.limit_year_month_day_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), bracket_absence(MONTH_STRING),
                     bracket_absence(DAY_STRING), absence(TIME_POINT_SUFFIX)]))

        # `指代限定年`：`两年后`、`20多年前`
        # 1、如若遇到 `4年前的中秋节`，`30多年前的夏天`，则须分为两个时间词汇进行解析。很容易因年份模糊被误识别
        # 2、如若遇到 `3万年前`，因返回结果标准化格式无法解析，因而不予支持解析。
        # 3、`32年前` 指三十二年前，还是2032年前，存在矛盾，须依据上下文，
        #    三十二年前，多见小说、故事等题材，2032年前，多见于官方文档等文书中。因此，考虑官方文档的准确性，
        #    默认按照三十二年前处理，除非强调2032年。
        self.blur_year_pattern = re.compile(
            r'(\d{1,4}|[一二两三四五六七八九十百千]+)[几多]?年(半)?(多)?[以之]?[前后]|'
            r'半年(多)?[以之]?[前|后]|'
            r'几[十百千](多)?年[以之]?[前|后]')

        # `世纪、年代`：`20世纪二十年代`
        self.century_year_pattern = re.compile(
            r'(公元(前)?)?(\d{1,2}|((二)?十)?[一二三四五六七八九]|(二)?十|上)世纪'
            r'((\d0|[一二三四五六七八九]十)年代)?([初中末](期)?|前期|后期)?|'
            r'(\d0|[一二三四五六七八九]十)年代([初中末](期)?|前期|后期)?')

        # `（年、月）、枚举日`：十月21号、22号、23号， 9月1日，2日，3日
        self.enum_day_pattern = re.compile(
            ''.join([bracket_absence(YEAR_STRING), bracket_absence(MONTH_STRING),
                     bracket(DAY_STRING), bracket('[、，, ]' + bracket(DAY_STRING)), '+']))

        # `农历年、月、日`：二〇一七年农历正月十九
        self.lunar_year_month_day_pattern = re.compile(
            ''.join([
                # 2012年9月初十/9月初十/初十， `日`自证农历
                LU_A, bracket_absence(LUNAR_YEAR_STRING), LU_A, bracket_absence(LUNAR_MONTH_STRING),
                SELF_EVI_LUNAR_DAY_STRING, I,

                # 2012年冬月/2012年冬月初十/冬月初十/冬月， `月`自证农历
                LU_A, bracket_absence(LUNAR_YEAR_STRING), LU_A,
                bracket(SELF_EVI_LUNAR_MONTH_STRING), absence(LUNAR_SOLAR_DAY_STRING), I,

                # 强制标明农历，原因在于农历和公历的混淆，非常复杂
                bracket(LUNAR_YEAR_STRING), LU, bracket(LUNAR_MONTH_STRING), bracket(DAY_STRING), I,  # 2018年农历8月23号

                LU, bracket(LUNAR_YEAR_STRING), bracket(LUNAR_MONTH_STRING), I,  # 农历二零一二年九月
                bracket(LUNAR_YEAR_STRING), LU, bracket(LUNAR_MONTH_STRING), I,  # 二零一二年农历九月

                # 二月十五/2月十五/农历九月十二， `日`后无`日`字，自证农历
                LU_A, bracket(LUNAR_MONTH_STRING), LUNAR_DAY_STRING, I,

                LU, bracket(LUNAR_MONTH_STRING), I,  # 农历九月
                LU, bracket(LUNAR_YEAR_STRING), I,  # 农历二〇一二年
                LU, LUNAR_DAY_STRING]))  # 农历初十

        self.lunar_limit_year_month_day_pattern = re.compile(
            ''.join([
                # 非强制`农历`，根据 `日` 得知为农历日期
                LU_A, bracket(LIMIT_YEAR_STRING), LU_A, bracket(LUNAR_MONTH_STRING),
                SELF_EVI_LUNAR_DAY_STRING, I,  # 今年9月初十

                # 非强制`农历`，根据 `月` 得知为农历日期
                bracket(LIMIT_YEAR_STRING), LU_A, bracket(SELF_EVI_LUNAR_MONTH_STRING),
                absence(LUNAR_SOLAR_DAY_STRING), I,  # 2012年冬月/2012年冬月初十/冬月初十/冬月

                # 去年二月十五/去年2月十五/明年农历九月十二， `日`后无`日`字，自证农历
                LU_A, bracket(LIMIT_YEAR_STRING), LU_A,
                bracket(LUNAR_MONTH_STRING), LUNAR_DAY_STRING, I,

                # 强制标明`农历`，原因在于农历和公历的混淆
                LU, bracket(LIMIT_YEAR_STRING), I,  # 农历二〇一二年
                LU, bracket(LIMIT_YEAR_STRING), bracket(LUNAR_MONTH_STRING), I,  # 农历二零一二年九月
                bracket(LIMIT_YEAR_STRING), LU, bracket(LUNAR_MONTH_STRING)]))  # 二零一二年农历九月

        # 年、（农历）季节
        self.year_lunar_season_pattern = re.compile(
            ''.join([bracket_absence(LUNAR_YEAR_STRING),
                     r'[春夏秋冬][季天]|', bracket(LUNAR_YEAR_STRING), r'[春夏秋冬]']))

        # 限定年、（农历）季节
        self.limit_year_lunar_season_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), r'[春夏秋冬][季天]?']))

        # 年、节气
        self.year_24st_pattern = re.compile(''.join([bracket_absence(LUNAR_YEAR_STRING), SOLAR_TERM_STRING]))

        # 年、月、模糊日（旬）
        self.year_month_blur_day_pattern = re.compile(
            ''.join([bracket_absence(LUNAR_YEAR_STRING), bracket(MONTH_STRING), BLUR_DAY_STRING]))

        # 限定年、月、模糊日（旬）
        self.limit_year_month_blur_day_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), bracket(MONTH_STRING), BLUR_DAY_STRING]))

        # 星期 （一般不与年月相关联）
        self.standard_week_day_pattern = re.compile(
            '(上+|下+|本|这)?(一)?(个)?(周)?' + WEEK_STRING + '[一二三四五六日末天]')

        # 星期前后推算
        self.blur_week_pattern = re.compile(
            '[前后]' + WEEK_NUM_STRING + '(个)?' + WEEK_STRING + I +
            WEEK_NUM_STRING + '(个)?' + WEEK_STRING + '(之)?[前后]' + I +
            '(上+|下+|本|这)?(一)?(个)?' + WEEK_STRING)

        # 月、第n个星期k
        self.limit_week_pattern = re.compile(
            ''.join([bracket(MONTH_STRING), '(的)?',
                     '第[1-5一二三四五](个)?', WEEK_STRING, '[一二三四五六日末天]']))

        # 年、月、第n个星期
        self.year_month_week_pattern = re.compile(
            ''.join([bracket(YEAR_STRING), bracket(MONTH_STRING), '的?',
                     '第[1-5一二三四五](个)?', WEEK_STRING]))

        # 限定年、月、第n个星期
        self.limit_year_month_week_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), bracket(MONTH_STRING), '的?',
                     '第[1-5一二三四五](个)?', WEEK_STRING]))

        # 月、第n个星期
        self.month_week_pattern = re.compile(
            ''.join([bracket(MONTH_STRING), '(的)?',
                     '第[1-5一二三四五](个)?', WEEK_STRING]))

        # 限定月、第n个星期
        self.limit_month_week_pattern = re.compile(
            ''.join([bracket(LIMIT_MONTH_STRING), '(的)?',
                     '第[1-5一二三四五](个)?', WEEK_STRING]))

        # 年、第n个星期
        self.year_week_pattern = re.compile(
            ''.join([bracket(YEAR_STRING), '第', bracket(WEEK_NUM_STRING),
                     '(个)?', WEEK_STRING]))

        # 限定年、第n个星期
        self.limit_year_week_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), '第', bracket(WEEK_NUM_STRING),
                     '(个)?', WEEK_STRING]))

        # 1月1  此类不全的日期，缺少日
        # 注意，此种情况只针对 日 是 阿拉伯数字的情况，若是汉字 日，如 “五月二十”，则按农历进行解析，
        # 此时，则不存在日期的 “日” 的缺失。
        self.num_month_num_pattern = re.compile(
            ''.join(['^', MONTH_NUM_STRING, '月', r'([12]\d|3[01]|[0]?[1-9])', '$']))

        # 公历固定节日
        self.year_fixed_solar_festival_pattern = re.compile(
            ''.join([bracket_absence(YEAR_STRING), FIXED_SOLAR_FESTIVAL]))

        # 限定年 公历固定节日
        self.limit_year_fixed_solar_festival_pattern = re.compile(bracket(LIMIT_YEAR_STRING) + FIXED_SOLAR_FESTIVAL)

        # 农历固定节日
        self.year_fixed_lunar_festival_pattern = re.compile(
            ''.join([bracket_absence(YEAR_STRING), CONJ_A, LU_A, FIXED_LUNAR_FESTIVAL]))

        # 限定年 农历固定节日
        self.limit_year_fixed_lunar_festival_pattern = re.compile(
            ''.join([bracket(LIMIT_YEAR_STRING), CONJ_A, LU_A, FIXED_LUNAR_FESTIVAL, absence(TIME_POINT_SUFFIX)]))

        # 公历规律节日
        self.year_regular_solar_festival_pattern = re.compile(
            bracket_absence(YEAR_STRING) + REGULAR_FOREIGN_FESTIVAL)

        # 限定年 公历规律节日
        self.limit_year_regular_solar_festival_pattern = re.compile(
            bracket_absence(LIMIT_YEAR_STRING) + REGULAR_FOREIGN_FESTIVAL)

        # 限定性`日`
        self.limit_day_pattern = re.compile(
            r'(前|今|明|同一|当|后|大大前|大大后|大前|大后|昨|次|本)[天日晚]')

        # 时分秒 文字
        self.hour_minute_second_pattern = re.compile(
            ''.join([absence(BLUR_HOUR_STRING), bracket(HOUR_STRING),
                     bracket_absence(MIN_SEC_STRING + '分?'), bracket_absence(MIN_SEC_STRING + '秒'),
                     absence(TIME_POINT_SUFFIX), I,
                     bracket(MIN_SEC_STRING + '分'), bracket_absence(MIN_SEC_STRING + '秒'),
                     absence(TIME_POINT_SUFFIX)]))

        # 连续模糊 时
        self.consecutive_blur_hour_pattern = re.compile(
            ''.join([absence(BLUR_HOUR_STRING), bracket(CONSECUTIVE_BLUR_HOUR_STRING)]))

        # 标准格式`:`分隔时分秒
        self.num_hour_minute_second_pattern = re.compile(
            ''.join([absence(BLUR_HOUR_STRING),
                     r'([01]\d|2[01234]|\d)[:：]([012345]\d)([:：]([012345]\d))?',
                     absence(TIME_POINT_SUFFIX), r'(时)?', I,
                     r'([012345]\d)[:：]([012345]\d)', absence(TIME_POINT_SUFFIX), r'(时)?']))

        # 模糊性 `时` 段
        self.blur_hour_pattern = re.compile(BLUR_HOUR_STRING)

        # 限定性 `分`
        self.hour_limit_minute_pattern = re.compile(
            ''.join([absence(BLUR_HOUR_STRING), bracket(HOUR_STRING), r'([123一二三]刻|半)']))

        self.single_num_pattern = re.compile(SINGLE_NUM_STRING)

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
            ''.join(['((过去)(的)?|(最)?近|([之提]?前))', standard_delta_string, '[里内]?']))

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

        # XX年第N天：`2025年第一天`
        self.year_day_order_delta_point_pattern = re.compile(
            ''.join([YEAR_STRING[:-1] + r'年?', r'第', DELTA_NUM_STRING, r'[天日]']))

        # **** 年 ****
        self.year_pattern = re.compile(YEAR_STRING[:-1] + r'(?=年)')
        self.limit_year_pattern = re.compile(LIMIT_YEAR_STRING[:-1] + r'(?=年)')
        self.blur_year_1_pattern = re.compile(r'([12]?\d{1,4}|(?<!几)[一二两三四五六七八九十百千])[几多]?年(半)?(多)?[以之]?[前后]')
        self.blur_year_2_pattern = re.compile('半年(多)?[以之]?[前后]')
        self.blur_year_3_pattern = re.compile('几[十百千](多)?年[以之]?[前后]')

        self.lunar_year_pattern = re.compile('[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]年')

        self.century_pattern = re.compile(r'(\d{1,2}|((二)?十)?[一二三四五六七八九]|(二)?十|上)(?=世纪)')
        self.decade_pattern = re.compile(r'(\d0|[一二三四五六七八九]十)(?=年代)')
        self.year_num_pattern = re.compile('[一二两三四五六七八九十百千0-9]{1,4}')

        self.year_patterns = [self.year_pattern, self.limit_year_pattern, self.blur_year_1_pattern,
                              self.blur_year_2_pattern, self.blur_year_3_pattern, self.lunar_year_pattern]

        # **** 月 ****
        self.month_pattern = re.compile(MONTH_STRING)
        self.month_num_pattern = re.compile(MONTH_NUM_STRING)  # 1~12
        self.span_month_pattern = re.compile('([第前后头]([一二两三四五六七八九十]|十[一二]|[1-9]|1[012])|首)(个)?月(份)?')
        self.solar_season_pattern = re.compile(
            '((([第前后头Qq][一二三四1-4两]|首)(个)?|[一二三四1-4])季度[初中末]?)')
        self.blur_month_pattern = re.compile(BLUR_MONTH_STRING)
        self.lunar_month_pattern = re.compile(bracket(LUNAR_MONTH_STRING[:-1]) + '(?=月)')

        self.month_patterns = [self.month_pattern, self.solar_season_pattern, self.blur_month_pattern,
                               self.span_month_pattern, self.lunar_month_pattern, self.limit_month_pattern]

        # **** 日|星期 ****
        self.day_1_pattern = re.compile(DAY_STRING)
        self.day_2_pattern = re.compile(r'(前|今|明|同一|当|后|大大前|大大后|大前|大后|昨|次)(?=[天日晚])')  # 昨晚9点
        self.day_3_pattern = re.compile(BLUR_DAY_STRING)
        self.lunar_day_pattern = re.compile(LUNAR_DAY_STRING + '(?!月)')
        self.lunar_24st_pattern = re.compile(SOLAR_TERM_STRING)
        self.lunar_season_pattern = re.compile('([春夏秋冬][季天]?)')

        self.week_1_pattern = re.compile('[前后][一二两三四五六七八九1-9](个)?' + WEEK_STRING)
        self.week_2_pattern = re.compile('[一两三四五六七八九1-9](个)?' + WEEK_STRING + '(之)?[前后]')
        self.week_3_pattern = re.compile('(上+|下+|本|这)(一)?(个)?' + WEEK_STRING)
        self.week_4_pattern = re.compile(WEEK_STRING + '[一二三四五六日末天]')
        self.week_5_pattern = re.compile(''.join(['第', WEEK_NUM_STRING, '(个)?', WEEK_STRING]))
        self.ymd_segs = re.compile(r'[\-.·/ ]')
        self.week_num_pattern = re.compile(WEEK_NUM_STRING)

        self.day_patterns = [
            self.day_1_pattern, self.lunar_day_pattern, self.lunar_24st_pattern,
            self.lunar_season_pattern, self.day_3_pattern, self.week_1_pattern,
            self.week_2_pattern, self.week_3_pattern, self.week_4_pattern,
            self.week_5_pattern, self.day_2_pattern]

        # **** 时 ****
        self.hour_pattern = re.compile(
            HOUR_STRING.replace('[时点]', '') + r'(?=[时点])')
        self.hour_limitation_pattern = re.compile(BLUR_HOUR_STRING)
        self.consecutive_hour_pattern = re.compile(
            CONSECUTIVE_BLUR_HOUR_STRING.replace('[点]', '') + r'(?=[点])')

        self.hour_patterns = [self.hour_pattern, self.hour_limitation_pattern,
                              self.consecutive_hour_pattern]

        # **** 分 ****
        self.minute_pattern = re.compile(r'(?<=[时点])' + MIN_SEC_STRING + '(?=分)?')
        self.limit_minute_pattern = re.compile(r'(?<=[时点])([123一二三]刻|半)')

        self.minute_patterns = [self.minute_pattern, self.limit_minute_pattern]

        # **** 秒 ****
        self.second_pattern = re.compile(r'(?<=分)' + MIN_SEC_STRING + '(?=秒)?')
        self.hms_segs = re.compile('[:：]')
        self.second_patterns = [self.second_pattern, ]

        # for TIME_SPAN pattern
        self.first_1_span_pattern = re.compile(
            r'(?<=(从|自))([^起到至\-—~～]+)(?=(起|到|至|以来|开始|—|－|-|~|～))|'
            r'(?<=(从|自))([^起到至\-—~～]+)')
        self.first_2_span_pattern = re.compile(r'(.+)(?=(——|--|~~|－－|～～))')
        self.first_3_span_pattern = re.compile(r'([^起到至\-—~～]+)(?=(起|到|至|以来|开始|－|—|-|~|～))')
        self.first_4_span_pattern = re.compile(r'(.+)(?=(之后|以后)$)')  # (之以)?后)$
        self.first_5_span_pattern = re.compile(r'(.+)(?=(后)$)')  # (之以)?后)$

        self.second_0_span_pattern = re.compile(r'(?<=(以来|开始|——|--|~~|－－|～～))(.+)')
        self.second_1_span_pattern = re.compile(r'(?<=[起到至\-—~～－])([^起到至\-—~～－]+)(?=([之以]?前|止)$)')
        self.second_2_span_pattern = re.compile(r'(?<=[起到至\-—~～－])([^起到至\-—~～－]+)')
        self.second_3_span_pattern = re.compile(
            r'^((\d{1,2}|[一二两三四五六七八九十百千]+)[几多]?年(半)?(多)?|半年(多)?|几[十百千](多)?年)'
            r'(?=([之以]?前|止)$)')  # 此种匹配容易和 `三年以前` 相互矛盾，因此设置正则

        # for delta span pattern
        self.first_delta_span_pattern = re.compile(r'([^到至\-—~～]+)(?=(——|--|~~|～～|－－|到|至|－|—|-|~|～))')
        self.second_1_delta_span_pattern = re.compile(r'(?<=(——|--|~~|～～|－－))([^到至\-—~～]+)')
        self.second_2_delta_span_pattern = re.compile(r'(?<=[到至－—\-~～])([^到至－\-—~～]+)')

        # 公历固定节日
        self.fixed_solar_holiday_dict = {
            # 国内
            '元旦': [1, 1], '妇女节': [3, 8], '女神节': [3, 8], '三八': [3, 8],
            '植树节': [3, 12], '五一': [5, 1], '劳动节': [5, 1], '青年节': [5, 4],
            '六一': [6, 1], '儿童节': [6, 1], '七一': [7, 1], '建党节': [7, 1],
            '八一': [8, 1], '建军节': [8, 1], '教师节': [9, 10], '国庆节': [10, 1],
            '十一': [10, 1], '国庆': [10, 1], '清明节': [4, 5],  # 清明节有误, 4~6 日

            # 西方
            '情人节': [2, 14], '愚人节': [4, 1], '万圣节': [10, 31], '圣诞': [12, 25],

            # 特定日
            '地球日': [4, 22], '护士节': [5, 12], '三一五': [3, 15], '消费者权益日': [3, 15],
            '三.一五': [3, 15], '三·一五': [3, 15], '双11': [11, 11], '双十一': [11, 11],
            '双十二': [12, 12], '双12':[12, 12]
        }

        # 农历固定节日
        self.fixed_lunar_holiday_dict = {
            '春节': [1, 1], '大年初一': [1, 1], '大年初二': [1, 2], '大年初三': [1, 3],
            '大年初四': [1, 4], '大年初五': [1, 5], '大年初六': [1, 6], '大年初七': [1, 7],
            '大年初八': [1, 8], '大年初九': [1, 9], '大年初十': [1, 10],
            '元宵': [1, 15], '填仓节': [1, 25], '龙抬头': [2, 2],
            '上巳节': [3, 3], '寒食节': [4, 3],
            '浴佛节': [4, 8], '端午': [5, 5], '端阳': [5, 5], '姑姑节': [6, 6],
            '七夕': [7, 7], '中元': [7, 15], '财神节': [7, 22], '中秋': [8, 15],
            '重阳': [9, 9], '下元节': [10, 15], '寒衣节': [10, 1], '腊八': [12, 8],
            '除夕': [12, 30], '大年三十': [12, 30],
            # 除夕某些年份，12月 30 不存在，就是腊月 29 是除夕。
            # 清明同理，不固定
        }

        # 公历规律节日
        self.regular_solar_holiday_dict = {
            '母亲节': {'month': 5, 'week': 2, 'day': 7},  # 5 月第二个星期日
            '父亲节': {'month': 6, 'week': 3, 'day': 7},  # 6 月第三个星期日
            '感恩节': {'month': 11, 'week': 4, 'day': 4},  # 11 月第四个星期四
        }

        # 周期性日期
        self.period_time_pattern = re.compile(
            r'每((间)?隔)?([一二两三四五六七八九十0-9]+|半)?'
            r'(年|(个)?季度|(个)?月|(个)?(星期|礼拜)|(个)?周|((个)?工作)?日|天|(个)?(小时|钟头)|分(钟)?|秒(钟)?)')

        # 由于 time_span 格式造成的时间单位缺失的检测
        # 如：`去年9~12月`、 `2016年8——10月`，但 `2017年9月10日11:00至2018年` 除外，因最后为时、分
        self.time_span_point_compensation = re.compile(
            absence(BLUR_HOUR_STRING) +
            r'(?!:)[\d一二三四五六七八九十零]{1,2}[月日号点时]?(到|至|——|－－|--|~~|～～|—|－|-|~|～)'
            r'([\d一二三四五六七八九十零]{1,2}[月日号点时]|[\d一二三四五六七八九十零]{2,4}年)')

        # 特殊时间表述
        self.special_time_delta_pattern = re.compile(
            r'(' + SINGLE_NUM_STRING + r'天' + SINGLE_NUM_STRING + '[夜晚]|' + \
            SINGLE_NUM_STRING + '+[个载度]春秋|一年四季|大半(天|年|(个)?(月|小时|钟头)))')
        self.special_time_span_pattern = re.compile(
            r'(今明两[天年]|全[天月年])')

    def _compensate_string(self, time_string, first_time_string, second_time_string):
        """ 补全时间字符串缺失部分 """
        time_compensation = self.time_span_point_compensation.search(time_string)
        if time_compensation:
            time_compensation = time_compensation.group()

            # compensate the first
            if '年' in time_compensation:
                if first_time_string[-1] not in '点时日号月年':  # 若第一个时间以 日月 等结尾，而第二个时间以年开头，则不补全
                    first_time_string = ''.join([first_time_string, '年'])
            elif '月' in time_compensation:
                if first_time_string[-1] not in '点时日号月':
                    first_time_string = ''.join([first_time_string, '月'])
            elif '日' in time_compensation or '号' in time_compensation:
                if first_time_string[-1] not in '点时日号':
                    first_time_string = ''.join([first_time_string, '日'])
            elif '点' in time_compensation or '时' in time_compensation:
                if first_time_string[-1] not in '点时':
                    first_time_string = ''.join([first_time_string, '时'])

            # compensate the second
            hour_limitation = self.hour_patterns[1].search(time_string)
            if hour_limitation:
                second_time_string = ''.join([hour_limitation.group(), second_time_string])

            return first_time_string, second_time_string
        else:
            return first_time_string, second_time_string

    def __call__(self, time_string, time_base=time.time(), time_type=None,
                 ret_type='str', strict=False, virtual_time=False, ret_future=False,
                 period_results_num=None, lunar_date=True):
        """ 解析时间字符串。 """
        if self.future_time is None:
            self._preprocess()

        self.string_strict = strict  # 用于控制字符串中的 杂串不被包含
        self.virtual_time = virtual_time  # 指示虚拟时间，若有些模糊字符串可解析为虚拟时间，则按虚拟时间解析，如“前两天”
        self.ret_future = ret_future
        self.lunar_date = lunar_date

        # 清洗字符串
        time_string = TimeParser._cleansing(time_string)

        # 解析 time_base 为 handler
        self.time_base_handler = TimeParser._convert_time_base2handler(time_base)

        # 按 time_period 解析，未检测到后，按 time_delta 解析
        period_res, blur_time = self.parse_time_period(time_string, period_results_num=period_results_num)
        if period_res:
            return {'type': 'time_period',
                    'definition': blur_time,
                    'time': period_res}

        # 解析 time_delta，未检测到后，按 time_point 与 time_span 解析
        delta_res = self.time_delta.parse_time_delta_span(time_string, time_type=time_type)
        if delta_res is not None:
            return delta_res

        # time_base_handler 中必须有 year，否则依然无法确定具体时间
        legal = TimeUtility.check_handler(self.time_base_handler) and (self.time_base_handler[0] != -1)
        if not legal:
            raise ValueError('The given time base `{}` is illegal.'.format(time_base))

        # time_span & time_point parser
        first_full_time_handler, second_full_time_handler, time_type, blur_time = \
            self.parse_time_span_point(time_string)

        first_standard_time_string, second_standard_time_string = self.time_handler2standard_time(
            first_full_time_handler, second_full_time_handler)

        return {'type': time_type,
                'definition': blur_time,
                'time': [first_standard_time_string, second_standard_time_string]}

    def _check_limit_time_base(self, first_time_string, second_time_string,
                               first_full_time_handler):
        """ 检测 time_span_point 里的时间字符串中 符合 limit 类型字符串，
        此时，time_base 不可以随着 first_time_string 改变
        以及是否改变 time_base 以及如何调整 time_base。
        Args:
            first_time_string: 第一个时间字符串
            second_time_string: 第二个时间字符串
            first_full_time_handler: 根据第一个时间字符串得出的 time_base

        Returns:
            适合第二个字符串的 time_base，依据第二个字符串进行判断
        """
        limit_ymd_time_patterns = [
            # 时间点型
            [self.limit_year_lunar_season_pattern, self.normalize_limit_year_lunar_season],
            [self.limit_year_month_blur_day_pattern, self.normalize_limit_year_month_blur_day],
            [self.limit_year_solar_season_pattern, self.normalize_limit_year_solar_season],
            [self.limit_solar_season_pattern, self.normalize_limit_solar_season],
            [self.limit_year_week_pattern, self.normalize_limit_year_week],
            [self.limit_week_pattern, self.normalize_limit_week],
            [self.limit_year_blur_month_pattern, self.normalize_limit_year_blur_month],
            [self.limit_month_blur_day_pattern, self.normalize_limit_month_blur_day],
            [self.limit_month_day_pattern, self.normalize_limit_month_day],
            [self.limit_month_pattern, self.normalize_limit_month],
            [self.limit_year_span_month_pattern, self.normalize_limit_year_span_month],

            # week 较为特殊
            [self.standard_week_day_pattern, self.normalize_standard_week_day],

            # festival group
            [self.limit_year_fixed_solar_festival_pattern, self.normalize_limit_year_fixed_solar_festival],
            [self.limit_year_fixed_lunar_festival_pattern, self.normalize_limit_year_fixed_lunar_festival],
            [self.limit_year_regular_solar_festival_pattern, self.normalize_limit_year_regular_solar_festival],

            [self.lunar_limit_year_month_day_pattern, self.normalize_lunar_limit_year_month_day],
            [self.limit_year_month_day_pattern, self.normalize_limit_year_month_day],
            [self.limit_day_pattern, self.normalize_limit_day],
            # []
        ]

        first_time_string_limit = False
        second_time_string_limit = False

        # 检查时间字符串是否为 limit 类型
        for ymd_limit_pattern in limit_ymd_time_patterns:
            first_ymd_limit_string = TimeParser.parse_pattern(first_time_string, ymd_limit_pattern[0])
            second_ymd_limit_string = TimeParser.parse_pattern(second_time_string, ymd_limit_pattern[0])
            if first_ymd_limit_string != '':
                first_time_string_limit = True
            if second_ymd_limit_string != '':
                second_time_string_limit = True
            if first_time_string_limit and second_time_string_limit:
                break

        # 若第二个字符串为 limit 类型，如 “去年9月”，则 time_base 不变
        # text = '2014年11月到下个月9号'  # FT -> BASE
        # text = '去年11月到今年3月'  # TF -> FIRST
        # text = '前天9点到明天白天'  # TT -> BASE
        if second_time_string_limit:
            return self.time_base_handler
        else:
            return first_full_time_handler

    def _adjust_underlying_future_time(
            self, time_string, first_full_time_handler, second_full_time_handler):
        """

        Args:
            time_string: 时间字符串，进行未来时间扩展
            first_full_time_handler: 假设不进行未来时间扩展，正常解析的时间起点
            second_full_time_handler: 假设不进行未来时间扩展，正常解析的时间终点

        Returns:
            扩展后的未来时间
        """

        # 检查哪些时间字符串可以被扩展为 未来字符串，并将其调节
        ymd_time_patterns = [
            # 时间点型
            self.year_24st_pattern,
            self.year_lunar_season_pattern,
            self.year_month_blur_day_pattern,
            self.year_solar_season_pattern,
            self.standard_week_day_pattern,
            self.blur_week_pattern,
            self.year_blur_month_pattern,
            self.century_year_pattern,
            self.year_span_month_pattern,

            self.year_order_delta_point_pattern,
            self.day_order_delta_point_pattern,

            # festival group
            self.year_fixed_solar_festival_pattern,
            self.year_fixed_lunar_festival_pattern,
            self.year_regular_solar_festival_pattern,

            self.lunar_limit_year_month_day_pattern,
            self.blur_year_pattern,
            self.lunar_year_month_day_pattern,
            self.year_month_day_pattern,
            self.standard_year_pattern,
        ]
        hms_time_patterns = [
            # TIME_POINT 型
            self.hour_minute_second_pattern,
            self.num_hour_minute_second_pattern,
            self.hour_limit_minute_pattern,
            self.blur_hour_pattern,
        ]

        # 命中以上正则，则考虑扩展为未来时间
        time_string_flag = False
        for ymd_limit_pattern in ymd_time_patterns + hms_time_patterns:
            ymd_string = TimeParser.parse_pattern(time_string, ymd_limit_pattern)
            if ymd_string != '':
                time_string_flag = True
                break

        if time_string_flag:
            matched_res = self.future_time_unit_pattern.search(time_string)
            if matched_res:
                matched_unit = matched_res.group()
                if matched_unit in ['月', '节']:
                    time_string = '明年' + time_string
                elif matched_unit in ['日', '号']:
                    time_string = '下个月' + time_string
                elif matched_unit in ['周', '星期', '礼拜']:
                    time_string = '下' + time_string

                elif matched_unit in ['时', '点']:
                    # 此时需要判断 time_base 里的时，和字符串中的时，哪个发生在前，哪个在后。
                    # 如果 time_base 发生在前，如 [2023, 1, 6, 16, 30, 0], 而时间字符串为 “下午6点”
                    # 则此时不改变字符串，直接返回即可。
                    if first_full_time_handler[3] != -1 and self.time_base_handler[3] != -1:  # 小时时间均存在
                        if first_full_time_handler[3] > self.time_base_handler[3]:  # 在 小时 字段符合不扩增至第二天的条件
                            pass
                        elif first_full_time_handler[3] < self.time_base_handler[3]:  # 符合扩增条件
                            time_string = '明天' + time_string
                        else:  # 还需比较 分钟

                            if first_full_time_handler[4] != -1 and self.time_base_handler[4] != -1:  # 分钟时间均存在
                                if first_full_time_handler[4] > self.time_base_handler[4]:  # 在分钟字段不扩增
                                    pass
                                elif first_full_time_handler[4] < self.time_base_handler[4]:  # 符合扩增条件
                                    time_string = '明天' + time_string
                                else:
                                    # 暂时不考虑 秒钟 ，此时直接将时间扩增至第二天
                                    time_string = '明天' + time_string
                            else:
                                time_string = '明天' + time_string
                    else:
                        # 时间基未指明，因此直接跨到第二天
                        time_string = '明天' + time_string
                else:
                    pass

        return time_string

    def _compensate_num_month_num(self, time_string):
        """ 一种特定的日期类型，“1月1”，没指明 “日”。因此需要进行补全，然后再进行处理。

        Args:
            time_string:

        Returns:

        """
        matched_res = self.num_month_num_pattern.search(time_string)
        if matched_res is not None:
            return time_string + '日'
        else:
            return time_string

    def parse_time_span_point(self, time_string):
        # 按照 “从 …… 至 ……” 进行解析
        first_time_string, second_time_string = self.parse_span_2_2_point(time_string)

        if first_time_string is not None or second_time_string is not None:
            time_type = 'time_span'
            old_time_base_handler = self.time_base_handler
            try:
                if first_time_string is not None and second_time_string is None:
                    first_time_string = self._compensate_num_month_num(first_time_string)

                    first_full_time_handler, _, _, blur_time = self.parse_time_point(
                        first_time_string, self.time_base_handler)

                    # 当 time_base 大于 first_full_time_handler，直接赋值，
                    # 否则，定义 second_full_time_handler 为未定义无穷大值
                    compare_res = TimeUtility._compare_handler(first_full_time_handler, self.time_base_handler)
                    if compare_res >= 0:
                        second_full_time_handler = self.future_time
                    elif compare_res < 0:
                        # 默认此时 second handler 为 `至今`
                        second_full_time_handler = self.time_base_handler
                elif first_time_string is not None and second_time_string is not None:

                    first_time_string = self._compensate_num_month_num(first_time_string)
                    second_time_string = self._compensate_num_month_num(second_time_string)
                    first_time_string, second_time_string = self._compensate_string(
                        time_string, first_time_string, second_time_string)

                    first_full_time_handler, _, _, blur_time = self.parse_time_point(
                        first_time_string, self.time_base_handler)
                    if second_time_string in ['今', '至今', '现在', '今天']:
                        # 默认此时 time_base 大于 first_full_time_handler
                        second_full_time_handler = self.time_base_handler
                    else:
                        # 此时，对于 `昨天11点到明天晚上` 此类 limit 类型字符串会有影响，须调整 time_base
                        self.time_base_handler = self._check_limit_time_base(
                            first_time_string, second_time_string, first_full_time_handler)

                        _, second_full_time_handler, _, blur_time = self.parse_time_point(
                            second_time_string, self.time_base_handler)

                        # 对于 time_span 且 second_full_time_handler 的 时分秒，分别为 [..., 10, -1, -1]，
                        # 须将其补全为 [..., 10, 0, 0]。
                        if second_full_time_handler[3] > -1 and second_full_time_handler[4:] == [-1, -1]:
                            if time_string[-1] in '点时':  # 即必须满足正则 [数字]时 pattern
                                second_full_time_handler[4:] = [0, 0]

                elif first_time_string is None and second_time_string is not None:
                    second_time_string = self._compensate_num_month_num(second_time_string)

                    _, second_full_time_handler, _, blur_time = self.parse_time_point(
                        second_time_string, self.time_base_handler)

                    # 当 time_base 大于 first_full_time_handler，直接赋值，
                    # 否则，定义 second_full_time_handler 为未定义无穷大值
                    compare_res = TimeUtility._compare_handler(
                        self.time_base_handler, second_full_time_handler)
                    if compare_res >= 0:
                        first_full_time_handler = self.past_time
                    elif compare_res < 0:
                        # 默认此时 second handler 为 `从此刻开始`
                        first_full_time_handler = self.time_base_handler
                else:
                    raise KeyError()

            except Exception:

                # 当按 time_span 处理错误后，则考虑问题出在对 time_string 的切分上，仍按 time_point 解析
                self.time_base_handler = old_time_base_handler
                first_full_time_handler, second_full_time_handler, time_type, \
                    blur_time = self.parse_time_point(
                        time_string, self.time_base_handler)
        else:
            # 非 time span，按 time_point 解析
            time_string = self._compensate_num_month_num(time_string)

            first_full_time_handler, second_full_time_handler, time_type, \
                blur_time = self.parse_time_point(
                    time_string, self.time_base_handler)

            # 检查 handler，确定是否按 ret_future 未来时间解析
            if self.ret_future:

                future_time_string = self._adjust_underlying_future_time(
                    time_string, first_full_time_handler, second_full_time_handler)
                first_full_time_handler, second_full_time_handler, time_type, blur_time = self.parse_time_point(
                    future_time_string, self.time_base_handler)

        return first_full_time_handler, second_full_time_handler, time_type, blur_time

    def _seg_or_not_first(self, time_string):
        """ 针对待分解字符串，判定哪种情况须分解，哪种不应当分解

        该种判断方法，将不希望被分割的 `-`替换成异常字符 `䶵`，然后使用分割方法进行分割
        感觉存在潜在的问题。
        """
        # time_span 的分割词也分层级，汉字`起至到` 的优先级高于 `-~`等，后者可用于`年月日`的分割
        if time_string is None:
            return None

        # 处理特殊的不可分割为两 time_point 的情况
        # 1、2018-04-02 这样的形式，不拆分，直接返回双 None
        #    例如：2018-04-02，2007.12-31，1999.5-20 12:20，
        #         2008.2.1-2019.5.9，
        #    但不包括 1989.02-1997.10

        # 强制 seg pattern，指字符串中仅有的 `-` 字符要用于表达两个 时间点(time_point) 的分割，
        # 因此，该字符串的 `-` 要用于强制分割，可直接返回字符串
        seg_patterns = [self.time_span_seg_standard_year_month_to_year_month]
        for pattern in seg_patterns:
            matched_string = TimeParser.parse_pattern(time_string, pattern)
            if matched_string is not None and matched_string != '':
                # 匹配到后，无须进行替换，即须拆分
                return time_string

        # '''
        # 强制不 seg pattern，即字符串中的所有 `-` 都不表达两个 时间点(time_point) 的分割，
        # 因此，须考察 字符串中有几个这样的时间点，如果是
        no_seg_patterns = [self.time_span_no_seg_standard_year_month_day]
        for pattern in no_seg_patterns:
            # matched_string = TimeParser.parse_pattern(time_string, pattern)
            searched_res = pattern.search(time_string)
            if searched_res:
                # all_res = [item for item in pattern.finditer(time_string)]
                # start_idx = searched_res.span()[0]
                # end_idx = searched_res.span()[1]
                # time_string = time_string[start_idx: end_idx].replace('-', '䶵')

                # 匹配到后，须进行替换
                time_string = time_string.replace('-', '䶵')
                break
        # '''
        if '起' in time_string or '至' in time_string or '到' in time_string:
            time_string = time_string.replace('-', '䶵')
        return time_string

    def _seg_or_not_second(self, time_string):
        """ 将被替换的 '䶵' 字符还原成 '-' """
        if time_string is None:
            return None

        time_string = time_string.replace('䶵', '-').strip()
        return time_string

    def _time_point(self):
        return TimePoint(), TimePoint()

    def parse_span_2_2_point(self, time_string):
        """检测时间字符串，并将其分解为两个 time_point """
        # 处理层级分割的 临时做法，后续还需优化
        time_string = self._seg_or_not_first(time_string)

        # 找第一个字符串
        if self.first_1_span_pattern.search(time_string):
            first_res = self.first_1_span_pattern.search(time_string)
        elif self.first_2_span_pattern.search(time_string):
            first_res = self.first_2_span_pattern.search(time_string)
        elif self.first_3_span_pattern.search(time_string):
            if time_string[-2:] in ['夏至', '冬至']:
                first_res = None
            else:
                first_res = self.first_3_span_pattern.search(time_string)
        elif self.first_4_span_pattern.search(time_string) and '前后' not in time_string:
            first_res = self.first_4_span_pattern.search(time_string)
        elif self.first_5_span_pattern.search(time_string) and '前后' not in time_string:
            first_res = self.first_5_span_pattern.search(time_string)
        else:
            first_res = None

        first_string = None if first_res is None else first_res.group()

        # 找第二个字符串
        second_string = None
        if self.second_0_span_pattern.search(time_string):
            second_res = self.second_0_span_pattern.search(time_string)
        elif self.second_1_span_pattern.search(time_string):
            second_res = self.second_1_span_pattern.search(time_string)
        elif self.second_2_span_pattern.search(time_string):
            second_res = self.second_2_span_pattern.search(time_string)
        elif self.second_3_span_pattern.search(time_string) is None:
            if '之前' in time_string[-2:] or '以前' in time_string[-2:]:
                second_string = time_string[:-2]
            elif '前' in time_string[-1:]:
                second_string = time_string[:-1]
            else:
                second_res = None
        else:
            second_res = None

        if second_string is None:
            second_string = None if second_res is None else second_res.group()

        first_string = self._seg_or_not_second(first_string)
        second_string = self._seg_or_not_second(second_string)

        return first_string, second_string

    def parse_time_period(self, time_string, period_results_num=None):
        """ 判断字符串是否为 time_period，若是则返回结果，若不是则返回 None，跳转到其它类型解析。 """

        has_weekday = False
        if '工作日' in time_string:
            has_weekday = True

        searched_res = self.period_time_pattern.search(time_string)
        if searched_res:
            period_time = searched_res.group()
            period_delta = self.normalize_time_period(period_time)

            if len(time_string) > len(period_time):
                # 一般来讲，在字符串无异常字符的情况下，此时存在 time_point，如`每年9月` 中的 9月
                # 但是某些时间周期难以表示，如 `每周周一` 中的 周一。此时用 time_point 中的绝对时间进行表示，并附以时间文本
                time_point_string = time_string.replace(period_time, '')
                # 补充 time_point_string
                if (period_time.endswith('礼拜') or period_time.endswith('周') or period_time.endswith('星期'))\
                        and (not time_point_string.startswith('周')):
                    time_point_string = '周' + time_point_string

                try:
                    if period_results_num is None:

                        if has_weekday:
                            # `每周工作日9点` 中，`工作日9点`要进入 time_point_string，需要将 `工作日` 剔除
                            time_point_string = time_point_string.split('工作日')[-1].replace('的', '')

                            for i in range(7):
                                first_full_time_handler, second_full_time_handler, _, blur_time = self.parse_time_span_point(
                                    time_point_string)
                                first_full_time_datetime = TimeParser._convert_handler2datetime(first_full_time_handler)
                                is_weekday = TimeParser._check_weekday(first_full_time_datetime)
                                if is_weekday:
                                    break
                                else:
                                    cur_time_base_datetime = TimeParser._convert_handler2datetime(
                                        self.time_base_handler)

                                    cur_time_base_datetime += datetime.timedelta(days=1)
                                    self.time_base_handler = TimeParser._convert_time_base2handler(
                                        cur_time_base_datetime)

                            first_std_time_string, second_std_time_string = self.time_handler2standard_time(
                                first_full_time_handler, second_full_time_handler)
                            results = [first_std_time_string, second_std_time_string]

                        else:
                            first_full_time_handler, second_full_time_handler, _, blur_time = self.parse_time_span_point(
                                time_point_string)
                            first_std_time_string, second_std_time_string = self.time_handler2standard_time(
                                first_full_time_handler, second_full_time_handler)

                            results = [first_std_time_string, second_std_time_string]

                    elif type(period_results_num) is int and period_results_num > 0:

                        if has_weekday:
                            time_point_string = time_point_string.split('工作日')[-1]
                        results = []

                        while len(results) < period_results_num:
                            first_full_time_handler, second_full_time_handler, _, blur_time = self.parse_time_span_point(
                                time_point_string)
                            first_std_time_string, second_std_time_string = self.time_handler2standard_time(
                                first_full_time_handler, second_full_time_handler)

                            cur_time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

                            if has_weekday:
                                is_weekday = TimeParser._check_weekday(cur_time_base_datetime)
                                if is_weekday and ([first_std_time_string, second_std_time_string] not in results):
                                    results.append([first_std_time_string, second_std_time_string])
                            else:
                                if [first_std_time_string, second_std_time_string] not in results:
                                    results.append([first_std_time_string, second_std_time_string])

                            if 'year' in period_delta:
                                cur_time_base_datetime += datetime.timedelta(days=365)
                            if 'month' in period_delta:
                                cur_time_base_datetime += datetime.timedelta(days=30.417)
                            if 'day' in period_delta:
                                if not has_weekday:  # 若日期非按每一日结算，则须按 7天为单位跳过，否则会报错。
                                    cur_time_base_datetime += datetime.timedelta(days=7)
                                else:
                                    cur_time_base_datetime += datetime.timedelta(days=1)
                            if 'hour' in period_delta:
                                cur_time_base_datetime += datetime.timedelta(hours=1)
                            if 'minute' in period_delta:
                                cur_time_base_datetime += datetime.timedelta(minutes=1)
                            if 'second' in period_delta:
                                cur_time_base_datetime += datetime.timedelta(seconds=1)

                            self.time_base_handler = TimeParser._convert_time_base2handler(cur_time_base_datetime)
                    else:
                        raise ValueError('the given results_num `{}` is illegal.'.format(period_results_num))

                except Exception as e:
                    # 即无法解析的字符串，按照原字符串进行返回
                    logging.error(traceback.format_exc())

                    if self.string_strict:
                        # 但根据某些情况，此处加强字符串审核，直接报错。如 “每年6.” 等。其中 “6” 并非有意义时间字符串。
                        raise ValueError('the given time string `{}` is illegal.'.format(time_string))

                    first_std_time_string, second_std_time_string = None, None
                    results = [first_std_time_string, second_std_time_string]
                    blur_time = 'blur'

                period_point = {'time': results,
                                'string': time_point_string}
            else:
                period_point = None
                blur_time = 'accurate'

            return {'delta': period_delta, 'point': period_point}, blur_time

        return None, None

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

        return TimeUtility._cut_zero_key(time_delta.__dict__)

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
            time_delta_num, _time_definition = self._normalize_delta_unit(time_string, pattern, unit=unit)
            time_delta.__setattr__(unit, time_delta.__getattribute__(unit) + time_delta_num * multi)
            if time_delta_num > 0:
                time_definition = _time_definition

        return time_delta, 'time_delta', time_definition

    def _normalize_delta_unit(self, time_string, pattern, unit=None):
        """ 将 time_delta 归一化 """
        # 处理字符串的问题
        if unit is None:
            time_string = time_string.replace('俩', '两个')
            time_string = time_string.replace('仨', '三个')
        else:
            if unit in ["second", "minute", "day", "year"]:  # 三秒，三天，三年
                time_string = time_string.replace('俩', '两')
                time_string = time_string.replace('仨', '三')
            elif unit in ["hour", "month"]:  # 三个小时，三个月
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
                time_delta = self._char_num2num(delta_num_string)
            if '半' in time_string:
                if time_delta > 0:
                    time_delta += 0.5
                else:
                    time_delta = 0.5
                time_definition = 'blur'

            if '多' in time_string or '余' in time_string:
                time_definition = 'blur'

            if '近' in time_string and '最近' not in time_string:
                time_definition = 'blur'

        return time_delta, time_definition

    def _check_blur(self, time_string, time_definition):
        # 若字符串中存在 `左右` 或 `许` 等，说明是 blur，反之返回 None 表示不确定性
        if '左右' in time_string[-2:]:
            return 'blur'
        if '许' in time_string[-1]:
            return 'blur'
        if '前后' in time_string[-2:]:
            return 'blur'

        return time_definition

    @staticmethod
    def _check_weekday(time_base_datetime):
        if time_base_datetime.weekday() <= 4:  # 周一至周五，0~4，周六日 5、6
            return True
        else:
            return False

    def parse_time_point(self, time_string, time_base_handler):
        """解析时间点字符串，
        # 此处，时间点字符串不一定为 time point 类型，仅仅依据显式 `从……到……` 的正则匹配得到的字符串
        """
        # time_point pattern & norm_func
        if self.ymd_pattern_norm_funcs is None:
            self.ymd_pattern_norm_funcs = [
                # 枚举日期型
                [self.enum_day_pattern, self.normalize_enum_day_pattern],

                # 超模糊型
                [self.super_blur_two_ymd_pattern, self.normalize_super_blur_two_ymd],

                # 时间点型
                [self.standard_year_month_day_pattern, self.normalize_standard_year_month_day],
                [self.standard_2_year_month_day_pattern, self.normalize_standard_2_year_month_day],
                [self.year_24st_pattern, self.normalize_year_24st],
                [self.limit_year_lunar_season_pattern, self.normalize_limit_year_lunar_season],
                [self.year_lunar_season_pattern, self.normalize_year_lunar_season],
                [self.limit_year_month_blur_day_pattern, self.normalize_limit_year_month_blur_day],
                [self.year_month_blur_day_pattern, self.normalize_year_month_blur_day],
                [self.limit_year_solar_season_pattern, self.normalize_limit_year_solar_season],
                [self.limit_solar_season_pattern, self.normalize_limit_solar_season],
                [self.year_solar_season_pattern, self.normalize_year_solar_season],
                [self.limit_month_week_pattern, self.normalize_limit_month_week],
                [self.month_week_pattern, self.normalize_month_week],
                [self.year_month_week_pattern, self.normalize_year_month_week],
                [self.limit_year_month_week_pattern, self.normalize_limit_year_month_week],
                [self.limit_year_week_pattern, self.normalize_limit_year_week],
                [self.year_week_pattern, self.normalize_year_week],
                [self.limit_week_pattern, self.normalize_limit_week],
                [self.standard_week_day_pattern, self.normalize_standard_week_day],
                [self.blur_week_pattern, self.normalize_blur_week],
                [self.limit_year_blur_month_pattern, self.normalize_limit_year_blur_month],
                [self.limit_month_blur_day_pattern, self.normalize_limit_month_blur_day],
                [self.limit_month_day_pattern, self.normalize_limit_month_day],
                [self.limit_month_pattern, self.normalize_limit_month],
                [self.year_blur_month_pattern, self.normalize_year_blur_month],
                [self.century_year_pattern, self.normalize_century_year],
                [self.limit_year_span_month_pattern, self.normalize_limit_year_span_month],
                [self.year_span_month_pattern, self.normalize_year_span_month],

                [self.year_day_order_delta_point_pattern, self.normalize_year_day_order_delta_point],
                [self.year_order_delta_point_pattern, self.normalize_year_order_delta_point],
                [self.day_order_delta_point_pattern, self.normalize_day_order_delta_point],

                # time delta 2 span group
                [self.weilai_delta2span_pattern, self.normalize_weilai_delta2span],
                [self.guoqu_delta2span_pattern, self.normalize_guoqu_delta2span],
                [self.guo_delta2span_pattern, self.normalize_guo_delta2span],

                # time delta 2 point group
                [self.workday_delta_point_pattern, self.normalize_workday_delta_point],
                [self.day_delta_point_pattern, self.normalize_day_delta_point],
                [self.week_delta_point_pattern, self.normalize_week_delta_point],
                [self.month_delta_point_pattern, self.normalize_month_delta_point],
                [self.solar_season_delta_point_pattern, self.normalize_solar_season_delta_point],
                [self.year_delta_point_pattern, self.normalize_year_delta_point],  # 与 blur year 有重复

                # festival group
                [self.limit_year_fixed_solar_festival_pattern, self.normalize_limit_year_fixed_solar_festival],
                # 调整了 self.year_fixed_solar_festival_pattern 位置，避免出现 “今天十一点半” 字符串中 “十一” 被识别为节日
                # 该正则与 self.limit_day_pattern 相矛盾
                # [self.year_fixed_solar_festival_pattern, self.normalize_year_fixed_solar_festival],
                [self.limit_year_fixed_lunar_festival_pattern, self.normalize_limit_year_fixed_lunar_festival],
                [self.year_fixed_lunar_festival_pattern, self.normalize_year_fixed_lunar_festival],
                [self.limit_year_regular_solar_festival_pattern, self.normalize_limit_year_regular_solar_festival],
                [self.year_regular_solar_festival_pattern, self.normalize_year_regular_solar_festival],

                [self.lunar_limit_year_month_day_pattern, self.normalize_lunar_limit_year_month_day],
                [self.limit_year_month_day_pattern, self.normalize_limit_year_month_day],
                [self.blur_year_pattern, self.normalize_blur_year],
                [self.limit_day_pattern, self.normalize_limit_day],
                [self.year_fixed_solar_festival_pattern, self.normalize_year_fixed_solar_festival],
                [self.lunar_year_month_day_pattern, self.normalize_lunar_year_month_day],
                [self.year_month_day_pattern, self.normalize_year_month_day],
                [self.standard_year_pattern, self.normalize_standard_year],

                # special patterns
                [self.special_time_span_pattern, self.normalize_special_time_span],
            ]

        if self.hms_pattern_norm_funcs is None:
            self.hms_pattern_norm_funcs = [
                # 超模糊型
                [self.super_blur_two_hms_pattern, self.normalize_super_blur_two_hms],

                # TIME_DELTA 转换型
                [self.second_delta_point_pattern, self.normalize_second_delta_point],
                [self.minute_delta_point_pattern, self.normalize_minute_delta_point],
                [self.quarter_delta_point_pattern, self.normalize_quarter_delta_point],
                [self.hour_delta_point_pattern, self.normalize_hour_delta_point],

                # TIME_POINT 模糊型
                [self.consecutive_blur_hour_pattern, self.normalize_consecutive_blur_hour_pattern],

                # TIME_POINT 型
                [self.hour_minute_second_pattern, self.normalize_hour_minute_second],
                [self.num_hour_minute_second_pattern, self.normalize_num_hour_minute_second],
                [self.hour_limit_minute_pattern, self.normalize_hour_limit_minute],
                [self.blur_hour_pattern, self.normalize_blur_hour],

            ]

        # 减少循环和遍历
        ymd_string_list = []
        ymd_func_list = []
        ymd_empty_string_flag = False
        for ymd_pattern, ymd_func in self.ymd_pattern_norm_funcs:
            ymd_string = TimeParser.parse_pattern(time_string, ymd_pattern)

            if ymd_string != '':
                ymd_string_list.append(ymd_string)
                ymd_func_list.append([ymd_pattern, ymd_func])
            else:
                if not ymd_empty_string_flag:
                    ymd_string_list.append(ymd_string)
                    ymd_func_list.append([ymd_pattern, ymd_func])

                    ymd_empty_string_flag = True

        hms_string_list = []
        hms_func_list = []
        hms_empty_string_flag = False
        for hms_pattern, hms_func in self.hms_pattern_norm_funcs:
            hms_string = TimeParser.parse_pattern(time_string, hms_pattern)

            if hms_string != '':
                hms_string_list.append(hms_string)
                hms_func_list.append([hms_pattern, hms_func])
            else:
                if not hms_empty_string_flag:
                    hms_string_list.append(hms_string)
                    hms_func_list.append([hms_pattern, hms_func])

                    hms_empty_string_flag = True

        cur_ymd_func, cur_hms_func = None, None
        cur_ymd_string, cur_hms_string = '', ''
        break_flag = False
        # for ymd_pattern, ymd_func in self.ymd_pattern_norm_funcs:
        #     ymd_string = TimeParser.parse_pattern(time_string, ymd_pattern)
        #     for (hms_pattern, hms_func) in self.hms_pattern_norm_funcs:
        #         hms_string = TimeParser.parse_pattern(time_string, hms_pattern)
        for _ymd_string, (ymd_pattern, ymd_func) in zip(ymd_string_list, ymd_func_list):
            ymd_string = _ymd_string
            for _hmd_string, (hms_pattern, hms_func) in zip(hms_string_list, hms_func_list):
                hms_string = _hmd_string

                if len(ymd_string) + len(hms_string) > len(cur_ymd_string) + len(cur_hms_string):
                    cur_hms_func = hms_func
                    cur_ymd_func = ymd_func
                    cur_hms_string = hms_string
                    cur_ymd_string = ymd_string

                if ''.join([cur_ymd_string, cur_hms_string]) == time_string:
                    break_flag = True
                    break
                else:
                    continue

            if break_flag:
                break

        if len(''.join([cur_ymd_string, cur_hms_string])) < len(time_string.replace(' ', '')):
            if self.chinese_char_pattern.search(time_string):
                # 若搜索到中文，则 `-` 等符号可用作 time_span 的分隔符，可以不用处理判断字符串未匹配的异常情况
                if self.string_strict:
                    raise ValueError('## exception string `{}`.'.format(time_string))
                else:
                    pass
            else:
                # 若未搜索到中文，则 `-` 等符号很可能只是间隔符，如`2018-08-09`而非 span 分隔符，此时要求字符串干净
                raise ValueError('## exception string `{}`.'.format(time_string))

        day_bias = [0, '弱']  # 用于调整根据 时分秒判断的 日
        # 年月日、时分秒相互对应完整
        if cur_ymd_string != '' and cur_hms_string == '':
            first_time_handler, second_time_handler, time_type, blur_time = \
                cur_ymd_func(cur_ymd_string)

        elif cur_ymd_string != '' and cur_hms_string != '':
            # 1、若年月日 字符串存在但是 两 handler 不相等，说明 时分秒 字符串无法确定是哪一天，报错。
            # 2、若年月日 字符串存在但是 handler 中 day 不确定，说明 时分秒 字符串无法确定是哪一天，报错。
            ymd_first_time_handler, ymd_second_time_handler, ymd_time_type, ymd_blur_time = \
                cur_ymd_func(cur_ymd_string)

            if (ymd_first_time_handler != ymd_second_time_handler)\
                    or ymd_first_time_handler[2] == -1:
                raise ValueError('the string `{}` is illegal, because the hour-min-sec string'
                                 'can NOT be designated to a specific day.'.format(time_string))

            hms_first_time_handler, hms_second_time_handler, hms_time_type, hms_blur_time, day_bias = \
                cur_hms_func(cur_hms_string)

            first_time_handler = [max(i, j) for (i, j) in zip(ymd_first_time_handler, hms_first_time_handler)]
            second_time_handler = [max(i, j) for (i, j) in zip(ymd_first_time_handler, hms_second_time_handler)]
            time_type = hms_time_type
            blur_time = hms_blur_time

        elif cur_ymd_string == '' and cur_hms_string != '':
            first_time_handler, second_time_handler, time_type, blur_time, day_bias = \
                cur_hms_func(cur_hms_string)

        else:
            raise ValueError('can not parse the string `{}`.'.format(time_string))

        legal = TimeUtility.check_handler(first_time_handler)
        if not legal:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        first_full_time_handler = TimeUtility.time_completion(
            first_time_handler, time_base_handler)
        second_full_time_handler = TimeUtility.time_completion(
            second_time_handler, time_base_handler)

        # 根据 时分秒信息对 日 做偏移校准
        if day_bias[1] == '强':
            first_full_timebase = TimeParser._convert_handler2datetime(first_full_time_handler)
            first_full_timebase += datetime.timedelta(days=day_bias[0])
            _first_full_time_handler = TimeParser._convert_time_base2handler(first_full_timebase)
            first_full_time_handler = [i if i == -1 else j for i, j in
                                       zip(first_full_time_handler, _first_full_time_handler)]

            second_full_timebase = TimeParser._convert_handler2datetime(second_full_time_handler)
            second_full_timebase += datetime.timedelta(days=day_bias[0])
            _second_full_time_handler = TimeParser._convert_time_base2handler(second_full_timebase)
            second_full_time_handler = [i if i == -1 else j for i, j in
                                        zip(second_full_time_handler, _second_full_time_handler)]

        return first_full_time_handler, second_full_time_handler, time_type, blur_time

    def normalize_special_time_span(self, time_string):
        """ 解决特殊时间解析
        # r'(今明两[天年]|全[天月年])'"""
        first_time_point, second_time_point = self._time_point()

        if '今明' in time_string:
            if '年' in time_string:
                first_time_point.year = self.time_base_handler[0]
                second_time_point.year = self.time_base_handler[0] + 1
            elif '天' in time_string:
                if self.time_base_handler[2] == -1:
                    raise ValueError('the given time_base `{}` is illegal.'.format(time_string))
                first_time_point.day = self.time_base_handler[2]
                second_time_point.day = self.time_base_handler[2] + 1
            else:
                raise ValueError('the given `{}` is illegal.'.format(time_string))

        elif '全' in time_string:
            if '年' in time_string:
                first_time_point.year = self.time_base_handler[0]
                second_time_point.year = self.time_base_handler[0]
            elif '月' in time_string:
                first_time_point.month = self.time_base_handler[1]
                second_time_point.month = self.time_base_handler[1]
            elif '天' in time_string:
                first_time_point.day = self.time_base_handler[2]
                second_time_point.day = self.time_base_handler[2]
            else:
                raise ValueError('the given `{}` is illegal.'.format(time_string))
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'accurate'

    def normalize_standard_year_month_day(self, time_string):
        """ 解析 标准数字 年月日（标准） 时间 """
        # 清洗 time_string 的边缘杂字符串，如`2018-02-09-`，其原字符串可能为
        # `2018-02-09-11:20`
        def pattern_strip(ymd_segs, time_string):
            head = ymd_segs.search(time_string[0])
            tail = ymd_segs.search(time_string[-1])
            while head or tail:
                if head:
                    time_string = time_string[1:]
                if tail:
                    time_string = time_string[:-1]
                head = ymd_segs.search(time_string[0])
                tail = ymd_segs.search(time_string[-1])

            return time_string

        time_string = pattern_strip(self.ymd_segs, time_string)

        colon_num = len(self.ymd_segs.findall(time_string))
        if colon_num == 2:
            year, month, day = self.ymd_segs.split(time_string)

        elif colon_num == 1:
            first_int, second_int = self.ymd_segs.split(time_string)
            if (1600 < int(first_int) < 2200) and int(second_int) <= 12:
                year = int(first_int)
                month = int(second_int)
                day = -1
            elif int(first_int) <= 12 and int(second_int) <= 31:
                year = -1
                month = int(first_int)
                day = int(second_int)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        time_point = TimePoint()

        time_point.year = int(year)
        time_point.month = int(month)
        time_point.day = int(day)

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_standard_2_year_month_day(self, time_string):
        """ 解析 标准数字 年月日（标准） 时间 """
        # 如 `20180209`，8位，应当按照时间来做解析
        time_point = TimePoint()
        time_point.year = int(time_string[:4])
        time_point.month = int(time_string[4:6])
        time_point.day = int(time_string[6:])

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_standard_year(self, time_string):
        """ 解析 标准数字 年（标准） 时间 """
        time_point = TimePoint()

        year = self.standard_year_pattern.search(time_string)
        time_point.year = int(year.group()) if year else self.time_base_handler[0]
        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_span', 'accurate'

    def _normalize_year(self, time_string, time_base_handler):
        year = self.year_patterns[0].search(time_string)
        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self.chinese_year_char_2_arabic_year_char(year_string)

            # 针对 13年8月，08年6月，三三年 这类日期，补全其年份
            if len(year_string) == 2:
                year_string = TimeParser._year_completion(
                    year_string, time_base_handler)

            return int(year_string)
        else:
            return None

    def normalize_super_blur_two_ymd(self, time_string):
        """ 超模糊正则，在中文中，以 前两天、过两年等表达的并非真正的 2年，而是模糊数，
        相当于 前几周，前几天"""
        first_time_point, second_time_point = self._time_point()
        if '前' in time_string:
            if '年' in time_string:
                first_time_point.year = self.time_base_handler[0] - 5
                second_time_point.year = self.time_base_handler[0] - 2
            elif '月' in time_string:
                time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)
                # TODO:
                # 前两个月：
                # 具有三重语义，根据不同语境进行区分，
                # 1、某年的前两个月(time_span)，如“2021年的前两个月” -> 2021年的1月和2月
                # 2、大约两个月前的某个时间点(time_point)，如“他前两个月离职了。” -> 以 2021年12月10日为 base，
                #     即2021年10月的某个时间点
                # 3、从此刻之前的两个月的时间范围(time_span)，如“把前两个月的报表拿给我” ->
                #     以 2021年12月10日为 base，即 2021年的 10月和11月
                # 本工具暂时无法支持多重语义的解析，故根据估计的语义出现频次，按第三种语义进行解析。
                first_time_base_datetime = time_base_datetime - datetime.timedelta(days=30.417 * 2)
                second_time_base_datetime = time_base_datetime - datetime.timedelta(days=30.417 * 1)

                first_time_point.assign(*tuple(first_time_base_datetime.utctimetuple())[:2])
                second_time_point.assign(*tuple(second_time_base_datetime.utctimetuple())[:2])

            elif '天' in time_string:
                time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

                first_time_base_datetime = time_base_datetime - datetime.timedelta(days=7)
                second_time_base_datetime = time_base_datetime - datetime.timedelta(days=2)

                first_time_point.assign(*tuple(first_time_base_datetime.utctimetuple())[:3])
                second_time_point.assign(*tuple(second_time_base_datetime.utctimetuple())[:3])

            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_super_blur_two_hms(self, time_string):
        """ 超模糊正则，在中文中，以 前两分钟、过两个小时等表达的并非真正的 2 分钟，而是模糊数，
        相当于 前几分钟，前几秒"""
        first_time_point, second_time_point = self._time_point()
        if '前' in time_string:
            if '小时' in time_string or '钟头' in time_string:
                assert self.time_base_handler[-3] > -1, 'hour must exist.'

                time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

                first_time_base_datetime = time_base_datetime - datetime.timedelta(hours=6)
                second_time_base_datetime = time_base_datetime - datetime.timedelta(hours=2)

                first_time_point.assign(*tuple(first_time_base_datetime.utctimetuple())[:4])
                second_time_point.assign(*tuple(second_time_base_datetime.utctimetuple())[:4])

            elif '分' in time_string:
                assert self.time_base_handler[-2] > -1, 'minute must exist.'

                time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

                first_time_base_datetime = time_base_datetime - datetime.timedelta(minutes=9)
                second_time_base_datetime = time_base_datetime - datetime.timedelta(minutes=2)

                first_time_point.assign(*tuple(first_time_base_datetime.utctimetuple())[:5])
                second_time_point.assign(*tuple(second_time_base_datetime.utctimetuple())[:5])

            elif '秒' in time_string:
                assert self.time_base_handler[-1] > -1, 'second must exist.'

                time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

                first_time_base_datetime = time_base_datetime - datetime.timedelta(seconds=9)
                second_time_base_datetime = time_base_datetime - datetime.timedelta(seconds=2)

                first_time_point.assign(*tuple(first_time_base_datetime.utctimetuple())[:6])
                second_time_point.assign(*tuple(second_time_base_datetime.utctimetuple())[:6])

            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur', [0, '弱']

    def normalize_enum_day_pattern(self, time_string):
        """ 解析 (年月)?枚举日 时间
        如：`8月14日、15日、16日`。此种类型时间字符串，可以按照 `8月14日`、`15日`、`16日` 进行解析，
        但须指定正确的 time_base 信息。即将 time_base 信息的指定交给调用者。但这会增加处理难度，因此，
        针对这种枚举类型时间，设计单独类型做解析。
        """
        month = self.month_patterns[0].search(time_string)
        day_list = self.day_patterns[0].findall(time_string)

        first_time_point, second_time_point = self._time_point()

        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        if month is not None:
            month_string = month.group(1)
            first_time_point.month = int(self._char_num2num(month_string))
            second_time_point.month = first_time_point.month

        if len(day_list) != 0:
            day_list = [int(item[0]) for item in day_list]
            first_time_point.day = min(day_list)
            second_time_point.day = max(day_list)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_month_day(self, time_string):
        """ 解析 年月日（标准） 时间 """
        month = self.month_patterns[0].search(time_string)
        day = self.day_patterns[0].search(time_string)

        time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            time_point.year = year

        if month is not None:
            month_string = month.group(1)
            time_point.month = int(self._char_num2num(month_string))

        if day is not None:
            day_string = day.group(1)
            time_point.day = int(self._char_num2num(day_string))

        time_handler = time_point.handler()

        time_definition = self._check_blur(time_string, 'accurate')
        return time_handler, time_handler, 'time_point', time_definition

    def normalize_limit_solar_season(self, time_string):
        """ 解析限定 季度 """
        first_time_point, second_time_point = self._time_point()

        if self.time_base_handler[1] == -1 or self.time_base_handler[1] > 12:
            raise ValueError('the `month` of time_base `{}` is undefined.'.format(
                self.time_base_handler))

        infos = [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10, 11, 12]]
        spans = ['初', '中', '末']

        if '上' in time_string:
            season_count = time_string.count('上')
            for idx, item in enumerate(infos):
                if self.time_base_handler[1] in item:
                    season_month_idx = idx - season_count % 4
                    year_gap = (idx - season_count) // 4

                    match_span_flag = False
                    for i, span in enumerate(spans):
                        if span in time_string:
                            first_time_point.month = infos[season_month_idx][i]
                            second_time_point.month = infos[season_month_idx][i]
                            match_span_flag = True
                            break
                    if not match_span_flag:
                        first_time_point.month = infos[season_month_idx][0]
                        second_time_point.month = infos[season_month_idx][2]

                    first_time_point.year = self.time_base_handler[0] + year_gap
                    second_time_point.year = self.time_base_handler[0] + year_gap

        elif '下' in time_string:
            season_count = time_string.count('下')
            for idx, item in enumerate(infos):
                # 确保 season_month_idx < 4
                season_month_idx = idx + season_count % 4 - 4
                year_gap = (idx + season_count) // 4
                if self.time_base_handler[1] in item:
                    match_span_flag = False
                    for i, span in enumerate(spans):
                        if span in time_string:
                            first_time_point.month = infos[season_month_idx][i]
                            second_time_point.month = infos[season_month_idx][i]
                            match_span_flag = True
                            break
                    if not match_span_flag:
                        first_time_point.month = infos[season_month_idx][0]
                        second_time_point.month = infos[season_month_idx][2]

                    first_time_point.year = self.time_base_handler[0] + year_gap
                    second_time_point.year = self.time_base_handler[0] + year_gap

        elif '这' in time_string or '本' in time_string:
            for item in infos:
                if self.time_base_handler[1] in item:
                    first_time_point.month = item[0]
                    second_time_point.month = item[2]

        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def _normalize_solar_season(self, time_string):
        """ 解析 `(第)? 三 (个)?季度 (末)?` 等"""
        first_month = -1
        second_month = -1
        month = self.month_patterns[1].search(time_string)
        if month is not None:
            solar_season = month.group()
            if '1' in solar_season or '一' in solar_season or '首' in solar_season:
                if '第' in solar_season:
                    if '初' in solar_season:
                        first_month = 1
                        second_month = 1
                    elif '中' in solar_season:
                        first_month = 2
                        second_month = 2
                    elif '末' in solar_season:
                        first_month = 3
                        second_month = 3
                    else:
                        first_month = 1
                        second_month = 3

                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 3
                elif '后' in solar_season:
                    first_month = 10
                    second_month = 12
                else:
                    if '初' in solar_season:
                        first_month = 1
                        second_month = 1
                    elif '中' in solar_season:
                        first_month = 2
                        second_month = 2
                    elif '末' in solar_season:
                        first_month = 3
                        second_month = 3
                    else:
                        first_month = 1
                        second_month = 3
            elif '2' in solar_season or '二' in solar_season:
                if '第' in solar_season:
                    if '初' in solar_season:
                        first_month = 4
                        second_month = 4
                    elif '中' in solar_season:
                        first_month = 5
                        second_month = 5
                    elif '末' in solar_season:
                        first_month = 6
                        second_month = 6
                    else:
                        first_month = 4
                        second_month = 6
                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 6
                elif '后' in solar_season:
                    first_month = 7
                    second_month = 12
                else:
                    if '初' in solar_season:
                        first_month = 4
                        second_month = 4
                    elif '中' in solar_season:
                        first_month = 5
                        second_month = 5
                    elif '末' in solar_season:
                        first_month = 6
                        second_month = 6
                    else:
                        first_month = 4
                        second_month = 6
            elif '3' in solar_season or '三' in solar_season:
                if '第' in solar_season:
                    if '初' in solar_season:
                        first_month = 7
                        second_month = 7
                    elif '中' in solar_season:
                        first_month = 8
                        second_month = 8
                    elif '末' in solar_season:
                        first_month = 9
                        second_month = 9
                    else:
                        first_month = 7
                        second_month = 9
                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 9
                elif '后' in solar_season:
                    first_month = 4
                    second_month = 12
                else:
                    if '初' in solar_season:
                        first_month = 7
                        second_month = 7
                    elif '中' in solar_season:
                        first_month = 8
                        second_month = 8
                    elif '末' in solar_season:
                        first_month = 9
                        second_month = 9
                    else:
                        first_month = 7
                        second_month = 9
            elif '4' in solar_season or '四' in solar_season:
                # 4季度、第四季度
                if '初' in solar_season:
                    first_month = 10
                    second_month = 10
                elif '中' in solar_season:
                    first_month = 11
                    second_month = 11
                elif '末' in solar_season:
                    first_month = 12
                    second_month = 12
                else:
                    first_month = 10
                    second_month = 12
            elif '前两' in solar_season or '头两' in solar_season:
                first_month = 1
                second_month = 6
            elif '后两' in solar_season:
                first_month = 7
                second_month = 12
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return first_month, second_month

    def normalize_limit_year_solar_season(self, time_string):
        """ 解析 限定年/季度(公历) 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        first_time_point.month, second_time_point.month = self._normalize_solar_season(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_solar_season(self, time_string):
        """ 解析 年/季度(公历) 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        first_time_point.month, second_time_point.month = self._normalize_solar_season(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def _normalize_span_month(self, time_string):
        month = self.month_patterns[3].search(time_string)
        if month is not None:
            span_month = month.group()
            if '首' not in span_month:
                month_num = self.month_num_pattern.search(span_month)
                month_num = int(self._char_num2num(month_num.group()))

                if '前' in span_month or '头' in span_month:
                    first_month = 1
                    second_month = month_num
                elif '后' in span_month:
                    first_month = 13 - month_num
                    second_month = 12
                elif '第' in span_month:
                    first_month = month_num
                    second_month = month_num
                else:
                    raise ValueError('The given time string `{}` is illegal.'.format(time_string))
            else:
                first_month = 1
                second_month = 1

        else:
            first_month = -1
            second_month = -1

        return first_month, second_month

    def normalize_limit_year_span_month(self, time_string):
        """ 解析 限定年/前n个月 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        first_time_point.month, second_time_point.month = self._normalize_span_month(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_span_month(self, time_string):
        """ 解析 年/前n个月 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        first_time_point.month, second_time_point.month = self._normalize_span_month(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def _check_delta_base_conflict(self, time_delta_dict, time_base_handler):
        # 检测 time_delta 的 dict 与 time_base_handler 的冲突，会导致无法解析
        flag = True

        for idx, time_unit_name in enumerate(self.time_unit_names):
            if time_delta_dict.get(time_unit_name, 0) > 0 and time_base_handler[idx] == -1:
                flag = False
                break

        if not flag:
            raise ValueError('the given time_base `{}` is illegal'.format(time_base_handler))

        return flag

    @staticmethod
    def _compute_based_on_time_delta(time_base_datetime, time_delta_dict, coefficient=1):
        # 在时间基(datetime 格式)上加减 time_delta_dict 的时间
        # coefficient 仅取 1 或 -1，用于控制时间是加，还是减
        time_base_datetime += datetime.timedelta(days=coefficient * 365 * time_delta_dict.get('year', 0))
        time_base_datetime += datetime.timedelta(days=coefficient * 30.417 * time_delta_dict.get('month', 0))
        time_base_datetime += datetime.timedelta(days=coefficient * time_delta_dict.get('day', 0))
        time_base_datetime += datetime.timedelta(hours=coefficient * time_delta_dict.get('hour', 0))
        time_base_datetime += datetime.timedelta(minutes=coefficient * time_delta_dict.get('minute', 0))
        time_base_datetime += datetime.timedelta(seconds=coefficient * time_delta_dict.get('second', 0))

        return time_base_datetime

    def normalize_weilai_delta2span(self, time_string):
        """ 解析 未来（三天、48小时等）
        当 time_delta 位于 年、月、天等以上时，会将结果扩展到一日结束，即 time_delta 并不精准
        当 time_delta 位于 时、分、秒等以下时，不会将结果扩展到一小时结束，而是继承 time_base_handler，做到精准的 time_delta
        """
        time_delta, _, blur_time = self.normalize_standard_time_delta(time_string, time_type='time_delta')
        time_delta_dict = TimeUtility._cut_zero_key(time_delta.__dict__)

        self._check_delta_base_conflict(time_delta_dict, self.time_base_handler)

        first_time_handler = self.time_base_handler

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        time_base_datetime = TimeParser._compute_based_on_time_delta(
            time_base_datetime, time_delta_dict)
        second_time_handler = TimeParser._convert_time_base2handler(time_base_datetime)
        delta_set = set(time_delta_dict.keys())

        if 'hour' in delta_set or 'minute' in delta_set or 'second' in delta_set or 'day' in delta_set:
            definition = 'accurate'
            second_time_handler = [s if b > -1 else -1 for (b, s) in zip(self.time_base_handler, second_time_handler)]
        else:
            definition = 'blur'
            second_time_handler = [s if (b > -1 and idx <= 2) else -1
                                   for idx, (b, s) in enumerate(zip(self.time_base_handler, second_time_handler))]

        return first_time_handler, second_time_handler, 'time_span', definition

    def normalize_guoqu_delta2span(self, time_string):
        """ 解析 过去（三天、48小时等）
        当 time_delta 位于 年、月、天等以上时，会将结果扩展到一日结束，即 time_delta 并不精准
        当 time_delta 位于 时、分、秒等以下时，不会将结果扩展到一小时结束，而是继承 time_base_handler，做到精准的 time_delta
        """
        time_delta, _, blur_time = self.normalize_standard_time_delta(time_string, time_type='time_delta')
        time_delta_dict = TimeUtility._cut_zero_key(time_delta.__dict__)

        self._check_delta_base_conflict(time_delta_dict, self.time_base_handler)

        second_time_handler = self.time_base_handler

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)
        time_base_datetime = TimeParser._compute_based_on_time_delta(
            time_base_datetime, time_delta_dict, coefficient=-1)

        first_time_handler = TimeParser._convert_time_base2handler(time_base_datetime)
        delta_set = set(time_delta_dict.keys())

        if 'hour' in delta_set or 'minute' in delta_set or 'second' in delta_set or 'day' in delta_set:
            definition = 'accurate'
            if '近' in time_string and '最近' not in time_string:  # 这里有点太奇怪了。逻辑过于碎片化
                definition = 'blur'
            first_time_handler = [s if b > -1 else -1 for (b, s) in zip(self.time_base_handler, first_time_handler)]
        else:
            definition = 'blur'
            first_time_handler = [s if (b > -1 and idx <= 2) else -1
                                  for idx, (b, s) in enumerate(zip(self.time_base_handler, first_time_handler))]

        return first_time_handler, second_time_handler, 'time_span', definition

    def normalize_guo_delta2span(self, time_string):
        """ 解析 过（三天、48小时等）
        当 time_delta 位于 年、月、天等以上时，会将结果扩展到一日结束，即 time_delta 并不精准
        当 time_delta 位于 时、分、秒等以下时，不会将结果扩展到一小时结束，而是继承 time_base_handler，做到精准的 time_delta
        """
        time_delta, _, blur_time = self.normalize_standard_time_delta(time_string, time_type='time_delta')
        time_delta_dict = TimeUtility._cut_zero_key(time_delta.__dict__)

        self._check_delta_base_conflict(time_delta_dict, self.time_base_handler)

        second_time_handler = self.future_time

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)
        time_base_datetime = TimeParser._compute_based_on_time_delta(
            time_base_datetime, time_delta_dict)

        first_time_handler = TimeParser._convert_time_base2handler(time_base_datetime)
        delta_set = set(time_delta_dict.keys())
        if 'hour' in delta_set or 'minute' in delta_set or 'second' in delta_set:
            definition = 'accurate'
            first_time_handler = [s if b > -1 else -1 for (b, s) in zip(self.time_base_handler, first_time_handler)]
        else:
            definition = 'blur'
            first_time_handler = [s if (b > -1 and idx <= 2) else -1
                                  for idx, (b, s) in enumerate(zip(self.time_base_handler, first_time_handler))]

        return first_time_handler, second_time_handler, 'time_span', definition

    def normalize_second_delta_point(self, time_string):
        """ 解析 time delta 秒的 point 时间
        1、限制于 年月日时分秒 信息
        2、无法处理半秒
        3、若 time_base 中未指定秒，则以 time_base 信息不充分报错。
        """
        day_bias = [0, '弱']
        if self.time_base_handler[-1] == -1:
            raise ValueError(
                'the time_base `{}` is lack of second, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_second_delta, definition = self._normalize_delta_unit(
            time_string, self.second_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'blur'

        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = cur_time_handler
            if time_second_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(seconds=0.5)
            elif time_second_delta >= 1:
                first_datetime = cur_datetime - datetime.timedelta(seconds=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)

            time_type = 'time_point'
            definition = 'accurate'

        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'

        elif '后' in time_string:

            cur_datetime = time_base_datetime + datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            if time_second_delta == 0.5:
                second_datetime = cur_datetime + datetime.timedelta(seconds=0.5)
            elif time_second_delta >= 1:
                second_datetime = cur_datetime + datetime.timedelta(seconds=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)

            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(seconds=time_second_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition, day_bias

    def normalize_minute_delta_point(self, time_string):
        """ 解析 time delta 日的 point 时间
        1、限制于 年月日时分 信息
        2、若秒信息在 time_base 中未给出，则按照 该分钟00 进行处理
        3、若 time_base 中未指定分，则以 time_base 信息不充分报错。
        4、若是半分 + 0.5，超过 1 分钟 + 1
        """
        day_bias = [0, '弱']
        if self.time_base_handler[4] == -1:
            raise ValueError(
                'the time_base `{}` is lack of minute, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_minute_delta, definition = self._normalize_delta_unit(
            time_string, self.minute_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'blur'
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = cur_time_handler
            if time_minute_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(minutes=0.5)
            elif time_minute_delta >= 1:
                first_datetime = cur_datetime - datetime.timedelta(minutes=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)

            time_type = 'time_point'
            definition = 'accurate'
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:

            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            if time_minute_delta == 0.5:
                second_datetime = cur_datetime + datetime.timedelta(minutes=0.5)
            elif time_minute_delta >= 1:
                second_datetime = cur_datetime + datetime.timedelta(minutes=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)

            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_minute_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition, day_bias

    def normalize_quarter_delta_point(self, time_string):
        """ 解析 time delta 刻钟的 point 时间
        1、限制于 年月日时分 信息
        2、若秒信息在 time_base 中未给出，则按照 该分钟00 进行处理
        3、若 time_base 中未指定分，则以 time_base 信息不充分报错。
        4、刻钟不存在 半刻
        """
        mpq = 15

        day_bias = [0, '弱']
        if self.time_base_handler[4] == -1:
            raise ValueError(
                'the time_base `{}` is lack of minute, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_quarter_delta, definition = self._normalize_delta_unit(
            time_string, self.quarter_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'blur'
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = cur_time_handler
            if time_quarter_delta >= 1:
                first_datetime = cur_datetime - datetime.timedelta(minutes=1 * mpq)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)

            time_type = 'time_point'
            definition = 'accurate'
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:

            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            if time_quarter_delta >= 1:
                second_datetime = cur_datetime + datetime.timedelta(minutes=1 * mpq)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)

            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = cur_time_handler
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(minutes=time_quarter_delta * mpq)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition, day_bias

    def normalize_hour_delta_point(self, time_string):
        """ 解析 time delta 日的 point 时间
        1、限制于 年月日时，分秒信息被丢弃掉，
        2、若时分秒信息在 time_base 中未给出，则按照 00:00:00 进行处理
        3、若 time_base 中未指定月，则以 time_base 信息不充分报错。
        4、若是半小时 + 0.5， 超过1小时 + 1
        """
        day_bias = [0, '弱']
        if self.time_base_handler[3] == -1:
            raise ValueError(
                'the time_base `{}` is lack of hour, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_hour_delta, definition = self._normalize_delta_unit(
            time_string, self.hour_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], cur_time_handler[3],
                                   cur_time_handler[4], -1]
            time_type = 'time_span'
            definition = 'blur'
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = cur_time_handler
            if time_hour_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(hours=0.5)
            elif time_hour_delta >= 1:
                first_datetime = cur_datetime - datetime.timedelta(hours=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            first_time_handler = [first_time_handler[0], first_time_handler[1],
                                  first_time_handler[2], first_time_handler[3],
                                  first_time_handler[4], -1]

            time_type = 'time_point'
            definition = 'accurate'
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], cur_time_handler[3],
                                  cur_time_handler[4], -1]
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:

            cur_datetime = time_base_datetime + datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = cur_time_handler
            if time_hour_delta == 0.5:
                second_datetime = cur_datetime + datetime.timedelta(hours=0.5)
            elif time_hour_delta >= 1:
                second_datetime = cur_datetime + datetime.timedelta(hours=1)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            second_time_handler = [second_time_handler[0], second_time_handler[1],
                                   second_time_handler[2], second_time_handler[3],
                                   second_time_handler[4], -1]

            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], cur_time_handler[3],
                                   cur_time_handler[4], -1]
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(hours=time_hour_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], cur_time_handler[3],
                                  cur_time_handler[4], -1]
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition, day_bias

    def normalize_workday_delta_point(self, time_string):
        """ 解析 time delta 工作日的 point 时间
        1、限制于 年月日时，分秒信息被丢弃掉，
        2、若时分秒信息在 time_base 中未给出，则按照 00:00:00 进行处理
        3、若 time_base 中未指定月，则以 time_base 信息不充分报错。
        """
        if self.time_base_handler[2] == -1:
            raise ValueError(
                'the time_base `{}` is lack of day, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_day_delta, definition = self._normalize_delta_unit(
            time_string, self.workday_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        one_day = datetime.timedelta(days=1)
        cur_datetime = time_base_datetime
        workday_count = 0
        while True:
            cur_datetime += one_day
            if cur_datetime.weekday() <= 4:
                workday_count += 1
            if workday_count == time_day_delta:
                break

        if '之后' in time_string or '以后' in time_string:
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], -1, -1, -1]

            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], -1, -1, -1]

            second_datetime = cur_datetime

            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            second_time_handler = [second_time_handler[0], second_time_handler[1],
                                   second_time_handler[2], -1, -1, -1]

            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], -1, -1, -1]
            time_type = 'time_span'
            definition = 'accurate'
        else:
            # 一般不存在 `15个工作日之前`， `3个工作日以来` 这种表述
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_day_delta_point(self, time_string):
        """ 解析 time delta 日的 point 时间
        1、限制于 年月日时，分秒信息被丢弃掉，
        2、若时分秒信息在 time_base 中未给出，则按照 00:00:00 进行处理
        3、若 time_base 中未指定月，则以 time_base 信息不充分报错。
        """
        if self.time_base_handler[2] == -1:
            raise ValueError(
                'the time_base `{}` is lack of day, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_day_delta, definition = self._normalize_delta_unit(time_string, self.day_delta_pattern)

        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            if int(time_day_delta) == time_day_delta:  # 是整数，按整数返回
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], cur_time_handler[3], -1, -1]
            time_type = 'time_span'
            definition = 'blur'
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            if int(time_day_delta) == time_day_delta:  # 是整数，按整数返回
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], cur_time_handler[3], -1, -1]
            if time_day_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(days=0.5)
            elif time_day_delta >= 1:
                first_datetime = cur_datetime
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            if int(time_day_delta) == time_day_delta:  # 是整数，按整数返回
                first_time_handler = [first_time_handler[0], first_time_handler[1],
                                      first_time_handler[2], -1, -1, -1]
            else:
                first_time_handler = [first_time_handler[0], first_time_handler[1],
                                      first_time_handler[2], first_time_handler[3], -1, -1]
            time_type = 'time_point'
            definition = 'accurate'
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            if int(time_day_delta) == time_day_delta:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], cur_time_handler[3], -1, -1]
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            if int(time_day_delta) == time_day_delta:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], cur_time_handler[3], -1, -1]
            if time_day_delta == 0.5:
                second_datetime = cur_datetime + datetime.timedelta(days=0.5)
            elif time_day_delta >= 1:
                # second_datetime = cur_datetime + datetime.timedelta(days=1)
                second_datetime = cur_datetime
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            if int(time_day_delta) == time_day_delta:
                second_time_handler = [second_time_handler[0], second_time_handler[1],
                                       second_time_handler[2], -1, -1, -1]
            else:
                second_time_handler = [second_time_handler[0], second_time_handler[1],
                                       second_time_handler[2], second_time_handler[3], -1, -1]
            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            if int(time_day_delta) == time_day_delta:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], cur_time_handler[3], -1, -1]
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_day_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_day_delta) == time_day_delta:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], cur_time_handler[3], -1, -1]
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_week_delta_point(self, time_string):
        """ 解析 time delta 星期的 point 时间
        1、限制于 年月日，时分秒信息被丢弃掉，
        3、若 time_base 中未指日，则以 time_base 信息不充分报错。
        """
        dpw = 7
        if self.time_base_handler[2] == -1:
            raise ValueError(
                'the time_base `{}` is lack of day, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))

        time_week_delta, definition = self._normalize_delta_unit(time_string, self.week_delta_pattern)
        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], -1, -1, -1]

            time_type = 'time_span'
            definition = 'blur'
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], -1, -1, -1]

            first_datetime = cur_datetime - datetime.timedelta(days=dpw)

            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            first_time_handler = [first_time_handler[0], first_time_handler[1],
                                  first_time_handler[2], -1, -1, -1]

            time_type = 'time_point'
            definition = 'accurate'
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], -1, -1, -1]
            second_time_handler = self.future_time
            time_type = 'time_span'
            definition = 'blur'
        elif '后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], -1, -1, -1]

            second_datetime = cur_datetime + datetime.timedelta(days=dpw)

            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            second_time_handler = [second_time_handler[0], second_time_handler[1],
                                   second_time_handler[2], -1, -1, -1]
            time_type = 'time_point'
            definition = 'accurate'
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   cur_time_handler[2], -1, -1, -1]
            time_type = 'time_span'
            definition = 'accurate'
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_week_delta)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  cur_time_handler[2], -1, -1, -1]
            second_time_handler = self.time_base_handler
            time_type = 'time_span'
            definition = 'accurate'
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_month_delta_point(self, time_string):
        """ 解析 time delta 日的 point 时间
        1、限制于 年月日，时分秒信息被丢弃掉，
        2、若日时分秒信息在 time_base 中未给出，则按照 当月1号 00:00:00 进行处理
        3、若 time_base 中未指定月，则以 time_base 信息不充分报错。
        """
        dpm = 30.417
        time_month_delta, definition = self._normalize_delta_unit(
            time_string, self.month_delta_pattern)

        if self.time_base_handler[1] == -1:
            raise ValueError(
                'the time_base `{}` is lack of month, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        time_type = 'time_span'
        definition = 'blur'
        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       -1, -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       -1, -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
            if time_month_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(days=dpm * 0.5)
            elif time_month_delta >= 1:
                first_datetime = cur_datetime - datetime.timedelta(days=dpm)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                first_time_handler = [first_time_handler[0], first_time_handler[1],
                                      -1, -1, -1, -1]
            else:
                first_time_handler = [first_time_handler[0], first_time_handler[1],
                                      first_time_handler[2], -1, -1, -1]
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            second_time_handler = self.future_time
        elif '后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            if time_month_delta == 0.5:
                second_datetime = cur_datetime + datetime.timedelta(days=dpm * 0.5)
            elif time_month_delta >= 1:
                second_datetime = cur_datetime + datetime.timedelta(days=dpm)
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            if int(time_month_delta) == time_month_delta:  # 是整数，按整数返回
                second_time_handler = [second_time_handler[0], second_time_handler[1],
                                       -1, -1, -1, -1]
            else:
                second_time_handler = [second_time_handler[0], second_time_handler[1],
                                       second_time_handler[2], -1, -1, -1]
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            if int(time_month_delta) == time_month_delta:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       -1, -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       cur_time_handler[2], -1, -1, -1]
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_month_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_month_delta) == time_month_delta:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      cur_time_handler[2], -1, -1, -1]
            second_time_handler = self.time_base_handler
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_solar_season_delta_point(self, time_string):
        """ 解析 time delta 季度的 point 时间
        1、限制于 年月，日时分秒信息被丢弃掉，
        2、若日信息在 time_base 中未给出，则按照 当月1号 00:00:00 进行处理
        3、若 time_base 中未指定月，则以 time_base 信息不充分报错。
        """
        dpm = 30.417 * 3
        time_solar_season_delta, definition = self._normalize_delta_unit(
            time_string, self.solar_season_delta_pattern)

        if self.time_base_handler[1] == -1:
            raise ValueError(
                'the time_base `{}` is lack of month, '
                'causing an error for the string `{}`.'.format(
                    self.time_base_handler, time_string))
        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        time_type = 'time_span'
        definition = 'blur'
        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   -1, -1, -1, -1]
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   -1, -1, -1, -1]
            first_datetime = cur_datetime
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            first_time_handler = [first_time_handler[0], first_time_handler[1],
                                  -1, -1, -1, -1]
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  -1, -1, -1, -1]
            second_time_handler = self.future_time
        elif '后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  -1, -1, -1, -1]

            second_datetime = cur_datetime  # + datetime.timedelta(days=dpm)

            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            second_time_handler = [second_time_handler[0], second_time_handler[1],
                                   -1, -1, -1, -1]
        elif '内' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.time_base_handler
            second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                   -1, -1, -1, -1]

        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_solar_season_delta * dpm)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                  -1, -1, -1, -1]
            second_time_handler = self.time_base_handler
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_year_delta_point(self, time_string):
        """ 解析 time delta 日的 point 时间 """
        dpy = 365
        time_year_delta, definition = self._normalize_delta_unit(time_string, self.year_delta_pattern)
        time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)

        if '之前' in time_string or '以前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_year_delta * dpy)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

            first_time_handler = self.past_time
            if int(time_year_delta) == time_year_delta:
                second_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       -1, -1, -1, -1]
        elif '前' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_year_delta * dpy)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_year_delta) == time_year_delta:
                second_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
            else:
                second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                       -1, -1, -1, -1]
            if time_year_delta == 0.5:
                first_datetime = cur_datetime - datetime.timedelta(days=0.5 * dpy)
            elif time_year_delta >= 1:
                first_datetime = cur_datetime
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            first_time_handler = TimeParser._convert_time_base2handler(first_datetime)
            if int(time_year_delta) == time_year_delta:
                first_time_handler = [first_time_handler[0], -1, -1, -1, -1, -1]
            else:
                first_time_handler = [first_time_handler[0], first_time_handler[1],
                                      -1, -1, -1, -1]
        elif '之后' in time_string or '以后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_year_delta * dpy)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_year_delta) == time_year_delta:
                first_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            second_time_handler = self.future_time
        elif '后' in time_string:
            cur_datetime = time_base_datetime + datetime.timedelta(days=time_year_delta * dpy)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_year_delta) == time_year_delta:
                first_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            if time_year_delta == 0.5:
                second_datetime = cur_datetime
            elif time_year_delta >= 1:
                second_datetime = cur_datetime
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
            second_time_handler = TimeParser._convert_time_base2handler(second_datetime)
            if int(time_year_delta) == time_year_delta:
                second_time_handler = [second_time_handler[0], -1, -1, -1, -1, -1]
            else:
                second_time_handler = [second_time_handler[0], second_time_handler[1],
                                       -1, -1, -1, -1]
        elif '内' in time_string:
            if time_year_delta > 2000:
                # 字符串形如  “2025年内”，含义是当年一整年
                first_time_handler = [int(time_year_delta), -1, -1, -1, -1, -1]
                second_time_handler = [int(time_year_delta), -1, -1, -1, -1, -1]
            else:
                # 字符串形如 “三年内”、“五十年内”，含义为未来若干年内
                cur_datetime = time_base_datetime + datetime.timedelta(days=time_year_delta * dpy)
                cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)

                first_time_handler = self.time_base_handler
                if int(time_year_delta) == time_year_delta:
                    second_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
                else:
                    second_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                           -1, -1, -1, -1]
        elif '来' in time_string:
            cur_datetime = time_base_datetime - datetime.timedelta(days=time_year_delta * dpy)
            cur_time_handler = TimeParser._convert_time_base2handler(cur_datetime)
            if int(time_year_delta) == time_year_delta:
                first_time_handler = [cur_time_handler[0], -1, -1, -1, -1, -1]
            else:
                first_time_handler = [cur_time_handler[0], cur_time_handler[1],
                                      -1, -1, -1, -1]
            second_time_handler = self.time_base_handler
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        time_type = 'time_span'
        definition = 'blur'

        return first_time_handler, second_time_handler, time_type, definition

    def normalize_year_order_delta_point(self, time_string):
        # 第三年
        first_time_point, second_time_point = self._time_point()
        delta_num = self.delta_num_pattern.search(time_string)
        if delta_num:
            delta_num_string = delta_num.group()
            time_delta_num = int(self._char_num2num(delta_num_string))
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

        first_time_point.year = self.time_base_handler[0] + time_delta_num - 1
        second_time_point.year = self.time_base_handler[0] + time_delta_num - 1

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_day_order_delta_point(self, time_string):
        # 第N天：`第三天`，
        first_time_point, second_time_point = self._time_point()
        delta_num = self.delta_num_pattern.search(time_string)
        if delta_num:
            delta_num_string = delta_num.group()
            time_delta_num = int(self._char_num2num(delta_num_string))
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

        first_time_point.day = self.time_base_handler[2] + time_delta_num - 1
        second_time_point.day = self.time_base_handler[2] + time_delta_num - 1

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_day_order_delta_point(self, time_string):
        # YY年第N天：`2025年第三天`，
        first_time_point, second_time_point = self._time_point()
        year_string, delta_day_string = time_string.split("第")
        delta_day_string = "第" + delta_day_string

        year = self._normalize_year(year_string, self.time_base_handler)
        if year is not None:
            # 找到某年的第一天
            first_time_point.year = year
            second_time_point.year = year
            first_time_point.month = 1
            second_time_point.month = 1
            first_time_point.day = 1
            second_time_point.day = 1

        delta_num = self.delta_num_pattern.search(delta_day_string)
        if delta_num:
            delta_num_string = delta_num.group()
            time_delta_num = int(self._char_num2num(delta_num_string))
        else:
            raise ValueError('the given `{}` is illegal.'.format(time_string))

        first_time_point.day = first_time_point.day + time_delta_num - 1
        second_time_point.day = second_time_point.day + time_delta_num - 1

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def _normalize_blur_month(self, time_string):
        month = self.month_patterns[2].search(time_string)
        if month is not None:
            blur_month = month.group()
            if '初' in blur_month:
                first_month = 1
                second_month = 2
            elif '开年' in blur_month or '伊始' in blur_month:
                first_month = 1
                second_month = 1
            elif '末' in blur_month or '尾' in blur_month or '终' in blur_month or '底' in blur_month:
                first_month = 11
                second_month = 12
            elif '上半年' in blur_month:
                first_month = 1
                second_month = 6
            elif '下半年' in blur_month:
                first_month = 7
                second_month = 12
            elif '暑' in blur_month:  # 暑假一般在 7，8月，非准确时间
                first_month = 7
                second_month = 8
            elif '寒' in blur_month:  # 寒假一般在 2月，非准确时间
                first_month = 2
                second_month = 2
            elif '前期' in blur_month:
                first_month = 1
                second_month = 3
            elif '中期' in blur_month:
                first_month = 4
                second_month = 9
            elif '后期' in blur_month:
                first_month = 10
                second_month = 12
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))
        else:
            first_month = -1
            second_month = -1

        return first_month, second_month

    def normalize_year_blur_month(self, time_string):
        """ 解析 年/模糊月份 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        first_time_point.month, second_time_point.month = self._normalize_blur_month(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def _normalize_limit_year(self, time_string, time_base_handler):
        """ 处理 limit_year """
        year = self.year_patterns[1].search(time_string)
        if year is not None:
            year_string = year.group(1)
            if '大前' in year_string:
                first_year = time_base_handler[0] - 3
                second_year = time_base_handler[0] - 3
            elif '前一' in year_string:
                first_year = time_base_handler[0] - 1
                second_year = time_base_handler[0] - 1
            elif '前' in year_string:
                first_year = time_base_handler[0] - 2
                second_year = time_base_handler[0] - 2
            elif '去' in year_string or '上' in year_string:
                first_year = time_base_handler[0] - 1
                second_year = time_base_handler[0] - 1
            elif '今' in year_string or '这' in time_string or '同' in time_string or '当' in time_string or '本' in time_string:
                first_year = time_base_handler[0]
                second_year = time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                first_year = time_base_handler[0] + 1
                second_year = time_base_handler[0] + 1
            elif '后' in year_string:
                first_year = time_base_handler[0] + 2
                second_year = time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))
        else:
            # 存在`年初、年末`等字段，默认time_base年
            first_year = time_base_handler[0]
            second_year = time_base_handler[0]

        return first_year, second_year

    def normalize_limit_year_blur_month(self, time_string):
        """ 解析 限制年/模糊月份 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        first_time_point.month, second_time_point.month = self._normalize_blur_month(time_string)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def _normalize_limit_month(self, time_string, time_base_handler,
                               first_time_point, second_time_point):
        month = self.month_patterns[5].search(time_string)
        if month is not None:
            month_string = month.group()
            if '上' in month_string:
                month_count = month_string.count('上')
                if time_base_handler[1] == 1:
                    first_time_point.year = time_base_handler[0] - 1
                    second_time_point.year = time_base_handler[0] - 1
                    first_time_point.month = 12 - (month_count - 1)
                    second_time_point.month = 12 - (month_count - 1)
                else:
                    first_time_point.month = time_base_handler[1] - month_count
                    second_time_point.month = time_base_handler[1] - month_count
            elif '下' in month_string or '次' in month_string:
                # 当 month_string 不包含`上`但包含`次`时， month_string = 1
                month_count = month_string.count('下') or 1
                if time_base_handler[1] == 12:
                    first_time_point.year = time_base_handler[0] + 1
                    second_time_point.year = time_base_handler[0] + 1
                    first_time_point.month = month_count
                    second_time_point.month = month_count
                else:
                    first_time_point.month = time_base_handler[1] + month_count
                    second_time_point.month = time_base_handler[1] + month_count
            elif '同' in month_string or '本' in month_string or '当' in month_string or '这' in month_string:
                first_time_point.month = time_base_handler[1]
                second_time_point.month = time_base_handler[1]
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))
        else:
            first_time_point.month = time_base_handler[1]
            second_time_point.month = time_base_handler[1]

        return first_time_point, second_time_point

    def normalize_limit_month_day(self, time_string):
        """ 解析 限制月份、日 时间
        下个月5号，上个月 等等
        """
        day = self.day_patterns[0].search(time_string)

        first_time_point, second_time_point = self._time_point()
        first_time_point, second_time_point = self._normalize_limit_month(
            time_string, self.time_base_handler, first_time_point, second_time_point)

        if day:
            day = int(self._char_num2num(day.group(1)))
            first_time_point.day = day
            second_time_point.day = day

        return first_time_point.handler(), second_time_point.handler(), 'time_point',\
            'blur' if first_time_point.handler()[2] < 0 else 'accurate'

    def _normalize_blur_day(self, time_string, first_time_point, second_time_point):
        blur_day = self.day_patterns[4].search(time_string)
        if blur_day:
            blur_day_string = blur_day.group()
            if '上旬' in blur_day_string:
                first_day = 1
                second_day = 10
            elif '中旬' in blur_day_string:
                first_day = 11
                second_day = 20
            elif '下旬' in blur_day_string:
                first_day = 21
                second_day = -1
            elif '初' in blur_day_string:
                first_day = 1
                second_day = 5
            elif '中' in blur_day_string:
                first_day = 10
                second_day = 20
            elif '底' in blur_day_string or '末' in blur_day_string:
                first_day = 25
                second_day = -1
            else:
                raise ValueError('can not parse `{}`.'.format(time_string))
            first_time_point.day = int(first_day)
            second_time_point.day = int(second_day)
        else:
            first_time_point.day = -1
            second_time_point.day = -1

        return first_time_point, second_time_point

    def normalize_limit_month_blur_day(self, time_string):
        """ 解析 限制月份、模糊日 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point, second_time_point = self._normalize_limit_month(
            time_string, self.time_base_handler, first_time_point, second_time_point)

        first_time_point, second_time_point = self._normalize_blur_day(
            time_string, first_time_point, second_time_point)

        return first_time_point.handler(), second_time_point.handler(), 'time_point',\
            'blur' if first_time_point.handler()[2] < 0 else 'accurate'

    def normalize_limit_month(self, time_string):
        """ 解析 限制月份 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point, second_time_point = self._normalize_limit_month(
            time_string, self.time_base_handler, first_time_point, second_time_point)

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_point.handler(), second_time_point.handler(), 'time_point',\
            'blur' if first_time_point.handler()[2] < 0 else 'accurate'

    def normalize_century_year(self, time_string):
        """ 解析 世纪、年 时间 """
        century = self.century_pattern.search(time_string)
        decade = self.decade_pattern.search(time_string)

        first_time_point, second_time_point = self._time_point()
        if '公元前' in time_string:
            christ_era = False
        else:
            christ_era = True

        if century is not None:
            # 上世纪确指 20世纪
            if '上世纪' in time_string:
                century = 20
            else:
                century = int(self._char_num2num(century.group()))

        if decade is not None:
            decade = int(self._char_num2num(decade.group()))

        # century 与 decade 不可能同时为空，否则该条不会被匹配
        if century is None:
            if decade > 20:
                year = 1900 + decade
            else:
                year = 2000 + decade

            if '初期' in time_string or '初' in time_string or '前' in time_string:
                first_year = year
                second_year = year + 2
            elif '中期' in time_string or '中' in time_string:
                first_year = year + 3
                second_year = year + 6
            elif '末期' in time_string or '末' in time_string or '后' in time_string:
                first_year = year + 7
                second_year = year + 9
            else:
                first_year = year
                second_year = year + 9
        elif decade is None:
            if christ_era:
                year = (century - 1) * 100
            else:
                year = - century * 100

            if '初期' in time_string or '初' in time_string or '前' in time_string:
                first_year = year
                second_year = year + 19
            elif '中期' in time_string or '中' in time_string:
                first_year = year + 20
                second_year = year + 79
            elif '末期' in time_string or '末' in time_string or '后' in time_string:
                first_year = year + 80
                second_year = year + 99
            else:
                first_year = year
                second_year = year + 99
        else:
            if christ_era:
                year = (century - 1) * 100 + decade
            else:
                year = - century * 100 + decade

            if '初期' in time_string or '初' in time_string or '前期' in time_string:
                first_year = year
                second_year = year + 2
            elif '中期' in time_string or '中' in time_string:
                first_year = year + 3
                second_year = year + 6
            elif '末期' in time_string or '末' in time_string or '后' in time_string:
                first_year = year + 7
                second_year = year + 9
            else:
                first_year = year
                second_year = year + 9

        first_time_point.year = first_year
        second_time_point.year = second_year

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_limit_year_month_day(self, time_string):
        """ 解析 限定年、月、日 时间 """
        month = self.month_patterns[0].search(time_string)
        day = self.day_patterns[0].search(time_string)

        time_point = TimePoint()

        time_point.year, _ = self._normalize_limit_year(
            time_string, self.time_base_handler)
        time_type = 'time_span'
        if month is not None:
            time_point.month = int(self._char_num2num(month.group(1)))

        if day is not None:
            time_point.day = int(self._char_num2num(day.group(1)))
            time_type = 'time_point'

        time_definition = self._check_blur(time_string, 'accurate')

        return time_point.handler(), time_point.handler(), time_type, time_definition

    def normalize_blur_year(self, time_string):
        """ 解析 模糊年 时间 """
        blur_year_1 = self.year_patterns[2].search(time_string)
        blur_year_2 = self.year_patterns[3].search(time_string)
        blur_year_3 = self.year_patterns[4].search(time_string)

        first_time_point, second_time_point = self._time_point()
        # 月份针对 半年设定
        first_month = -1
        second_month = -1

        if blur_year_1 is not None:
            year_num = self.year_num_pattern.search(time_string)
            year_num = int(self._char_num2num(year_num.group()))

            if '几' in time_string or ('多' in time_string and (time_string.index('多') < time_string.index('年'))):
                # `十多年前` 与 `一年多以前` 中，多和 年的位置变化
                # 此时不会出现 `年半` 的情况
                if '年前' in time_string or '年之前' in time_string or '年以前' in time_string:

                    if year_num % 1000 == 0:
                        first_year = self.time_base_handler[0] - year_num - 1000
                    elif year_num % 100 == 0:
                        first_year = self.time_base_handler[0] - year_num - 100
                    elif year_num % 10 == 0:
                        first_year = self.time_base_handler[0] - year_num - 10
                    second_year = self.time_base_handler[0] - year_num
                elif '年后' in time_string or '年之后' in time_string or '年以后' in time_string:
                    first_year = self.time_base_handler[0] + year_num
                    if year_num % 1000 == 0:
                        second_year = self.time_base_handler[0] + year_num + 1000
                    elif year_num % 100 == 0:
                        second_year = self.time_base_handler[0] + year_num + 100
                    elif year_num % 10 == 0:
                        second_year = self.time_base_handler[0] + year_num + 10
                else:
                    raise ValueError('The given time string `{}` is illegal.'.format(time_string))

            else:
                if '年半' in time_string:
                    if '前' in time_string:
                        if 3 < self.time_base_handler[1] <= 9:
                            first_year = self.time_base_handler[0] - year_num - 1
                            first_month = self.time_base_handler[1] + 3
                            second_year = self.time_base_handler[0] - year_num
                            second_month = self.time_base_handler[1] - 3
                        elif 0 < self.time_base_handler[1] <= 3:
                            first_year = self.time_base_handler[0] - year_num
                            first_month = self.time_base_handler[1] + 3
                            second_year = self.time_base_handler[0] - year_num
                            second_month = self.time_base_handler[1] + 9
                        elif self.time_base_handler[1] > 9:
                            first_year = self.time_base_handler[0] - year_num
                            first_month = self.time_base_handler[1] - 9
                            second_year = self.time_base_handler[0] - year_num
                            second_month = self.time_base_handler[1] - 3
                        else:
                            # 即，基础时间中无月份，也就无从判定月份，按年返回
                            first_year = self.time_base_handler[0] - year_num
                            second_year = self.time_base_handler[0] - year_num

                    elif '后' in time_string:
                        if 3 < self.time_base_handler[1] <= 9:
                            first_year = self.time_base_handler[0] + year_num
                            first_month = self.time_base_handler[1] + 3
                            second_year = self.time_base_handler[0] + year_num + 1
                            second_month = self.time_base_handler[1] - 3
                        elif 0 < self.time_base_handler[1] <= 3:
                            first_year = self.time_base_handler[0] + year_num
                            first_month = self.time_base_handler[1] + 3
                            second_year = self.time_base_handler[0] + year_num
                            second_month = self.time_base_handler[1] + 9
                        elif self.time_base_handler[1] > 9:
                            first_year = self.time_base_handler[0] + year_num + 1
                            first_month = self.time_base_handler[1] - 9
                            second_year = self.time_base_handler[0] + year_num + 1
                            second_month = self.time_base_handler[1] - 3
                        else:
                            # 即，基础时间中无月份，也就无从判定月份，按年返回
                            first_year = self.time_base_handler[0] + year_num
                            second_year = self.time_base_handler[0] + year_num

                else:

                    if '前' in time_string:
                        first_year = self.time_base_handler[0] - year_num
                        second_year = self.time_base_handler[0] - year_num
                    elif '后' in time_string:
                        first_year = self.time_base_handler[0] + year_num
                        second_year = self.time_base_handler[0] + year_num
                    else:
                        raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        elif blur_year_2 is not None:
            if '前' in time_string:
                if 3 < self.time_base_handler[1] <= 9:
                    first_year = self.time_base_handler[0] - 1
                    first_month = self.time_base_handler[1] + 3
                    second_year = self.time_base_handler[0]
                    second_month = self.time_base_handler[1] - 3
                elif self.time_base_handler[1] <= 3:
                    first_year = self.time_base_handler[0]
                    first_month = self.time_base_handler[1] + 3
                    second_year = self.time_base_handler[0]
                    second_month = self.time_base_handler[1] + 9
                elif self.time_base_handler[1] > 9:
                    first_year = self.time_base_handler[0]
                    first_month = self.time_base_handler[1] - 9
                    second_year = self.time_base_handler[0]
                    second_month = self.time_base_handler[1] - 3
                else:
                    # 即，基础时间中无月份，也就无从判定月份，按年返回
                    first_year = self.time_base_handler[0]
                    second_year = self.time_base_handler[0]
            elif '后' in time_string:
                if 3 < self.time_base_handler[1] <= 9:
                    first_year = self.time_base_handler[0]
                    first_month = self.time_base_handler[1] + 3
                    second_year = self.time_base_handler[0] + 1
                    second_month = self.time_base_handler[1] - 3
                elif self.time_base_handler[1] <= 3:
                    first_year = self.time_base_handler[0]
                    first_month = self.time_base_handler[1] + 3
                    second_year = self.time_base_handler[0]
                    second_month = self.time_base_handler[1] + 9
                elif self.time_base_handler[1] > 9:
                    first_year = self.time_base_handler[0] + 1
                    first_month = self.time_base_handler[1] - 9
                    second_year = self.time_base_handler[0] + 1
                    second_month = self.time_base_handler[1] - 3
                else:
                    # 即，基础时间中无月份，也就无从判定月份，按年返回
                    first_year = self.time_base_handler[0]
                    second_year = self.time_base_handler[0]
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        elif blur_year_3 is not None:
            # raise ValueError('Can not parse time string `{}`.'.format(time_string))
            if '前' in time_string:
                if '几十' in time_string:
                    first_year = self.time_base_handler[0] - 100
                    second_year = self.time_base_handler[0] - 20
                elif '几百' in time_string:
                    first_year = self.time_base_handler[0] - 1000
                    second_year = self.time_base_handler[0] - 200
                elif '几千' in time_string:
                    first_year = self.time_base_handler[0] - 10000
                    second_year = self.time_base_handler[0] - 2000
            elif '后' in time_string:
                if '几十' in time_string:
                    first_year = self.time_base_handler[0] + 20
                    second_year = self.time_base_handler[0] + 100
                elif '几百' in time_string:
                    first_year = self.time_base_handler[0] + 200
                    second_year = self.time_base_handler[0] + 1000
                elif '几千' in time_string:
                    first_year = self.time_base_handler[0] + 2000
                    second_year = self.time_base_handler[0] + 10000

        else:
            raise ValueError('There is a bug for `{}`.'.format(time_string))

        first_time_point.year = first_year
        second_time_point.year = second_year
        first_time_point.month = first_month
        second_time_point.month = second_month

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_lunar_year_month_day(self, time_string):
        """ 解析 农历年、月、日 时间 """
        lunar_month = self.month_patterns[4].search(time_string)
        lunar_day = self.day_patterns[1].search(time_string)
        use_lunar_day = True
        if lunar_day is None:
            lunar_day = self.day_patterns[0].search(time_string)
            if lunar_day is not None:
                use_lunar_day = False

        lunar_time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            lunar_time_point.year = year

        leap_month = False
        if lunar_month:
            lunar_month_string = lunar_month.group(1)
            if '闰' in lunar_month_string:
                leap_month = True
            lunar_month_string = lunar_month_string\
                .replace('正', '一').replace('冬', '十一').replace('腊', '十二').replace('闰', '')
            lunar_month_string = int(self._char_num2num(lunar_month_string))

            lunar_time_point.month = lunar_month_string

        if lunar_day:
            if use_lunar_day:
                lunar_day_string = lunar_day.group(0)
                lunar_day_string = lunar_day_string\
                    .replace('初', '').replace('廿', '二十')
                lunar_day_string = int(self._char_num2num(lunar_day_string))

            else:
                lunar_day_string = lunar_day.group(1)
                lunar_day_string = int(self._char_num2num(lunar_day_string))

            lunar_time_point.day = lunar_day_string

        lunar_time_handler = lunar_time_point.handler()

        # 对农历日期的补全
        lunar_time_handler = TimeUtility.time_completion(lunar_time_handler, self.time_base_handler)

        if self.lunar_date:
            first_time_handler, second_time_handler = self._convert_lunar2solar(
                lunar_time_handler, leap_month=leap_month)
        else:
            first_time_handler, second_time_handler = lunar_time_handler, lunar_time_handler

        return first_time_handler, second_time_handler, 'time_point', 'accurate'

    def normalize_lunar_limit_year_month_day(self, time_string):
        """ 解析 农历限定年、月、日 时间 """
        lunar_month = self.month_patterns[4].search(time_string)
        lunar_day = self.day_patterns[1].search(time_string)

        lunar_time_point = TimePoint()

        first_year, second_year = self._normalize_limit_year(
            time_string, self.time_base_handler)
        lunar_time_point.year = first_year

        leap_month = False
        if lunar_month:
            lunar_month_string = lunar_month.group(1)
            if '闰' in lunar_month_string:
                leap_month = True
            lunar_month_string = lunar_month_string\
                .replace('正', '一').replace('冬', '十一').replace('腊', '十二').replace('闰', '')
            lunar_month_string = int(self._char_num2num(lunar_month_string))

            lunar_time_point.month = lunar_month_string

        if lunar_day:
            lunar_day_string = lunar_day.group(0)
            lunar_day_string = lunar_day_string\
                .replace('初', '').replace('廿', '二十')
            lunar_day_string = int(self._char_num2num(lunar_day_string))

            lunar_time_point.day = lunar_day_string

        lunar_time_handler = lunar_time_point.handler()

        # completion of lunar date
        lunar_time_handler = TimeUtility.time_completion(lunar_time_handler, self.time_base_handler)

        first_time_handler, second_time_handler = self._convert_lunar2solar(
            lunar_time_handler, leap_month=leap_month)

        return first_time_handler, second_time_handler, 'time_point', 'accurate'

    def normalize_year_24st(self, time_string):
        """ 解析 `年、节气` """
        _24st = self.day_patterns[2].search(time_string)

        time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            time_point.year = year

        if _24st:
            # 首先要确定年份，不可以为 -1，否则造成公历、农历转换错误。
            if time_point.year == -1:
                time_point.year = self.time_base_handler[0]

            _24st_string = _24st.group()
            month_string, day_string = self._parse_solar_terms(time_point.year, _24st_string)
            time_point.month = int(month_string)
            time_point.day = int(day_string)

            if _24st_string in ['小寒', '大寒']:
                time_point.year += 1

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_lunar_season(self, time_string):
        """ 解析 年/季节(农历) 时间 """
        season = self.day_patterns[3].search(time_string)

        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year
        else:
            first_time_point.year = self.time_base_handler[0]
            second_time_point.year = self.time_base_handler[0]

        if season is not None:
            solar_season = season.group()
            if '春' in solar_season:
                first_month, first_day = self._parse_solar_terms(first_time_point.year, '立春')
                second_month, second_day = self._parse_solar_terms(first_time_point.year, '立夏')
            elif '夏' in solar_season:
                first_month, first_day = self._parse_solar_terms(first_time_point.year, '立夏')
                second_month, second_day = self._parse_solar_terms(first_time_point.year, '立秋')
            elif '秋' in solar_season:
                first_month, first_day = self._parse_solar_terms(first_time_point.year, '立秋')
                second_month, second_day = self._parse_solar_terms(first_time_point.year, '立冬')
            elif '冬' in solar_season:
                first_month, first_day = self._parse_solar_terms(first_time_point.year, '立冬')
                second_month, second_day = self._parse_solar_terms(first_time_point.year, '立春')
                second_time_point.year += 1
            else:
                raise ValueError('the season string {} is illegal.'.format(time_string))

            first_time_point.month = int(first_month)
            second_time_point.month = int(second_month)
            first_time_point.day = int(first_day)
            second_time_point.day = int(second_day) - 1

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_limit_year_lunar_season(self, time_string):
        """ 解析 限定年/季节(农历) 时间 :return:
        """
        season = self.day_patterns[3].search(time_string)

        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        if season is not None:
            solar_season = season.group()

            four_season_string = '春夏秋冬春'
            for idx, item in enumerate(four_season_string):
                if idx != 4:
                    if item in solar_season:
                        first_month, first_day = self._parse_solar_terms(first_time_point.year, '立' + item)
                        second_month, second_day = self._parse_solar_terms(
                            first_time_point.year, '立' + four_season_string[idx + 1])
                        if idx == 3:
                            second_time_point.year += 1
                        break
            else:
                raise ValueError('the season string {} is illegal.'.format(time_string))

            first_time_point.month = int(first_month)
            second_time_point.month = int(second_month)
            first_time_point.day = int(first_day)
            second_time_point.day = int(second_day) - 1

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_month_blur_day(self, time_string):
        """ 解析 `年、月、模糊 日` 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        month = self.month_patterns[0].search(time_string)
        if month:
            month_string = int(self._char_num2num(month.group(1)))
            first_time_point.month = month_string
            second_time_point.month = month_string

        first_time_point, second_time_point = self._normalize_blur_day(
            time_string, first_time_point, second_time_point)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_limit_year_month_blur_day(self, time_string):
        """ 解析 `年、月、模糊 日` 时间 """
        month = self.month_patterns[0].search(time_string)

        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        if month:
            month_string = int(self._char_num2num(month.group(1)))
            first_time_point.month = month_string
            second_time_point.month = month_string

        first_time_point, second_time_point = self._normalize_blur_day(
            time_string, first_time_point, second_time_point)

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur'

    def normalize_standard_week_day(self, time_string):
        """ 解析 `标准星期 N` 时间 """
        week = self.day_patterns[7].search(time_string)
        week_day = self.day_patterns[8].search(time_string)

        one_week = datetime.timedelta(days=7)
        time_base_datetime = TimeParser._convert_handler2datetime(
            self.time_base_handler)

        if week:
            week_string = week.group()
            if '上' in week_string:
                week_count = week_string.count('上')
                time_base_datetime -= one_week * week_count
            elif '下' in week_string:
                week_count = week_string.count('下')
                time_base_datetime += one_week * week_count
            elif '本' in week_string or '这' in week_string:
                pass
            else:
                pass  # 即为本周

        if week_day:
            week_day_string = week_day.group()

            trans = ['一二三四五六天末日', [0, 1, 2, 3, 4, 5, 6, 6, 6]]
            for c, i in zip(trans[0], trans[1]):
                if c in week_day_string:
                    target_day = TimeParser.compute_week_day(time_base_datetime, i, flag=False)
                    break
            else:
                raise ValueError('`星期{}` is illegal.'.format(week_day_string))

        time_handler = TimeParser._convert_time_base2handler(target_day)
        time_point = TimePoint()
        time_point.year = time_handler[0]
        time_point.month = time_handler[1]
        time_point.day = time_handler[2]

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_blur_week(self, time_string):
        """ 解析 `前后 N 星期` 时间 """
        week_1 = self.day_patterns[5].search(time_string)
        week_2 = self.day_patterns[6].search(time_string)
        week_3 = self.day_patterns[7].search(time_string)

        one_week = datetime.timedelta(days=7)
        time_base_datetime = TimeParser._convert_handler2datetime(
            self.time_base_handler)

        first_time_point, second_time_point = self._time_point()
        if week_1:
            week_string = week_1.group()
            week_num = self.week_num_pattern.search(week_string)
            if week_num:
                week_num = int(self._char_num2num(week_num.group()))
            else:
                week_num = 0

            if '前' in week_string:
                for _ in range(week_num):
                    time_base_datetime -= one_week
                first_time_datetime = TimeParser.compute_week_day(time_base_datetime, 0, flag=False)
                self.map_time_unit(first_time_point, first_time_datetime, unit=['year', 'month', 'day'])
                first_time_handler = first_time_point.handler()
                second_time_handler = self.time_base_handler
            elif '后' in week_string:
                for _ in range(week_num):
                    time_base_datetime += one_week
                second_time_datetime = TimeParser.compute_week_day(time_base_datetime, 6, flag=False)
                self.map_time_unit(second_time_point, second_time_datetime, unit=['year', 'month', 'day'])
                second_time_handler = second_time_point.handler()
                first_time_handler = self.time_base_handler
            else:
                raise ValueError('the time string `{}` is illegal.'.format(time_string))

        elif week_2:
            week_string = week_2.group()
            week_num = self.week_num_pattern.search(week_string)
            if week_num:
                week_num = int(self._char_num2num(week_num.group()))
            else:
                week_num = 0

            if '前' in week_string:
                for _ in range(week_num):
                    time_base_datetime -= one_week

            elif '后' in week_string:
                for _ in range(week_num):
                    time_base_datetime += one_week

            else:
                raise ValueError('the time string `{}` is illegal.'.format(time_string))

            first_time_datetime = TimeParser.compute_week_day(time_base_datetime, 0, flag=False)
            self.map_time_unit(first_time_point, first_time_datetime, unit=['year', 'month', 'day'])
            first_time_handler = first_time_point.handler()

            second_time_datetime = TimeParser.compute_week_day(time_base_datetime, 6, flag=False)
            self.map_time_unit(second_time_point, second_time_datetime, unit=['year', 'month', 'day'])
            second_time_handler = second_time_point.handler()

        elif week_3:
            week_string = week_3.group()
            if '上上' in week_string:
                time_base_datetime -= (one_week + one_week)
            elif '下下' in week_string:
                time_base_datetime += (one_week + one_week)
            elif '上' in week_string:
                time_base_datetime -= one_week
            elif '下' in week_string:
                time_base_datetime += one_week
            elif '本' in week_string or '这' in week_string:
                pass
            else:
                pass  # 即为本周

            first_time_datetime = TimeParser.compute_week_day(time_base_datetime, 0, flag=False)
            self.map_time_unit(first_time_point, first_time_datetime, unit=['year', 'month', 'day'])
            first_time_handler = first_time_point.handler()

            second_time_datetime = TimeParser.compute_week_day(time_base_datetime, 6, flag=False)
            self.map_time_unit(second_time_point, second_time_datetime, unit=['year', 'month', 'day'])
            second_time_handler = second_time_point.handler()

        else:
            raise ValueError('the given time string is illegal.\n{}'.format(
                traceback.format_exc()))

        return first_time_handler, second_time_handler, 'time_point', 'blur'

    @staticmethod
    def compute_week_day(cur_day, target_week_day, flag=True):
        """ 从1 号开始计算，向后寻找对应的星期 N
        cur_day: datetime obj
        target_week_day: int (0-6)
        flag: 指示向前还是向后寻找， flag 为 True，向前寻找，否则在之前寻找
        """
        one_day = datetime.timedelta(days=1)
        cur_week_day = cur_day.weekday()
        delta = cur_week_day - target_week_day

        if delta == 0:
            return cur_day
        elif delta > 0:
            if flag:
                for _ in range(7 - delta):
                    cur_day += one_day
            else:
                for _ in range(delta):
                    cur_day -= one_day
        elif delta < 0:
            for _ in range(abs(delta)):
                cur_day += one_day

        return cur_day

    def normalize_limit_week(self, time_string):
        """ 解析 `M月的第 N 个星期` 时间 """
        month = self.month_patterns[0].search(time_string)
        week_res = self.day_patterns[9].search(time_string)
        week_day = self.day_patterns[8].search(time_string)

        time_point = TimePoint()

        if month:
            month_num = self.month_num_pattern.search(month.group())
            if month_num:
                month_num = int(self._char_num2num(month_num.group()))
                time_point.month = month_num
            else:
                raise ValueError('month string is not in `{}`.'.format(time_string))
        else:
            raise ValueError('month string is not in `{}`.'.format(time_string))

        if week_res and week_day:
            week_res = week_res.group()
            week_order_num = self.week_num_pattern.search(week_res)
            week_order_num = int(self._char_num2num(week_order_num.group()))
            week_day_string = week_day.group()

            one_week = datetime.timedelta(days=7)

            # 补全年份
            time_point.year = self.time_base_handler[0]

            time_base_datetime = TimeParser._convert_handler2datetime(
                [time_point.year, time_point.month, 1, 0, 0, 0])

            trans = ['一二三四五六天末日', [0, 1, 2, 3, 4, 5, 6, 6, 6]]
            for c, i in zip(trans[0], trans[1]):
                if c in week_day_string:
                    target_day = TimeParser.compute_week_day(time_base_datetime, i, flag=True)
                    break
            else:
                raise ValueError('`星期{}` is illegal.'.format(week_day_string))

            # 向后推周
            for i in range(week_order_num - 1):
                target_day += one_week

            time_handler = TimeParser._convert_time_base2handler(target_day)
            time_point.day = time_handler[2]
        else:
            raise ValueError('th given string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def _normalize_month_order_week(self, time_string, first_point_month, first_point_year=None):
        """ 解析 `第 N 个星期` 时间 """
        week_res = self.day_patterns[9].search(time_string)
        if week_res:
            week_res = week_res.group()
            week_order_num = self.week_num_pattern.search(week_res)
            week_order_num = int(self._char_num2num(week_order_num.group()))
            day_offset = week_order_num * 7
            if first_point_year is not None:
                first_day = datetime.datetime(first_point_year, first_point_month, 1)
            else:
                first_day = datetime.datetime(self.time_base_handler[0], first_point_month, 1)
            first_day_weekday = int(first_day.strftime("%w"))
            if first_day_weekday == 1:
                pass
            elif first_day_weekday == 0:
                day_offset += 1
            else:
                day_offset += 7 + 1 - first_day_weekday

            first_point_day = first_day + datetime.timedelta(days=day_offset - 7)
            second_point_day = first_day + datetime.timedelta(days=day_offset - 1)

            if first_point_day.month != first_point_month:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        return first_point_day, second_point_day

    def normalize_month_week(self, time_string):
        """ 解析 `2月第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        month = self.month_patterns[0].search(time_string)

        if month:
            month_num = self.month_num_pattern.search(month.group())
            month_num = int(self._char_num2num(month_num.group()))
            first_time_point.month = month_num
            second_time_point.month = month_num
        else:
            raise ValueError('month string is not in `{}`.'.format(time_string))

        first_point_day, second_point_day = self._normalize_month_order_week(
            time_string, first_time_point.month)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        # 12 月第四周有可能导致年份加一
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_limit_month_week(self, time_string):
        """ 解析 `限定月 第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point, second_time_point = self._normalize_limit_month(
            time_string, self.time_base_handler, first_time_point, second_time_point)

        first_point_day, second_point_day = self._normalize_month_order_week(
            time_string, first_time_point.month)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        # 12 月第四周有可能导致年份加一
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_month_week(self, time_string):
        """ 解析 `2021年2月第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
            second_time_point.year = year

        month = self.month_patterns[0].search(time_string)
        if month:
            month_string = int(self._char_num2num(month.group(1)))
            first_time_point.month = month_string
            second_time_point.month = month_string

        first_point_day, second_point_day = self._normalize_month_order_week(
            time_string, first_time_point.month, first_time_point.year)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_limit_year_month_week(self, time_string):
        """ 解析 `限定年 2月第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point.year, second_time_point.year = self._normalize_limit_year(
            time_string, self.time_base_handler)

        month = self.month_patterns[0].search(time_string)
        if month:
            month_string = int(self._char_num2num(month.group(1)))
            first_time_point.month = month_string
            second_time_point.month = month_string

        first_point_day, second_point_day = self._normalize_month_order_week(
            time_string, first_time_point.month, first_time_point.year)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def _normalize_year_order_week(self, time_string, first_point_year):
        # 找到 一年中的 第 N 个星期
        week_res = self.day_patterns[9].search(time_string)
        if week_res:
            week_res = week_res.group()
            week_order_num = self.week_num_pattern.search(week_res)
            week_order_num = int(self._char_num2num(week_order_num.group()))
            day_offset = week_order_num * 7

            first_day = datetime.datetime(first_point_year, 1, 1)
            first_day_weekday = int(first_day.strftime("%w"))
            if first_day_weekday == 1:
                pass
            elif first_day_weekday == 0:
                day_offset += 1
            else:
                day_offset += 7 + 1 - first_day_weekday

            first_point_day = first_day + datetime.timedelta(days=day_offset - 7)
            second_point_day = first_day + datetime.timedelta(days=day_offset - 1)

            if first_point_day.year != first_point_year:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))

            return first_point_day, second_point_day
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

    def normalize_year_week(self, time_string):
        """ 解析 `2021年第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        year = self._normalize_year(time_string, self.time_base_handler)
        if year is not None:
            first_time_point.year = year
        else:
            first_time_point.year = self.time_base_handler[0]

        first_point_day, second_point_day = self._normalize_year_order_week(
            time_string, first_time_point.year)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_limit_year_week(self, time_string):
        """ 解析 `限定年 第 N 个星期` 时间 """
        first_time_point, second_time_point = self._time_point()
        first_time_point.year, _ = self._normalize_limit_year(
            time_string, self.time_base_handler)

        first_point_day, second_point_day = self._normalize_year_order_week(
            time_string, first_time_point.year)

        self.map_time_unit(first_time_point, first_point_day, unit=['month', 'day'])
        self.map_time_unit(second_time_point, second_point_day, unit=['year', 'month', 'day'])

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'accurate'

    def normalize_year_fixed_solar_festival(self, time_string):
        """ 解析 `公历固定节日` 时间 """
        time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        time_point.year = year if year is not None else self.time_base_handler[0]

        # 默认必然已匹配某节日
        # 按照长度从长到短匹配，避免重复
        for festival, date in sorted(self.fixed_solar_holiday_dict.items(), key=lambda item: len(item[0]), reverse=True):
            if festival in time_string:
                time_point.month = date[0]
                time_point.day = date[1]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_limit_year_fixed_solar_festival(self, time_string):
        """ 解析 `限定年 公历固定节日` 时间 """
        time_point = TimePoint()

        time_point.year, _ = self._normalize_limit_year(
            time_string, self.time_base_handler)

        # 默认必然已匹配某节日
        # 按照长度从长到短匹配，避免重复
        for festival, date in sorted(self.fixed_solar_holiday_dict.items(), key=lambda item: len(item[0]), reverse=True):
            if festival in time_string:
                time_point.month = date[0]
                time_point.day = date[1]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_year_fixed_lunar_festival(self, time_string):
        """ 解析 `农历固定节日` 时间 """
        time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        time_point.year = year if year is not None else self.time_base_handler[0]

        # 默认必然已匹配某节日
        for festival, date in self.fixed_lunar_holiday_dict.items():
            if festival in time_string:
                first_solar_date, _ = self._convert_lunar2solar(
                    [time_point.year, date[0], date[1], -1, -1, -1], False)

                time_point.month = first_solar_date[1]
                time_point.day = first_solar_date[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_limit_year_fixed_lunar_festival(self, time_string):
        """ 解析 `限定年 农历固定节日` 时间 """
        time_point = TimePoint()

        time_point.year, _ = self._normalize_limit_year(
            time_string, self.time_base_handler)

        # 默认必然已匹配某节日
        for festival, date in self.fixed_lunar_holiday_dict.items():
            if festival in time_string:
                first_solar_date, _ = self._convert_lunar2solar(
                    [time_point.year, date[0], date[1], -1, -1, -1], False)

                time_point.month = first_solar_date[1]
                time_point.day = first_solar_date[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        time_definition = self._check_blur(time_string, 'accurate')
        return time_point.handler(), time_point.handler(), 'time_point', time_definition

    def normalize_year_regular_solar_festival(self, time_string):
        """ 解析 `农历规律节日` 时间 """
        time_point = TimePoint()

        year = self._normalize_year(time_string, self.time_base_handler)
        time_point.year = year if year is not None else self.time_base_handler[0]

        # 默认必然已匹配某节日
        for festival, date in self.regular_solar_holiday_dict.items():
            if festival in time_string:
                time_point.month = date['month']
                week_order_num = date['week']
                week_day = date['day']

                one_week = datetime.timedelta(days=7)
                time_base_datetime = TimeParser._convert_handler2datetime(
                    [time_point.year, time_point.month, 1, 0, 0, 0])

                target_day = TimeParser.compute_week_day(
                    time_base_datetime, week_day - 1, flag=True)

                # 向后推周
                for i in range(week_order_num - 1):
                    target_day += one_week

                time_handler = TimeParser._convert_time_base2handler(target_day)
                time_point.day = time_handler[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_limit_year_regular_solar_festival(self, time_string):
        """ 解析 `限定年 农历规律节日` 时间 """
        time_point = TimePoint()

        time_point.year, _ = self._normalize_limit_year(time_string, self.time_base_handler)

        # 默认必然已匹配某节日
        for festival, date in self.regular_solar_holiday_dict.items():
            if festival in time_string:
                time_point.month = date['month']
                week_order_num = date['week']
                week_day = date['day']

                one_week = datetime.timedelta(days=7)
                time_base_datetime = TimeParser._convert_handler2datetime(
                    [time_point.year, time_point.month, 1, 0, 0, 0])

                target_day = TimeParser.compute_week_day(
                    time_base_datetime, week_day - 1, flag=True)

                # 向后推周
                for i in range(week_order_num - 1):
                    target_day += one_week

                time_handler = TimeParser._convert_time_base2handler(target_day)
                time_point.day = time_handler[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_limit_day(self, time_string):
        """ 解析限定性 `日` 时间 """
        limit_day = self.day_patterns[10].search(time_string)

        time_point = TimePoint()

        if limit_day:
            limit_day_string = limit_day.group()
            time_base_datetime = TimeParser._convert_handler2datetime(self.time_base_handler)
            if '大大前' in limit_day_string:
                time_base_datetime -= datetime.timedelta(days=4)
            elif '大前' in limit_day_string:
                time_base_datetime -= datetime.timedelta(days=3)
            elif '前' in limit_day_string:
                time_base_datetime -= datetime.timedelta(days=2)
            elif '昨' in limit_day_string:
                time_base_datetime -= datetime.timedelta(days=1)
            elif '今' in limit_day_string or '同一' in limit_day_string or '当' in limit_day_string:
                pass
            elif '明' in limit_day_string or '次' in limit_day_string:
                time_base_datetime += datetime.timedelta(days=1)
            elif '大大后' in limit_day_string:
                time_base_datetime += datetime.timedelta(days=4)
            elif '大后' in limit_day_string:
                time_base_datetime += datetime.timedelta(days=3)
            elif '后' in limit_day_string:
                time_base_datetime += datetime.timedelta(days=2)
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

            self.map_time_unit(time_point, time_base_datetime, unit=['year', 'month', 'day'])
        else:
            time_point.day = self.time_base_handler[2]

        if time_point.day < 0:
            raise ValueError('The given base time `{}` is illegal.'.format(self.time_base_handler))

        return time_point.handler(), time_point.handler(), 'time_point', 'accurate'

    def normalize_hour_minute_second(self, time_string):
        """ 解析 `时分秒` 时间 """
        day_bias = [0, '弱']

        hour = self.hour_patterns[0].search(time_string)
        minute = self.minute_patterns[0].search(time_string)
        second = self.second_patterns[0].search(time_string)

        time_point = TimePoint()

        if hour:
            hour_string = hour.group(1)
            hour = int(self._char_num2num(hour_string))
            hour_limitation = self.hour_patterns[1].search(time_string)
            if hour_limitation:
                hour_limit_string = hour_limitation.group()
                hour = TimeParser.convert_hour(hour, hour_limit_string)
            if hour == 24:
                hour = 0  # 24 会在 datetime 中报错，即第二天的 0 时
                day_bias = [1, '强']

            time_point.hour = hour

        if minute:
            minute_string = minute.group(1)
            time_point.minute = int(self._char_num2num(minute_string))

        if second:
            second_string = second.group(1)
            time_point.second = int(self._char_num2num(second_string))

        time_definition = self._check_blur(time_string, 'accurate')

        return time_point.handler(), time_point.handler(), 'time_point', time_definition, day_bias

    def normalize_consecutive_blur_hour_pattern(self, time_string):
        """ 解析 `连续模糊 时` 时间  
        
        如：下午七八点
        """
        day_bias = [0, '弱']
        hour = self.hour_patterns[2].search(time_string)
        first_time_point, second_time_point = self._time_point()
        if hour:
            hour_string = hour.group(1)
            first_hour = int(self._char_num2num(hour_string[0]))
            second_hour = int(self._char_num2num(hour_string[-1]))
            hour_limitation = self.hour_patterns[1].search(time_string)
            if hour_limitation:
                hour_limit_string = hour_limitation.group()
                if (5 <= first_hour <= 12) and ('晚' in hour_limit_string or '夜' in hour_limit_string):
                    first_hour += 12
                    second_hour += 12  # 注意此时未判断 第二个时间，仅根据第一个进行判断
                if '中午' in hour_limit_string and first_hour not in [11, 12]:
                    first_hour += 12
                    second_hour += 12
                if '下午' in hour_limit_string and (1 <= first_hour <= 11):
                    first_hour += 12
                    second_hour += 12
            if first_hour == 24:
                first_hour = 0  # 24 会在 datetime 中报错，即第二天的 0 时
                second_hour = 1
                day_bias = [1, '强']

            first_time_point.hour = first_hour
            second_time_point.hour = second_hour

        return first_time_point.handler(), second_time_point.handler(), 'time_span', 'blur', day_bias

    def normalize_num_hour_minute_second(self, time_string):
        """ 解析 `数字（标准格式）时分秒` 时间 """
        time_string = time_string.replace('时', '')

        day_bias = [0, '弱']
        hour_limitation = self.hour_patterns[1].search(time_string)
        if hour_limitation:
            hour_limit_string = hour_limitation.group()
            time_string = time_string.replace(hour_limit_string, '')

        colon_num = len(self.hms_segs.findall(time_string))
        if colon_num == 2:
            hour, minute, second = self.hms_segs.split(time_string)
            if hour_limitation:
                hour = TimeParser.convert_hour(int(hour), hour_limit_string)

        elif colon_num == 1:
            first_int, second_int = self.hms_segs.split(time_string)
            if int(first_int) == 24 and int(second_int) == 0:
                hour = 24
                minute = 0
                second = -1
            elif int(first_int) <= 23:
                hour = int(first_int)
                minute = int(second_int)
                second = -1
                if hour_limitation:
                    hour = TimeParser.convert_hour(hour, hour_limit_string)
            else:
                hour = -1
                minute = int(first_int)
                second = int(second_int)
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        time_point = TimePoint()

        time_point.hour = int(hour)
        time_point.minute = int(minute)
        time_point.second = int(second)

        time_definition = self._check_blur(time_string, 'accurate')

        return time_point.handler(), time_point.handler(), 'time_point', time_definition, day_bias

    @staticmethod
    def convert_hour(h, h_string):
        if (5 <= h <= 12) and ('晚' in h_string or '夜' in h_string):
            h += 12
        if '中午' in h_string and h not in [11, 12]:
            h += 12
        if '下午' in h_string and (1 <= h <= 11):
            h += 12
        return h

    def normalize_hour_limit_minute(self, time_string):
        """ 解析 `时（限定性）分` 时间 """
        day_bias = [0, '弱']
        hour = self.hour_patterns[0].search(time_string)
        hour_limitation = self.hour_patterns[1].search(time_string)
        limit_minute = self.minute_patterns[1].search(time_string)

        time_point = TimePoint()

        if hour:
            hour_string = hour.group(1)
            hour = int(self._char_num2num(hour_string))
            if hour_limitation:
                hour_limit_string = hour_limitation.group()
                hour = TimeParser.convert_hour(hour, hour_limit_string)
            time_point.hour = hour

        if limit_minute:
            limit_minute_string = limit_minute.group()
            if '半' in limit_minute_string:
                time_point.minute = 30
            elif '刻' in limit_minute_string:
                num = self.month_num_pattern.search(limit_minute_string)
                if num:
                    num = int(self._char_num2num(num.group()))
                    if num == 1:
                        time_point.minute = 15
                    elif num == 2:
                        time_point.minute = 30
                    elif num == 3:
                        time_point.minute = 45
                    else:
                        raise ValueError('the given string `{}` is illegal.'.format(time_string))
                else:
                    raise ValueError('the given string `{}` is illegal.'.format(time_string))
            else:
                raise ValueError('the given string `{}` is illegal.'.format(time_string))

        time_definition = self._check_blur(time_string, 'accurate')
        return time_point.handler(), time_point.handler(), 'time_point', time_definition, day_bias

    def normalize_blur_hour(self, time_string):
        """ 解析 `模糊 时段` 时间 """
        day_bias = [0, '弱']
        hour = self.hour_patterns[1].search(time_string)

        first_time_point, second_time_point = self._time_point()
        if hour:
            hour_string = hour.group()
            for item in self.blur_time_info_map:
                if hour_string in item[0]:
                    first_time_point.hour = item[1]
                    second_time_point.hour = item[2]
            if first_time_point.hour == -1:
                raise ValueError('the given string `{}` is illegal'.format(time_string))

        return first_time_point.handler(), second_time_point.handler(), 'time_point', 'blur', day_bias

    @staticmethod
    def _year_completion(year_string, time_base_handler):
        """将两位字符串年份补齐至4位年份，
        依据 time_base 的内容来完成，若 time_base 时间用户未给出而使用了默认当前时间造成错误，
        说明 time_base 未给正确。
        如：
            49年10月1日，应当给出合理的 time_base 为 1949年6月 等日期。
            可补全至  1949年10月1日。
            若 time_base 为当前时刻，造成补全至 2049年10月1日，则存在误差。

        :param year_string:
        :param time_base_handler:
        :return:
        """
        if len(year_string) == 2:
            year_base = str(time_base_handler[0])
            if year_base[:2] in ['17', '18', '19']:
                # 当 year_base 为 20 世纪，则所有时间均为 20 世纪
                return year_base[:2] + year_string
            elif year_base[:2] == '20':
                # 当 year_base 为 21 世纪，而表达年份较大时，需要调整真实世纪
                if int(year_string) > int(year_base[2:]) + 10:
                    century = '19'
                else:
                    century = year_base[:2]
                return century + year_string
            else:
                raise ValueError('maybe the `year` can not be parsed.')
        else:
            return year_string

    def _convert_lunar2solar(self, lunar_time_handler, leap_month):

        def string2handler(datetime_obj):
            return [datetime_obj.year, datetime_obj.month, datetime_obj.day, -1, -1, -1]

        # 默认月份一定不为 -1
        if lunar_time_handler[2] == -1:
            first_solar_time_handler = self.lunar2solar(
                lunar_time_handler[0], lunar_time_handler[1],
                1, leap_month)
            try:
                second_solar_time_handler = self.lunar2solar(
                    lunar_time_handler[0], lunar_time_handler[1],
                    30, leap_month)
            except:
                second_solar_time_handler = self.lunar2solar(
                    lunar_time_handler[0], lunar_time_handler[1],
                    29, leap_month)  # 当农历月无30 天时，按 29天计算

            return string2handler(first_solar_time_handler),\
                string2handler(second_solar_time_handler)

        else:
            solar_time_handler = self.lunar2solar(
                lunar_time_handler[0], lunar_time_handler[1],
                lunar_time_handler[2], leap_month)
            handler = string2handler(solar_time_handler)
            return handler, handler

    def _parse_solar_terms(self, year, solar_term):
        """解析24节气

        :param year: 年份
        :param solar_term: 节气名
        :return:
        """
        if (19 == year // 100) or (2000 == year):
            solar_terms = self._20_century_solar_terms
        else:
            solar_terms = self._21_century_solar_terms

        if solar_term in ['小寒', '大寒', '立春', '雨水']:
            flag_day = int((year % 100) * 0.2422 + solar_terms[solar_term][0]) - int((year % 100 - 1) / 4)
        else:
            flag_day = int((year % 100) * 0.2422 + solar_terms[solar_term][0]) - int((year % 100) / 4)

        # 特殊年份处理
        for special in solar_terms[solar_term][2:]:
            if year == special[0]:
                flag_day += special[1]
                break
        return (solar_terms[solar_term][1]), str(flag_day)
