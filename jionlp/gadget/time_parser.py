# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
TODO:
    1、仍未支持对周期性时间的解析
    2、仍未支持对时间段的解析
    3、时分秒解析中的问题：
        1、9点到半夜1点，其中1点已经属于第二天，需要对其 day 做调整
        2、8点到中午12点，一般来讲，12点指12:00，而非 12:59，与年月日的默认规则有区别
        3、9号半夜2点，一般指第二天的半夜2点，即10号的 02:00
        4、昨晚2点半，究竟指今天2点半，还是昨天的2点半
    4、时间类型的定义、时间表达模糊程度的定义存在误差

"""

import re
import time
import datetime
import traceback

from jionlp import logging
from .money_standardization import MoneyStandardization
from .lunar_solar_date import LunarSolarDate


# `年、月、日`：`2009年5月31日`、`一九九二年四月二十五日`
YEAR_MONTH_DAY_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年)'
    r'((([0]?[1-9]|1[012])|[一二三四五六七八九十]|十[一二])月(份)?)?'
    r'((([012]?\d|3[01])|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号])?|'
    r'((([0]?[1-9]|1[012])|[一二三四五六七八九十]|十[一二])月(份)?)'
    r'((([012]?\d|3[01])|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号])?|'
    r'((([012]?\d|3[01])|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号])')

# `年、季度`：`2018年前三季度`
YEAR_SOLAR_SEASON_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年)?(([第前后头]?[一二三四1-4两]|首)(个)?季度)')

# `年、范围月`：`2018年前三个月`
YEAR_SPAN_MONTH_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年)?'
    r'(([第前后头]([一二两三四五六七八九十]|十[一二]|[1-9]|1[012])|首)(个)?月(份)?)')

# `年、模糊月 时间段`：`1988年末`、`07年暑假`
YEAR_BLUR_MONTH_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年)(年)?(初|[一]开年|伊始|末|尾|终|底)|'
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年)?([上|下]半年|暑假|寒假)')

# `限定月、日`： `下个月9号`
BLUR_MONTH_DAY_PATTERN = re.compile(
    r'([下上](个)?|同)月((([012]?\d|3[01])|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号])?')

# `模糊年、模糊月 时间段`：`1988年末`、`07年暑假`
LIMIT_YEAR_BLUR_MONTH_PATTERN = re.compile(
    '((前|今|明|去|同|当|后|大前|本|次)年)(年)?(初|[一]开年|伊始|末|尾|终|底|[上|下]半年|暑假|寒假)')

# `指代年、月、日`：`今年9月`、`前年9月2日`
LIMIT_YEAR_MONTH_DAY_PATTERN = re.compile(
    r'((前|今|明|去|同|当|后|大前|本|次)年)'
    r'((([0]?[1-9]|1[012])|[一二三四五六七八九十]|十[一二])月(份)?)?'
    r'((([012]?\d|3[01])|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号])?')

# `指代限定年`：`两年后`、`20多年前`
# 1、如若遇到 `4年前的中秋节`，`30多年前的夏天`，则须分为两个时间词汇进行解析。很容易因年份模糊被误识别
# 2、如若遇到 `3万年前`，因返回结果标准化格式无法解析，因而不予支持解析。
# 3、`32年前` 指三十二年前，还是2032年前，存在矛盾，须依据上下文，
#    三十二年前，多见小说、故事等题材，2032年前，多见于官方文档等文书中。因此，考虑官方文档的准确性，
#    默认按照三十二年前处理，除非强调2032年。
BLUR_YEAR_PATTERN = re.compile(
    r'(\d{1,4}|[一二两三四五六七八九十百千]+)[几多]?年(半)?(多)?[以之]?[前后]|'
    r'半年(多)?[以之]?[前|后]|'
    r'几[十百千](多)?年[以之]?[前|后]')

# `世纪、年代`：`20世纪二十年代`
CENTURY_YEAR_PATTERN = re.compile(
    r'(公元(前)?)?(\d{1,2}|((二)?十)?[一二三四五六七八九]|(二)?十|上)世纪((\d0|[一二三四五六七八九]十)年代)?([初中末](期)?|前期|后期)?|'
    r'(\d0|[一二三四五六七八九]十)年代([初中末](期)?|前期|后期)?')

# `农历年、月、日`：二〇一七年农历正月十九
# 强制农历 `日` 必须为汉字，不可为阿拉伯数字，容易引起混淆
LUNAR_YEAR_MONTH_DAY_PATTERN = re.compile(
    # 基本农历判定正则（已废弃）
    # '(农历)?(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    # '(农历)?((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)'
    # '((初|(二)?十|廿)[一二三四五六七八九]|(二|三)十)?|'

    # 2012年9月初十/9月初十/初十
    r'(农历)?(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    r'(农历)?((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)?'
    r'([初廿][一二三四五六七八九十])|'
    
    # 2012年冬月/2012年冬月初十/冬月初十/冬月
    r'(农历)?(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    r'(农历)?(((闰)?[正冬腊]|闰([一二三四五六七八九十]|十[一二]|[1-9]|1[012]))月)((初|(二)?十|廿)[一二三四五六七八九]|[二三]十)?|'
    
    # 强制标明农历，原因在于农历和公历的混淆，非常复杂
    r'(农历)(([12]\d{3}|\d{2}|[一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4})年)'
    r'((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)|'  # 农历二零一二年九月
    
    r'(([12]\d{3}|\d{2}|[一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4})年)'
    r'(农历)((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)|'  # 二零一二年农历九月
    
    r'(农历)((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)'
    r'((初|(二)?十|廿)[一二三四五六七八九]|[二三]?十)|'  # 农历九月初十
    
    r'(农历)((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)|'  # 农历九月

    r'(农历)(([12]\d{3}|\d{2}|[一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4})年)|'  # 农历二〇一二年
    
    r'(农历)((初|(二)?十|廿)[一二三四五六七八九]|[二三]?十)')  # 农历初十

LUNAR_LIMIT_YEAR_MONTH_DAY_PATTERN = re.compile(
    # 非强制也可，根据 `日` 得知为农历日期
    r'(农历)?((前|今|明|去|同|当|后|大前|本|次)年)'
    r'(农历)?((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)?'
    r'([初廿][一二三四五六七八九十])|'  # 2012年9月初十/9月初十/初十
    
    # 非强制也可，根据 `月` 得知为农历日期
    r'((前|今|明|去|同|当|后|大前|本|次)年)'
    r'(农历)?(((闰)?[正冬腊]|闰([一二三四五六七八九十]|十[一二]|[1-9]|1[012]))月)'
    r'((初|(二)?十|廿)[一二三四五六七八九]|[初二三]十)?|'  # 2012年冬月/2012年冬月初十/冬月初十/冬月
    
    # 强制标明农历，原因在于农历和公历的混淆，非常复杂
    r'(农历)((前|今|明|去|同|当|后|大前|本|次)年)|'  # 农历二〇一二年
    r'(农历)((前|今|明|去|同|当|后|大前|本|次)年)'
    r'((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)|'  # 农历二零一二年九月
    r'((前|今|明|去|同|当|后|大前|本|次)年)'
    r'(农历)((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012])月)')  # 二零一二年农历九月


# 年、（农历）季节
YEAR_LUNAR_SEASON_PATTERN = re.compile(
    r'(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    r'[春夏秋冬][季天]|'
    r'(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)[春夏秋冬]')

# 年、节气
YEAR_24ST_PATTERN = re.compile(
    r'(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    r'(立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|立秋|处暑|白露|秋分|'
    r'寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒)')

# 年、月、模糊日（旬）
YEAR_MONTH_XUN_PATTERN = re.compile(
    r'(([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})年)?'
    r'((([0]?[1-9]|1[012])|[一二三四五六七八九十]|十[一二])月(份)?)[上中下]旬')

# 星期 （一般不与年月相关联）
STANDARD_WEEK_DAY_PATTERN = re.compile(
    '(上上|上|下下|下|本|这)?(个)?(周)?(周|星期)[一二三四五六日末天]')

# 星期前后推算
BLUR_WEEK_PATTERN = re.compile(
    '[前后][一两三四五六七八九1-9](个)?(周|星期)|'
    '[一两三四五六七八九1-9](个)?(周|星期)(之)?[前后]|'
    '(上上|上|下下|下|本|这)?(个)?(周|星期)')

# 月、第n个星期k
LIMIT_WEEK_PATTERN = re.compile(
    '([0]?[1-9]|1[012]|[一二三四五六七八九十]|十[一二])月(份)?(的)?'
    '第[1-5一二三四五](个)?(周|星期)[一二三四五六日末天]')

# 公历固定节日
YEAR_FIXED_SOLAR_FESTIVAL_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年|'
    r'((前|今|明|去|同|当|后|大前|本|次)年))?'
    r'((元旦|十一)|(三八|五一|六一|七一|八一|国庆|圣诞)(节)?|'
    r'((三八)?妇女|女神|植树|(五一)?劳动|(五四)?青年|(六一)?儿童|(七一)?建党|(八一)?建军|教师|情人|愚人|万圣|护士)节|'
    r'地球日|三[\.·]?一五)')

# 农历固定节日
YEAR_FIXED_LUNAR_FESTIVAL_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年|'
    r'((前|今|明|去|同|当|后|大前|本|次)年))?'
    r'((春|元宵|填仓|上巳|寒食|清明|浴佛|姑姑|财神|下元|寒衣)节|'
    r'(龙抬头|除夕)|'
    r'(端午|端阳|七夕|中秋|重阳|腊八|中元)(节)?)')

# 公历规律节日
YEAR_REGULAR_SOLAR_FESTIVAL_PATTERN = re.compile(
    r'(([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})年|'
    r'((前|今|明|去|同|当|后|大前|本|次)年))?'
    r'(感恩|母亲|父亲)节')

# 限定性`日`
LIMIT_DAY_PATTERN = re.compile(r'(前|今|明|同一|当|后|大前|大后|昨|次)[天日晚]')

# 时分秒 文字
HOUR_MINUTE_SECOND_PATTERN = re.compile(
    r'(凌晨|清[晨|早]|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)?'
    r'(((十)?[一二三四五六七八九]|[零〇十]|二十[一二三四]?|[01]?\d|2[01234])[时点])'
    r'(((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)分?)?'
    r'(((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)秒)?|'
    
    # 分、秒
    r'(((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)分)'
    r'(((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)秒)?')

# 标准格式`:`分隔时分秒
NUM_HOUR_MINUTE_SECOND_PATTERN = re.compile(
    r'(凌晨|清[晨|早]|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)?'
    r'([01]\d|2[01234]|\d)\:([012345]\d)(\:([012345]\d))?|'
    r'([012345]\d)\:([012345]\d)')

# 模糊性 `时` 段
BLUR_HOUR_PATTERN = re.compile(
    r'(凌晨|清[晨|早]|一(大)?早|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)')

# 限定性 `分`
HOUR_LIMIT_MINUTE_PATTERN = re.compile(
    r'(凌晨|清[晨|早]|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)?'
    r'(((十)?[一二三四五六七八九]|[零〇十]|二十[一二三四]?|[01]?\d|2[01234])[时点])'
    r'([123一二三]刻|半)')


# **** 年 ****
YEAR_1_PATTERN = re.compile('(?<![0-9])[0-9](?=年)')
YEAR_2_PATTERN = re.compile('[0-9]{2}(?=年)')
YEAR_3_PATTERN = re.compile('(?<![0-9])[0-9]{3}(?=年)')
YEAR_4_PATTERN = re.compile(r'([12]?\d{2,3}|[一二三四五六七八九零〇]{2,4})(?=年)')
YEAR_5_PATTERN = re.compile('(前|今|明|去|同|当|后|大前|本|次)(?=年)')
BLUR_YEAR_1_PATTERN = re.compile(r'([12]?\d{1,4}|(?<!几)[一二两三四五六七八九十百千])[几多]?年(半)?(多)?[以之]?[前后]')
BLUR_YEAR_2_PATTERN = re.compile('半年(多)?[以之]?[前后]')
BLUR_YEAR_3_PATTERN = re.compile('几[十百千](多)?年[以之]?[前后]')

LUNAR_YEAR_1_PATTERN = re.compile(r'([一二三四五六七八九零〇]{2}|[一二三四五六七八九零〇]{4}|[12]\d{3}|\d{2})(?=年)')
LUNAR_YEAR_2_PATTERN = re.compile('[甲乙丙丁戊己庚辛壬癸][子丑寅卯辰巳午未申酉戌亥]年')

CENTURY_PATTERN = re.compile(r'(\d{1,2}|((二)?十)?[一二三四五六七八九]|(二)?十|上)(?=世纪)')
DECADE_PATTERN = re.compile(r'(\d0|[一二三四五六七八九]十)(?=年代)')
YEAR_NUM_PATTERN = re.compile('[一二两三四五六七八九十百千0-9]{1,4}')

YEAR_PATTERNS = [YEAR_1_PATTERN, YEAR_2_PATTERN, YEAR_3_PATTERN, YEAR_4_PATTERN,
                 YEAR_5_PATTERN, BLUR_YEAR_1_PATTERN, BLUR_YEAR_2_PATTERN,
                 BLUR_YEAR_3_PATTERN, LUNAR_YEAR_1_PATTERN, LUNAR_YEAR_2_PATTERN]


# **** 月 ****
MONTH_PATTERN = re.compile('([0]?[1-9]|1[012]|[一二三四五六七八九十]|十[一二])月(份)?')
MONTH_NUM_PATTERN = re.compile('[一二两三四五六七八九十0-9]{1,2}')
SPAN_MONTH_PATTERN = re.compile('([第前后头]([一二两三四五六七八九十]|十[一二]|[1-9]|1[012])|首)(个)?月(份)?')
SOLAR_SEASON_PATTERN = re.compile('(([第前后头]?[一二三四1-4两]|首)(个)?季度)')
BLUR_MONTH_1_PATTERN = re.compile('(初|[一]开年|伊始|末|尾|终|底|暑假|寒假|[上下]半年)')
BLUR_MONTH_2_PATTERN = re.compile('([下上](个)?|同)月')
LUNAR_MONTH_PATTERN = re.compile('((闰)?([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1[012]))(?=月)')

MONTH_PATTERNS = [MONTH_PATTERN, SOLAR_SEASON_PATTERN, BLUR_MONTH_1_PATTERN,
                  SPAN_MONTH_PATTERN, LUNAR_MONTH_PATTERN,
                  BLUR_MONTH_2_PATTERN]


# **** 日|星期 ****
DAY_1_PATTERN = re.compile(r'([012]?\d|3[01]|([一二]?十)?[一二三四五六七八九]|(三十)?[一]|[二三]?十)[日|号]')
DAY_2_PATTERN = re.compile(r'(前|今|明|同一|当|后|大前|大后|昨|次)(?=[天日晚])')  # 昨晚9点
LUNAR_DAY_PATTERN = re.compile('((初|(二)?十|廿)[一二三四五六七八九]|[初二三]十)(?!月)')
LUNAR_24ST_PATTERN = re.compile(
    '(立春|雨水|惊蛰|春分|清明|谷雨|立夏|小满|芒种|夏至|小暑|大暑|'
    '立秋|处暑|白露|秋分|寒露|霜降|立冬|小雪|大雪|冬至|小寒|大寒)')
LUNAR_SEASON_PATTERN = re.compile('([春夏秋冬][季天]?)')
XUN_PATTERN = re.compile('[上中下]旬')
WEEK_1_PATTERN = re.compile('[前后][一二两三四五六七八九1-9](个)?(周|星期)')
WEEK_2_PATTERN = re.compile('[一两三四五六七八九1-9](个)?(周|星期)(之)?[前后]')
WEEK_3_PATTERN = re.compile('(上上|上|下下|下|本|这)(个)?(周|星期)')
WEEK_4_PATTERN = re.compile('(周|星期)[一二三四五六日末天]')
WEEK_5_PATTERN = re.compile('第[1-5一二三四五](个)?(周|星期)')


DAY_PATTERNS = [DAY_1_PATTERN, LUNAR_DAY_PATTERN, LUNAR_24ST_PATTERN,
                LUNAR_SEASON_PATTERN, XUN_PATTERN, WEEK_1_PATTERN,
                WEEK_2_PATTERN, WEEK_3_PATTERN, WEEK_4_PATTERN,
                WEEK_5_PATTERN, DAY_2_PATTERN]


# **** 时 ****
HOUR_1_PATTERN = re.compile(
    r'((十)?[一二三四五六七八九]|[零〇十]|二十[一二三四]?|[01]?\d|2[01234])(?=[时|点])')
HOUR_LIMITATION_PATTERN = re.compile(
    r'(凌晨|清[晨|早]|一(大)?早|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)')
HOUR_2_PATTERN = re.compile(r'')

HOUR_PATTERNS = [HOUR_1_PATTERN, HOUR_LIMITATION_PATTERN]


# **** 分 ****
MINUTE_PATTERN = re.compile(
    r'(?<=[时|点])((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)(?=分)?')
LIMIT_MINUTE_PATTERN = re.compile(
    r'(?<=[时|点])([123一二三]刻|半)')

MINUTE_PATTERNS = [MINUTE_PATTERN, LIMIT_MINUTE_PATTERN]


# **** 秒 ****
SECOND_PATTERN = re.compile(
    r'(?<=分)((零|〇|[一二三四五]?十)[一二三四五六七八九]|[二三四五]?十|[012345]?\d)(?=秒)?')

SECOND_PATTERNS = [SECOND_PATTERN, ]


# for TIME_SPAN pattern
FIRST_1_SPAN_PATTERN = re.compile(
    '(?<=(从))(.+)(?=(到|至|以来|起|开始|——|\-|\~))|'
    '(?<=(从))(.+)')
FIRST_2_SPAN_PATTERN = re.compile('(.+)(?=(到|至|以来|起|开始|——|\-|\~))')

SECOND_1_SPAN_PATTERN = re.compile(
    r'(?<=[到至起\-\~])(.+)|(?<=(以来|开始|——))(.+)')
SECOND_2_SPAN_PATTERN = re.compile(
    r'(?<=[到至起\-\~])(.+)(?=([之以]?前))')
SECOND_3_SPAN_PATTERN = re.compile(
    r'^((\d{1,2}|[一二两三四五六七八九十百千]+)[几多]?年(半)?(多)?|半年(多)?|几[十百千](多)?年)'
    r'(?=([之以]?前))')  # 此种匹配容易和 `三年以前` 相互矛盾，因此设置正则


# 公历固定节日
FIXED_SOLAR_HOLIDAY_DICT = {
    # 国内
    '元旦': [1, 1], '妇女节': [3, 8], '女神节': [3, 8], '三八': [3, 8],
    '植树节': [3, 12], '五一': [5, 1], '劳动节': [5, 1], '青年节': [5, 4],
    '六一': [6, 1], '儿童节': [6, 1], '七一': [7, 1], '建党节': [7, 1],
    '八一': [8, 1], '建军节': [8, 1], '教师节': [9, 10], '国庆节': [10, 1],
    '十一': [10, 1],

    # 西方
    '情人节': [2, 14], '愚人节': [4, 1], '万圣节': [10, 31], '圣诞': [12, 25],

    # 特定日
    '地球日': [4, 22], '护士节': [5, 12], '三一五': [3, 15],
    '三.一五': [3, 15], '三·一五': [3, 15],
}

# 农历固定节日
FIXED_LUNAR_HOLIDAY_DICT = {
    '春节': [1, 1], '元宵节': [1, 15], '填仓节': [1, 25], '龙抬头': [2, 2],
    '上巳节': [3, 3], '寒食节': [4, 3], '清明节': [4, 4],  # 清明节有误, 4~6 日
    '浴佛节': [4, 8], '端午': [5, 5], '端阳': [5, 5], '姑姑节': [6, 6],
    '七夕': [7, 7], '中元': [7, 15], '财神节': [7, 22], '中秋': [8, 15],
    '重阳': [9, 9], '下元节': [10, 15], '寒衣节': [10, 1], '腊八': [12, 8],
    '除夕': [12, 30],
}

# 公历规律节日
REGULAR_SOLAR_HOLIDAY_DICT = {
    '母亲节': {'month': 5, 'week': 2, 'day': 7},  # 5 月第二个星期日
    '父亲节': {'month': 6, 'week': 3, 'day': 7},  # 6 月第三个星期日
    '感恩节': {'month': 11, 'week': 4, 'day': 4},  # 11 月第四个星期四

}

# 周期性日期
PERIOD_TIME_PATTERN = re.compile(
    '每(隔)?([一二两三四五六七八九十0-9]+)?(年|(个)?月|日|天|周|(小)?时|分(钟)?|秒(钟)?)')


class TimePoint(object):
    def __init__(self):
        self.year = -1
        self.month = -1
        self.day = -1
        self.hour = -1
        self.minute = -1
        self.second = -1

    def handler(self):
        return [self.year, self.month, self.day,
                self.hour, self.minute, self.second]


class TimeParser(object):
    """将时间表达式转换为标准的时间，
    分为 time_stamp, time_span, time_period, time_delta，
    解析步骤：
        1、将时间做预处理，形成标准可解析字符串
        2、对标准可解析字符串做解析，形成标准的时间

    """
    def __init__(self):
        self.time_point = None
        self.time_base_handler = None
        self.year_char2num_map = {
            '零': '0', '〇': '0', '一': '1', '二': '2', '三': '3', '四': '4',
            '五': '5', '六': '6', '七': '7', '八': '8', '九': '9'}

        self._preprocess()

    def _preprocess(self):
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

        self.money_standardization = MoneyStandardization()

        lunar_solar_date = LunarSolarDate()
        self.lunar2solar = lunar_solar_date.to_solar_date
        self.solar2lunar = lunar_solar_date.to_lunar_date

    def __call__(self, time_string, time_base=time.time()):
        """解析时间字符串。

        :param time_string: 时间字符串，一般从正则或 NER 获取到。
        :param time_base:
        :return:
        """
        # 解析 time_base 为 handler
        self.time_base_handler = TimeParser._convert_time_base2handler(time_base)

        # time_base_handler 中必须有 year，否则依然无法确定具体时间
        legal = TimeParser.check_handler(self.time_base_handler) and (self.time_base_handler[0] != -1)
        if not legal:
            raise ValueError('The given time base `{}` is illegal.'.format(time_base))

        # time_span pattern
        first_time_string, second_time_string = self.parse_span_2_2_point(time_string)
        if first_time_string is not None or second_time_string is not None:
            time_type = 'time_span'
            if first_time_string is not None and second_time_string is None:
                # 默认此时 second handler 为 `至今`
                first_full_time_handler, _, _, blur_time = self.parse_time_point(
                    first_time_string, self.time_base_handler)
                # 默认此时 time_base 大于 first_full_time_handler
                second_full_time_handler = self.time_base_handler
            elif first_time_string is not None and second_time_string is not None:

                first_full_time_handler, _, _, blur_time = self.parse_time_point(
                    first_time_string, self.time_base_handler)
                if second_time_string in ['今', '至今', '现在']:
                    # 默认此时 time_base 大于 first_full_time_handler
                    second_full_time_handler = self.time_base_handler
                else:
                    # self.time_base_handler 依然被 parse... 等函数使用
                    self.time_base_handler = first_full_time_handler
                    _, second_full_time_handler, _, blur_time = self.parse_time_point(
                        second_time_string, first_full_time_handler)
            else:
                # 即 first time string 为空，默认为 time base handler，而second time string 有值
                first_full_time_handler = self.time_base_handler
                _, second_full_time_handler, _, blur_time = self.parse_time_point(
                    second_time_string, self.time_base_handler)

        else:
            # 非 time span，按 time_point 解析
            first_full_time_handler, second_full_time_handler, time_type, \
                blur_time = self.parse_time_point(
                    time_string, self.time_base_handler)

        standard_time_string = TimeParser.time_handler2standard_time(
            first_full_time_handler, second_full_time_handler)

        return {'type': time_type,
                'definition': blur_time,
                'time': [standard_time_string[0], standard_time_string[1]]}

    def parse_span_2_2_point(self, time_string):
        """检测时间字符串，并将其分解为两个 time_point

        :return:
        """
        if FIRST_1_SPAN_PATTERN.search(time_string):
            first_res = FIRST_1_SPAN_PATTERN.search(time_string)
        elif FIRST_2_SPAN_PATTERN.search(time_string):
            first_res = FIRST_2_SPAN_PATTERN.search(time_string)
        else:
            first_res = None

        second_string = None
        if SECOND_1_SPAN_PATTERN.search(time_string):
            second_res = SECOND_1_SPAN_PATTERN.search(time_string)
        elif SECOND_2_SPAN_PATTERN.search(time_string):
            second_res = SECOND_2_SPAN_PATTERN.search(time_string)
        elif SECOND_3_SPAN_PATTERN.search(time_string) is None:
            # second_res = SECOND_3_SPAN_PATTERN.search(time_string)
            if '之前' in time_string[-2:] or '以前' in time_string[-2:]:
                second_string = time_string[:-2]
            elif '前' in time_string[-1:]:
                second_string = time_string[:-1]
            else:
                second_res = None
        else:
            second_res = None

        first_string = None if first_res is None else first_res.group()
        if second_string is None:
            second_string = None if second_res is None else second_res.group()

        return first_string, second_string

    def parse_time_point(self, time_string, time_base_handler):
        """解析时间点字符串，
        # 此处，时间点字符串不一定为 time point 类型，仅仅依据显式 `从……到……` 的正则匹配得到的字符串

        :param time_string: 时间点字符串
        :param time_base_handler:
        :return:
        """
        # time_point pattern & norm_func
        ymd_pattern_norm_funcs = [
            [YEAR_24ST_PATTERN, self.normalize_year_24st],
            [YEAR_LUNAR_SEASON_PATTERN, self.normalize_year_lunar_season],
            [YEAR_MONTH_XUN_PATTERN, self.normalize_year_month_xun],
            [YEAR_SOLAR_SEASON_PATTERN, self.normalize_year_solar_season],
            [LIMIT_WEEK_PATTERN, self.normalize_limit_week],
            [STANDARD_WEEK_DAY_PATTERN, self.normalize_standard_week_day],
            [BLUR_WEEK_PATTERN, self.normalize_blur_week],
            [LIMIT_YEAR_BLUR_MONTH_PATTERN, self.normalize_limit_year_blur_month],
            [BLUR_MONTH_DAY_PATTERN, self.normalize_blur_month_day],
            [YEAR_BLUR_MONTH_PATTERN, self.normalize_year_blur_month],
            [CENTURY_YEAR_PATTERN, self.normalize_century_year],
            [YEAR_SPAN_MONTH_PATTERN, self.normalize_year_span_month],
            [YEAR_FIXED_SOLAR_FESTIVAL_PATTERN, self.normalize_year_fixed_solar_festival],
            [YEAR_FIXED_LUNAR_FESTIVAL_PATTERN, self.normalize_year_fixed_lunar_festival],
            [YEAR_REGULAR_SOLAR_FESTIVAL_PATTERN, self.normalize_year_regular_solar_festival],
            [LUNAR_LIMIT_YEAR_MONTH_DAY_PATTERN, self.normalize_lunar_limit_year_month_day],
            [LIMIT_YEAR_MONTH_DAY_PATTERN, self.normalize_limit_year_month_day],
            [BLUR_YEAR_PATTERN, self.normalize_blur_year],
            [LIMIT_DAY_PATTERN, self.normalize_limit_day],
            [LUNAR_YEAR_MONTH_DAY_PATTERN, self.normalize_lunar_year_month_day],
            [YEAR_MONTH_DAY_PATTERN, self.normalize_year_month_day]
        ]

        hms_pattern_norm_funcs = [
            [HOUR_MINUTE_SECOND_PATTERN, self.normalize_hour_minute_second],
            [NUM_HOUR_MINUTE_SECOND_PATTERN, self.normalize_num_hour_minute_second],
            [HOUR_LIMIT_MINUTE_PATTERN, self.normalize_hour_limit_minute],
            [BLUR_HOUR_PATTERN, self.normalize_blur_hour],
            # [],

        ]

        cur_ymd_func, cur_hms_func = None, None
        cur_ymd_string, cur_hms_string = '', ''
        break_flag = False
        for (ymd_pattern, ymd_func) in ymd_pattern_norm_funcs:
            ymd_string = TimeParser.parse_pattern(time_string, ymd_pattern)
            for (hms_pattern, hms_func) in hms_pattern_norm_funcs:
                hms_string = TimeParser.parse_pattern(time_string, hms_pattern)

                if len(ymd_string) + len(hms_string) > len(cur_ymd_string) + len(cur_hms_string):
                    cur_hms_func = hms_func
                    cur_ymd_func = ymd_func
                    cur_hms_string = hms_string
                    cur_ymd_string = ymd_string
                    # print('##', ymd_string, hms_string, ' orig: ', time_string)

                if ''.join([cur_ymd_string, cur_hms_string]) == time_string:
                    break_flag = True
                    break
                else:
                    continue

            if break_flag:
                break

        # 年月日、时分秒相互对应完整
        if cur_ymd_string != '' and cur_hms_string == '':
            first_time_handler, second_time_handler, time_type, blur_time = \
                cur_ymd_func(cur_ymd_string)
            # print(first_time_handler, second_time_handler, time_type, blur_time)
        elif cur_ymd_string != '' and cur_hms_string != '':
            # 1、若年月日 字符串存在但是 两 handler 不相等，说明 时分秒 字符串无法确定是哪一天，报错。
            # 2、若年月日 字符串存在但是 handler 中 day 不确定，说明 时分秒 字符串无法确定是哪一天，报错。
            ymd_first_time_handler, ymd_second_time_handler, ymd_time_type, ymd_blur_time = \
                cur_ymd_func(cur_ymd_string)
            # print(ymd_first_time_handler, ymd_second_time_handler, ymd_time_type, ymd_blur_time)

            if (ymd_first_time_handler != ymd_second_time_handler)\
                    or ymd_first_time_handler[2] == -1:
                raise ValueError('the string `{}` is illegal, because the hour-min-sec string'
                                 'can NOT be designated to a specific day.'.format(time_string))

            hms_first_time_handler, hms_second_time_handler, hms_time_type, hms_blur_time = \
                cur_hms_func(cur_hms_string)
            # print(hms_first_time_handler, hms_second_time_handler, hms_time_type, hms_blur_time)

            first_time_handler = [max(i, j) for (i, j) in zip(ymd_first_time_handler, hms_first_time_handler)]
            second_time_handler = [max(i, j) for (i, j) in zip(ymd_first_time_handler, hms_second_time_handler)]
            time_type = hms_time_type
            blur_time = hms_blur_time

        elif cur_ymd_string == '' and cur_hms_string != '':
            first_time_handler, second_time_handler, time_type, blur_time = \
                cur_hms_func(cur_hms_string)
            # print(first_time_handler, second_time_handler, time_type, blur_time)
        else:
            raise ValueError('can not parse the string `{}`.'.format(time_string))

        # first_time_handler, second_time_handler, time_type, blur_time = time_handler
        legal = TimeParser.check_handler(first_time_handler)
        if not legal:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        first_full_time_handler = TimeParser.time_completion(
            first_time_handler, time_base_handler)
        second_full_time_handler = TimeParser.time_completion(
            second_time_handler, time_base_handler)

        return first_full_time_handler, second_full_time_handler, time_type, blur_time

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

    def normalize_year_month_day(self, time_string):
        """ 解析 年月日（标准） 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[3]
        month_pattern = MONTH_PATTERNS[0]
        day_pattern = DAY_PATTERNS[0]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)
        day = day_pattern.search(time_string)

        time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年8月，08年6月 这类日期，补全其年份
            if month is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            time_point.year = int(year_string)

        if month is not None:
            month_string = month.group(1)
            time_point.month = self._char_num2num(month_string)

        if day is not None:
            day_string = day.group(1)
            time_point.day = self._char_num2num(day_string)

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_solar_season(self, time_string):
        """ 解析 年/季度(公历) 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[3]
        month_pattern = MONTH_PATTERNS[1]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年8月，08年6月 这类日期，补全其年份
            if month is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            first_time_point.year = int(year_string)
            second_time_point.year = int(year_string)
        if month is not None:
            solar_season = month.group()
            if '1' in solar_season or '一' in solar_season or '首' in solar_season:
                if '第' in solar_season:
                    first_month = 1
                    second_month = 3
                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 3
                elif '后' in solar_season:
                    first_month = 10
                    second_month = 12
                else:
                    first_month = 1
                    second_month = 3
            elif '2' in solar_season or '二' in solar_season:
                if '第' in solar_season:
                    first_month = 4
                    second_month = 6
                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 6
                elif '后' in solar_season:
                    first_month = 7
                    second_month = 12
                else:
                    first_month = 4
                    second_month = 6
            elif '3' in solar_season or '三' in solar_season:
                if '第' in solar_season:
                    first_month = 7
                    second_month = 9
                elif '前' in solar_season or '头' in solar_season:
                    first_month = 1
                    second_month = 9
                elif '后' in solar_season:
                    first_month = 4
                    second_month = 12
                else:
                    first_month = 7
                    second_month = 9
            elif '4' in solar_season or '四' in solar_season:
                # 4季度、第四季度
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

            first_time_point.month = first_month
            second_time_point.month = second_month

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'accurate'

    def normalize_year_span_month(self, time_string):
        """ 解析 年/前n个月 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[3]
        month_pattern = MONTH_PATTERNS[3]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)
        # print(year, month)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年8月，08年6月 这类日期，补全其年份
            if month is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            first_time_point.year = int(year_string)
            second_time_point.year = int(year_string)

        if month is not None:
            span_month = month.group()
            if '首' not in span_month:
                month_num = MONTH_NUM_PATTERN.search(span_month)
                month_num = self._char_num2num(month_num.group())

            if '前' in span_month or '头' in span_month:
                first_month = 1
                second_month = month_num
            elif '后' in span_month:
                first_month = 13 - month_num
                second_month = 12
            elif '第' in span_month:
                first_month = month_num
                second_month = month_num
            elif '首' in span_month:
                first_month = 1
                second_month = 1
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

            first_time_point.month = first_month
            second_time_point.month = second_month

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'accurate'

    def normalize_year_blur_month(self, time_string):
        """ 解析 年/模糊月份 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[3]
        month_pattern = MONTH_PATTERNS[2]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年8月，08年6月 这类日期，补全其年份
            if month is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            first_time_point.year = int(year_string)
            second_time_point.year = int(year_string)

        if month is not None:
            blur_month = month.group()
            # '初|[一]开年|末|尾|终|底|暑假|寒假|[上|下]半年|'
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
            elif '暑假' in blur_month:  # 暑假一般在 7，8月，非准确时间
                first_month = 7
                second_month = 8
            elif '寒假' in blur_month:  # 寒假一般在 2月，非准确时间
                first_month = 2
                second_month = 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

            first_time_point.month = first_month
            second_time_point.month = second_month

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'blur'

    def normalize_limit_year_blur_month(self, time_string):
        """ 解析 限制年/模糊月份 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[4]
        month_pattern = MONTH_PATTERNS[2]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            if '大前' in year_string:
                first_time_point.year = self.time_base_handler[0] - 3
                second_time_point.year = self.time_base_handler[0] - 3
            elif '前' in year_string:
                first_time_point.year = self.time_base_handler[0] - 2
                second_time_point.year = self.time_base_handler[0] - 2
            elif '去' in year_string:
                first_time_point.year = self.time_base_handler[0] - 1
                second_time_point.year = self.time_base_handler[0] - 1
            elif '今' in year_string or '同' in time_string or '当' in time_string or '本' in time_string:
                first_time_point.year = self.time_base_handler[0]
                second_time_point.year = self.time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                first_time_point.year = self.time_base_handler[0] + 1
                second_time_point.year = self.time_base_handler[0] + 1
            elif '后' in year_string:
                first_time_point.year = self.time_base_handler[0] + 2
                second_time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        if month is not None:
            blur_month = month.group()
            # '初|[一]开年|末|尾|终|底|暑假|寒假|[上|下]半年|'
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
            elif '暑假' in blur_month:  # 暑假一般在 7，8月，非准确时间
                first_month = 7
                second_month = 8
            elif '寒假' in blur_month:  # 寒假一般在 2月，非准确时间
                first_month = 2
                second_month = 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

            first_time_point.month = first_month
            second_time_point.month = second_month

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'blur'

    def normalize_blur_month_day(self, time_string):
        """ 解析 限制年/模糊月份 时间

        :return:
        """
        month = MONTH_PATTERNS[5].search(time_string)
        day = DAY_PATTERNS[0].search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        # 此处无年份，按照 time_base 获取
        first_time_point.year = self.time_base_handler[0]
        second_time_point.year = self.time_base_handler[0]

        if month is not None:
            month_string = month.group()
            if '上' in month_string:
                if self.time_base_handler[1] == 1:
                    first_time_point.year -= 1
                    second_time_point.year -= 1
                    first_time_point.month = 12
                    second_time_point.month = 12
                else:
                    first_time_point.month = self.time_base_handler[1] - 1
                    second_time_point.month = self.time_base_handler[1] - 1
            elif '下' in month_string:
                if self.time_base_handler[1] == 12:
                    first_time_point.year += 1
                    second_time_point.year += 1
                    first_time_point.month = 1
                    second_time_point.month = 1
                else:
                    first_time_point.month = self.time_base_handler[1] + 1
                    second_time_point.month = self.time_base_handler[1] + 1
            elif '同' in month_string:
                first_time_point.year = self.time_base_handler[1]
                second_time_point.year = self.time_base_handler[1]
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        if day:
            day_string = day.group(1)
            first_time_point.day = self._char_num2num(day_string)
            second_time_point.day = self._char_num2num(day_string)

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span',\
            'blur' if first_time_handler[2] < 0 else 'accurate'

    def normalize_century_year(self, time_string):
        """ 解析 年/模糊月份 时间

        :return:
        """
        century = CENTURY_PATTERN.search(time_string)
        decade = DECADE_PATTERN.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if '公元前' in time_string:
            christ_era = False
        else:
            christ_era = True

        if century is not None:
            # 上世纪确指 20世纪
            if '上世纪' in time_string:
                century = 20
            else:
                century = self._char_num2num(century.group())
            # print(century)

        if decade is not None:
            decade = self._char_num2num(decade.group())
            # print(decade)

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

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'blur'

    def normalize_limit_year_month_day(self, time_string):
        """ 解析 指代年、月、日 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[4]
        month_pattern = MONTH_PATTERNS[0]
        day_pattern = DAY_PATTERNS[0]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)
        day = day_pattern.search(time_string)

        time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            if '大前' in year_string:
                time_point.year = self.time_base_handler[0] - 3
            elif '前' in year_string:
                time_point.year = self.time_base_handler[0] - 2
            elif '去' in year_string:
                time_point.year = self.time_base_handler[0] - 1
            elif '今' in year_string or '同' in time_string or '当' in time_string or '本' in time_string:
                time_point.year = self.time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                time_point.year = self.time_base_handler[0] + 1
            elif '后' in year_string:
                time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        if month is not None:
            month_string = month.group(1)
            time_point.month = self._char_num2num(month_string)

        if day is not None:
            day_string = day.group(1)
            time_point.day = self._char_num2num(day_string)

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_span', 'accurate'

    def normalize_blur_year(self, time_string):
        """ 解析 指代年、月、日 时间

        :return:
        """
        blur_year_1_pattern = YEAR_PATTERNS[5]
        blur_year_2_pattern = YEAR_PATTERNS[6]
        blur_year_3_pattern = YEAR_PATTERNS[7]

        blur_year_1 = blur_year_1_pattern.search(time_string)
        blur_year_2 = blur_year_2_pattern.search(time_string)
        blur_year_3 = blur_year_3_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        # 月份针对 半年设定
        first_month = -1
        second_month = -1

        if blur_year_1 is not None:
            year_num = YEAR_NUM_PATTERN.search(time_string)
            year_num = self._char_num2num(year_num.group())

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

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()
        # if time_string == '一年半以前':
        #     print(first_time_handler)
        return first_time_handler, second_time_handler, 'time_span', 'blur'

    def normalize_lunar_year_month_day(self, time_string):
        """ 解析 农历年、月、日 时间

        :return:
        """
        lunar_year_1_pattern = YEAR_PATTERNS[8]
        lunar_month_pattern = MONTH_PATTERNS[4]
        lunar_day_pattern = DAY_PATTERNS[1]

        lunar_year_1 = lunar_year_1_pattern.search(time_string)
        lunar_month = lunar_month_pattern.search(time_string)
        lunar_day = lunar_day_pattern.search(time_string)

        lunar_time_point = TimePoint()

        if lunar_year_1 is not None:
            lunar_year_string = lunar_year_1.group(1)
            # 针对汉字年份进行转换
            lunar_year_string = self._char_year2num(lunar_year_string)

            # 针对 13年八月，08年六月 这类日期，补全其年份
            if lunar_month is not None:
                if len(lunar_year_string) == 2:
                    lunar_year_string = TimeParser._year_completion(
                        lunar_year_string, self.time_base_handler)

            lunar_time_point.year = int(lunar_year_string)

        # else:
        #     raise ValueError('There is a bug for `{}`.'.format(time_string))

        leap_month = False
        if lunar_month:
            # '([正一二三四五六七八九十冬腊]|十[一二]|[1-9]|1(0|1|2))(?=月)'
            lunar_month_string = lunar_month.group(1)
            if '闰' in lunar_month_string:
                leap_month = True
            lunar_month_string = lunar_month_string\
                .replace('正', '一').replace('冬', '十一').replace('腊', '十二').replace('闰', '')
            lunar_month_string = self._char_num2num(lunar_month_string)

            lunar_time_point.month = lunar_month_string

        if lunar_day:
            # (初|(二)?十|廿)[一二三四五六七八九]|(二|三)?十)?
            lunar_day_string = lunar_day.group(0)
            lunar_day_string = lunar_day_string\
                .replace('初', '').replace('廿', '二十')
            lunar_day_string = self._char_num2num(lunar_day_string)

            lunar_time_point.day = lunar_day_string

        lunar_time_handler = lunar_time_point.handler()

        # 对农历日期的补全
        lunar_time_handler = TimeParser.time_completion(lunar_time_handler, self.time_base_handler)

        first_time_handler, second_time_handler = self._convert_lunar2solar(
            lunar_time_handler, leap_month=leap_month)

        return first_time_handler, second_time_handler, 'time_point', 'accurate'

    def normalize_lunar_limit_year_month_day(self, time_string):
        """ 解析 农历限定年、月、日 时间

        :return:
        """
        lunar_year_pattern = YEAR_PATTERNS[4]
        lunar_month_pattern = MONTH_PATTERNS[4]
        lunar_day_pattern = DAY_PATTERNS[1]

        lunar_year = lunar_year_pattern.search(time_string)
        lunar_month = lunar_month_pattern.search(time_string)
        lunar_day = lunar_day_pattern.search(time_string)

        lunar_time_point = TimePoint()

        if lunar_year:
            lunar_year_string = lunar_year.group(1)
            if '大前' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0] - 3
            elif '前' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0] - 2
            elif '去' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0] - 1
            elif '今' in lunar_year_string or '同' in lunar_year_string or '当' in lunar_year_string or '本' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0]
            elif '明' in lunar_year_string or '次' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0] + 1
            elif '后' in lunar_year_string:
                lunar_time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        else:
            raise ValueError('There is a bug for `{}`.'.format(time_string))

        leap_month = False
        if lunar_month:
            lunar_month_string = lunar_month.group(1)
            if '闰' in lunar_month_string:
                leap_month = True
            lunar_month_string = lunar_month_string\
                .replace('正', '一').replace('冬', '十一').replace('腊', '十二').replace('闰', '')
            lunar_month_string = self._char_num2num(lunar_month_string)

            lunar_time_point.month = lunar_month_string

        if lunar_day:
            # (初|(二)?十|廿)[一二三四五六七八九]|(二|三)?十)?
            lunar_day_string = lunar_day.group(0)
            lunar_day_string = lunar_day_string\
                .replace('初', '').replace('廿', '二十')
            lunar_day_string = self._char_num2num(lunar_day_string)

            lunar_time_point.day = lunar_day_string

        lunar_time_handler = lunar_time_point.handler()

        # 对农历日期的补全
        lunar_time_handler = TimeParser.time_completion(lunar_time_handler, self.time_base_handler)

        first_time_handler, second_time_handler = self._convert_lunar2solar(
            lunar_time_handler, leap_month=leap_month)

        return first_time_handler, second_time_handler, 'time_point', 'accurate'

    def normalize_year_24st(self, time_string):
        """ 解析 `年、节气`

        :return:
        """
        year_pattern = YEAR_PATTERNS[8]
        _24st_pattern = DAY_PATTERNS[2]

        year = year_pattern.search(time_string)
        _24st = _24st_pattern.search(time_string)

        time_point = TimePoint()

        if year:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年八月，08年六月 这类日期，补全其年份
            if _24st is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            time_point.year = int(year_string)

        if _24st:
            _24st_string = _24st.group()
            month_string, day_string = self._parse_solar_terms(time_point.year, _24st_string)
            time_point.month = int(month_string)
            time_point.day = int(day_string)
            if _24st_string in ['小寒', '大寒']:
                time_point.year += 1

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_lunar_season(self, time_string):
        """ 解析 年/季节(农历) 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[8]
        season_pattern = DAY_PATTERNS[3]

        year = year_pattern.search(time_string)
        season = season_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年春，08年冬天 这类日期，补全其年份
            if season is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            first_time_point.year = int(year_string)
            second_time_point.year = int(year_string)
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

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'accurate'

    def normalize_year_month_xun(self, time_string):
        """ 解析 `年、月、旬` 时间

        :return:
        """
        year_pattern = YEAR_PATTERNS[8]
        month_pattern = MONTH_PATTERNS[0]
        xun_pattern = DAY_PATTERNS[4]

        year = year_pattern.search(time_string)
        month = month_pattern.search(time_string)
        xun = xun_pattern.search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if year is not None:
            year_string = year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            # 针对 13年8月，08年6月 这类日期，补全其年份
            if month is not None:
                if len(year_string) == 2:
                    year_string = TimeParser._year_completion(
                        year_string, self.time_base_handler)

            first_time_point.year = int(year_string)
            second_time_point.year = int(year_string)

        if month:
            month_string = month.group(1)
            month_string = self._char_num2num(month_string)
            first_time_point.month = month_string
            second_time_point.month = month_string

        if xun:
            xun_string = xun.group()
            if '上旬' in xun_string:
                first_day = 1
                second_day = 10
            elif '中旬' in xun_string:
                first_day = 11
                second_day = 20
            elif '下旬' in xun_string:
                first_day = 11
                second_day = -1
            else:
                raise ValueError()
            first_time_point.day = int(first_day)
            second_time_point.day = int(second_day)

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_span', 'accurate'

    def normalize_standard_week_day(self, time_string):
        """ 解析 `标准星期 N` 时间

        :return:
        """
        week = DAY_PATTERNS[7].search(time_string)
        week_day = DAY_PATTERNS[8].search(time_string)

        one_week = datetime.timedelta(days=7)
        time_base_datetime = TimeParser._convert_handler2datetime(
            self.time_base_handler)

        if week:
            week_string = week.group()
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

        def compute_week_day(cur_day, target_week_day):
            """ 同一个星期内，获取目标星期 N 日期
            cur_day: datetime obj
            target_week_day: int (0-6)
            """
            one_day = datetime.timedelta(days=1)
            cur_week_day = cur_day.weekday()
            delta = cur_week_day - target_week_day
            if delta == 0:
                return cur_day
            elif delta > 0:
                for _ in range(delta):
                    cur_day -= one_day
            elif delta < 0:
                for _ in range(abs(delta)):
                    cur_day += one_day

            return cur_day

        if week_day:
            week_day_string = week_day.group()
            if '一' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 0)
            elif '二' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 1)
            elif '三' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 2)
            elif '四' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 3)
            elif '五' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 4)
            elif '六' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 5)
            elif '天' in week_day_string or '末' in week_day_string or '日' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 6)
            else:
                raise ValueError

        time_handler = TimeParser._convert_time_base2handler(target_day)
        time_point = TimePoint()
        time_point.year = time_handler[0]
        time_point.month = time_handler[1]
        time_point.day = time_handler[2]
        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_blur_week(self, time_string):
        """ 解析 `前后 N 星期` 时间

        :return:
        """
        week_1 = DAY_PATTERNS[5].search(time_string)
        week_2 = DAY_PATTERNS[6].search(time_string)
        week_3 = DAY_PATTERNS[7].search(time_string)

        one_week = datetime.timedelta(days=7)
        time_base_datetime = TimeParser._convert_handler2datetime(
            self.time_base_handler)

        def compute_week_day(cur_day, target_week_day):
            """ 同一个星期内，获取目标星期 N 日期
            cur_day: datetime obj
            target_week_day: int (0-6)
            """
            one_day = datetime.timedelta(days=1)
            cur_week_day = cur_day.weekday()
            delta = cur_week_day - target_week_day
            if delta == 0:
                return cur_day
            elif delta > 0:
                for _ in range(delta):
                    cur_day -= one_day
            elif delta < 0:
                for _ in range(abs(delta)):
                    cur_day += one_day

            return cur_day

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if week_1:
            week_string = week_1.group()
            week_num = MONTH_NUM_PATTERN.search(week_string)
            if week_num:
                week_num = self._char_num2num(week_num.group())
            else:
                week_num = 0

            if '前' in week_string:
                for _ in range(week_num):
                    time_base_datetime -= one_week
                first_time_datetime = compute_week_day(time_base_datetime, 0)
                first_time_point.year = first_time_datetime.year
                first_time_point.month = first_time_datetime.month
                first_time_point.day = first_time_datetime.day
                first_time_handler = first_time_point.handler()
                second_time_handler = self.time_base_handler
            elif '后' in week_string:
                for _ in range(week_num):
                    time_base_datetime += one_week
                second_time_datetime = compute_week_day(time_base_datetime, 6)

                second_time_point.year = second_time_datetime.year
                second_time_point.month = second_time_datetime.month
                second_time_point.day = second_time_datetime.day
                second_time_handler = second_time_point.handler()
                first_time_handler = self.time_base_handler
            else:
                raise ValueError('the time string `{}` is illegal.'.format(time_string))

        elif week_2:
            week_string = week_2.group()
            week_num = MONTH_NUM_PATTERN.search(week_string)
            if week_num:
                week_num = self._char_num2num(week_num.group())
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

            first_time_datetime = compute_week_day(time_base_datetime, 0)
            first_time_point.year = first_time_datetime.year
            first_time_point.month = first_time_datetime.month
            first_time_point.day = first_time_datetime.day
            first_time_handler = first_time_point.handler()

            second_time_datetime = compute_week_day(time_base_datetime, 6)
            second_time_point.year = second_time_datetime.year
            second_time_point.month = second_time_datetime.month
            second_time_point.day = second_time_datetime.day
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

            first_time_datetime = compute_week_day(time_base_datetime, 0)
            first_time_point.year = first_time_datetime.year
            first_time_point.month = first_time_datetime.month
            first_time_point.day = first_time_datetime.day
            first_time_handler = first_time_point.handler()

            second_time_datetime = compute_week_day(time_base_datetime, 6)
            second_time_point.year = second_time_datetime.year
            second_time_point.month = second_time_datetime.month
            second_time_point.day = second_time_datetime.day
            second_time_handler = second_time_point.handler()

        else:
            raise ValueError('the given time string is illegal.\n{}'.format(
                traceback.format_exc()))

        return first_time_handler, second_time_handler, 'time_point', 'blur'

    def normalize_limit_week(self, time_string):
        """ 解析 `前后 N 星期` 时间

        :return:
        """

        month = MONTH_PATTERNS[0].search(time_string)
        week_res = DAY_PATTERNS[9].search(time_string)
        week_day = DAY_PATTERNS[8].search(time_string)

        time_point = TimePoint()

        if month:
            month_string = month.group()
            month_num = MONTH_NUM_PATTERN.search(month_string)
            if month_num:
                month_num = self._char_num2num(month_num.group())
                time_point.month = month_num
            else:
                raise ValueError('month string is not in `{}`.'.format(time_string))
        else:
            raise ValueError('month string is not in `{}`.'.format(time_string))

        if week_res and week_day:
            week_res = week_res.group()
            week_order_num = MONTH_NUM_PATTERN.search(week_res)
            week_order_num = self._char_num2num(week_order_num.group())
            week_day_string = week_day.group()

            one_week = datetime.timedelta(days=7)

            # 补全年份
            time_point.year = self.time_base_handler[0]

            time_base_datetime = TimeParser._convert_handler2datetime(
                [time_point.year, time_point.month, 1, 0, 0, 0])

            def compute_week_day(cur_day, target_week_day):
                """ 从1 号开始计算，向后寻找对应的星期 N
                cur_day: datetime obj
                target_week_day: int (0-6)
                """
                one_day = datetime.timedelta(days=1)
                cur_week_day = cur_day.weekday()
                delta = cur_week_day - target_week_day
                if delta == 0:
                    return cur_day
                elif delta > 0:
                    for _ in range(7 - delta):
                        cur_day += one_day
                elif delta < 0:
                    for _ in range(abs(delta)):
                        cur_day += one_day

                return cur_day

            if '一' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 0)
            elif '二' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 1)
            elif '三' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 2)
            elif '四' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 3)
            elif '五' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 4)
            elif '六' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 5)
            elif '天' in week_day_string or '末' in week_day_string or '日' in week_day_string:
                target_day = compute_week_day(time_base_datetime, 6)
            else:
                raise ValueError('`星期{}` is illegal.'.format(week_day_string))

            # 向后推周
            for i in range(week_order_num - 1):
                target_day += one_week

            time_handler = TimeParser._convert_time_base2handler(target_day)
            time_point.day = time_handler[2]
            time_handler = time_point.handler()
        else:
            raise ValueError('th given string `{}` is illegal.'.format(time_string))

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_fixed_solar_festival(self, time_string):
        """ 解析 `公历固定节日` 时间

        :return:
        """
        standard_year = YEAR_PATTERNS[3].search(time_string)
        limit_year = YEAR_PATTERNS[4].search(time_string)

        time_point = TimePoint()

        if standard_year:
            year_string = standard_year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            if len(year_string) == 2:
                year_string = TimeParser._year_completion(
                    year_string, self.time_base_handler)
            time_point.year = int(year_string)

        elif limit_year:
            year_string = limit_year.group(1)
            if '大前' in year_string:
                time_point.year = self.time_base_handler[0] - 3
            elif '前' in year_string:
                time_point.year = self.time_base_handler[0] - 2
            elif '去' in year_string:
                time_point.year = self.time_base_handler[0] - 1
            elif '今' in year_string or '同' in time_string or '当' in time_string or '本' in time_string:
                time_point.year = self.time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                time_point.year = self.time_base_handler[0] + 1
            elif '后' in year_string:
                time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        else:
            time_point.year = self.time_base_handler[0]

        # 默认必然已匹配某节日
        for festival, date in FIXED_SOLAR_HOLIDAY_DICT.items():
            if festival in time_string:
                time_point.month = date[0]
                time_point.day = date[1]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_fixed_lunar_festival(self, time_string):
        """ 解析 `农历固定节日` 时间

        :return:
        """
        standard_year = YEAR_PATTERNS[3].search(time_string)
        limit_year = YEAR_PATTERNS[4].search(time_string)

        time_point = TimePoint()

        if standard_year:
            year_string = standard_year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            if len(year_string) == 2:
                year_string = TimeParser._year_completion(
                    year_string, self.time_base_handler)
            time_point.year = int(year_string)

        elif limit_year:
            year_string = limit_year.group(1)
            if '大前' in year_string:
                time_point.year = self.time_base_handler[0] - 3
            elif '前' in year_string:
                time_point.year = self.time_base_handler[0] - 2
            elif '去' in year_string:
                time_point.year = self.time_base_handler[0] - 1
            elif '今' in year_string or '同' in time_string or '当' in time_string or '本' in time_string:
                time_point.year = self.time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                time_point.year = self.time_base_handler[0] + 1
            elif '后' in year_string:
                time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        else:
            time_point.year = self.time_base_handler[0]

        # 默认必然已匹配某节日
        for festival, date in FIXED_LUNAR_HOLIDAY_DICT.items():
            if festival in time_string:
                first_solar_date, _ = self._convert_lunar2solar(
                    [time_point.year, date[0], date[1], -1, -1, -1], False)

                time_point.month = first_solar_date[1]
                time_point.day = first_solar_date[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_year_regular_solar_festival(self, time_string):
        """ 解析 `农历固定节日` 时间

        :return:
        """
        standard_year = YEAR_PATTERNS[3].search(time_string)
        limit_year = YEAR_PATTERNS[4].search(time_string)

        time_point = TimePoint()

        if standard_year:
            year_string = standard_year.group(1)
            # 针对汉字年份进行转换
            year_string = self._char_year2num(year_string)

            if len(year_string) == 2:
                year_string = TimeParser._year_completion(
                    year_string, self.time_base_handler)
            time_point.year = int(year_string)

        elif limit_year:
            year_string = limit_year.group(1)
            if '大前' in year_string:
                time_point.year = self.time_base_handler[0] - 3
            elif '前' in year_string:
                time_point.year = self.time_base_handler[0] - 2
            elif '去' in year_string:
                time_point.year = self.time_base_handler[0] - 1
            elif '今' in year_string or '同' in time_string or '当' in time_string or '本' in time_string:
                time_point.year = self.time_base_handler[0]
            elif '明' in year_string or '次' in year_string:
                time_point.year = self.time_base_handler[0] + 1
            elif '后' in year_string:
                time_point.year = self.time_base_handler[0] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        else:
            time_point.year = self.time_base_handler[0]

        # 默认必然已匹配某节日
        for festival, date in REGULAR_SOLAR_HOLIDAY_DICT.items():
            if festival in time_string:
                time_point.month = date['month']
                week_order_num = date['week']
                week_day = date['day']

                one_week = datetime.timedelta(days=7)
                time_base_datetime = TimeParser._convert_handler2datetime(
                    [time_point.year, time_point.month, 1, 0, 0, 0])

                def compute_week_day(cur_day, target_week_day):
                    """ 从1 号开始计算，向后寻找对应的星期 N
                    cur_day: datetime obj
                    target_week_day: int (0-6)
                    """
                    one_day = datetime.timedelta(days=1)
                    cur_week_day = cur_day.weekday()
                    delta = cur_week_day - target_week_day
                    if delta == 0:
                        return cur_day
                    elif delta > 0:
                        for _ in range(7 - delta):
                            cur_day += one_day
                    elif delta < 0:
                        for _ in range(abs(delta)):
                            cur_day += one_day

                    return cur_day

                target_day = compute_week_day(time_base_datetime, week_day - 1)

                # 向后推周
                for i in range(week_order_num - 1):
                    target_day += one_week

                time_handler = TimeParser._convert_time_base2handler(target_day)
                time_point.day = time_handler[2]
                break

        if time_point.day < 0:
            raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_limit_day(self, time_string):
        """ 解析限定性 `日` 时间

        :return:
        """
        limit_day = DAY_PATTERNS[10].search(time_string)

        time_point = TimePoint()
        time_point.year = self.time_base_handler[0]
        time_point.month = self.time_base_handler[1]

        if limit_day:
            limit_day_string = limit_day.group()
            # (前|今|明|同一|当|后|大前|大后|昨)天'
            if '大前' in limit_day_string:
                time_point.day = self.time_base_handler[2] - 3
            elif '前' in limit_day_string:
                time_point.day = self.time_base_handler[2] - 2
            elif '昨' in limit_day_string:
                time_point.day = self.time_base_handler[2] - 1
            elif '今' in limit_day_string or '同一' in limit_day_string or '当' in limit_day_string:
                time_point.day = self.time_base_handler[2]
            elif '明' in limit_day_string or '次' in limit_day_string:
                time_point.day = self.time_base_handler[2] + 1
            elif '大后' in limit_day_string:
                time_point.day = self.time_base_handler[2] + 3
            elif '后' in limit_day_string:
                time_point.day = self.time_base_handler[2] + 2
            else:
                raise ValueError('The given time string `{}` is illegal.'.format(time_string))

        else:
            time_point.day = self.time_base_handler[2]

        if time_point.day < 0:
            raise ValueError('The given base time `{}` is illegal.'.format(self.time_base_handler))

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_hour_minute_second(self, time_string):
        """ 解析 `时分秒` 时间

        :return:
        """
        hour = HOUR_PATTERNS[0].search(time_string)
        minute = MINUTE_PATTERNS[0].search(time_string)
        second = SECOND_PATTERNS[0].search(time_string)

        time_point = TimePoint()

        if hour:
            hour_string = hour.group(1)
            hour = self._char_num2num(hour_string)
            # (凌晨|清[晨|早]|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)
            hour_limitation = HOUR_PATTERNS[1].search(time_string)
            if hour_limitation:
                hour_limit_string = hour_limitation.group()
                if (7 <= hour <= 12) and ('晚' in hour_limit_string or '夜' in hour_limit_string):
                    hour += 12
                if '中午' in hour_limit_string and hour not in [11, 12]:
                    hour += 12
                if '下午' in hour_limit_string and (1 <= hour <= 6):
                    hour += 12
            if hour == 24:
                hour = 23  # 24 会在 datetime 中报错，即第二天的 0 时，与 day 日期连用的方式还没做

            time_point.hour = hour

        if minute:
            minute_string = minute.group(1)
            time_point.minute = self._char_num2num(minute_string)

        if second:
            second_string = second.group(1)
            time_point.second = self._char_num2num(second_string)

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    @staticmethod
    def normalize_num_hour_minute_second(time_string):
        """ 解析 `（标准格式）时分秒` 时间

        :return:
        """
        hour_limitation = HOUR_PATTERNS[1].search(time_string)
        if hour_limitation:
            hour_limit_string = hour_limitation.group()
            time_string = time_string.replace(hour_limit_string, '')

        def convert_hour(h, h_string):
            if (7 <= h <= 12) and ('晚' in h_string or '夜' in h_string):
                h += 12
            if '中午' in h_string and h not in [11, 12]:
                h += 12
            if '下午' in h_string and (1 <= h <= 6):
                h += 12
            return h

        colon_num = time_string.count(':')
        if colon_num == 2:
            hour, minute, second = time_string.split(':')
            if hour_limitation:
                hour = convert_hour(hour, hour_limit_string)

        elif colon_num == 1:
            first_int, second_int = time_string.split(':')
            if int(first_int) == 24 and int(second_int) == 0:
                hour = 24
                minute = 0
                second = -1
            elif int(first_int) <= 23:
                hour = int(first_int)
                minute = int(second_int)
                second = -1
                if hour_limitation:
                    hour = convert_hour(hour, hour_limit_string)
            else:
                hour = -1
                minute = int(first_int)
                second = int(second_int)
        else:
            raise ValueError('the given string `{}` is illegal.'.format(time_string))

        time_point = TimePoint()

        time_point.hour = hour
        time_point.minute = minute
        time_point.second = second

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    def normalize_hour_limit_minute(self, time_string):
        """ 解析 `时（限定性）分` 时间

        :return:
        """
        hour = HOUR_PATTERNS[0].search(time_string)
        hour_limitation = HOUR_PATTERNS[1].search(time_string)
        limit_minute = MINUTE_PATTERNS[1].search(time_string)

        def convert_hour(h, h_string):
            if (7 <= h <= 12) and ('晚' in h_string or '夜' in h_string):
                h += 12
            if '中午' in h_string and h not in [11, 12]:
                h += 12
            if '下午' in h_string and (1 <= h <= 6):
                h += 12
            return h

        time_point = TimePoint()

        if hour:
            hour_string = hour.group(1)
            hour = self._char_num2num(hour_string)
            if hour_limitation:
                hour_limit_string = hour_limitation.group()
                hour = convert_hour(hour, hour_limit_string)
            time_point.hour = hour

        if limit_minute:
            limit_minute_string = limit_minute.group()
            if '半' in limit_minute_string:
                time_point.minute = 30
            elif '刻' in limit_minute_string:
                num = MONTH_NUM_PATTERN.search(limit_minute_string)
                if num:
                    num = self._char_num2num(num.group())
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

        time_handler = time_point.handler()

        return time_handler, time_handler, 'time_point', 'accurate'

    @staticmethod
    def normalize_blur_hour(time_string):
        """ 解析 `模糊 时段` 时间

        :return:
        """
        hour = HOUR_PATTERNS[1].search(time_string)

        first_time_point = TimePoint()
        second_time_point = TimePoint()

        if hour:
            hour_string = hour.group()

            # (凌晨|清[晨|早]|早[晨上]?|[上中下]午|(傍)?晚[间上]?|[深|半]夜)
            if hour_string == '清晨':
                first_time_point.hour = 5
                second_time_point.hour = 7
            elif hour_string == '清早':
                first_time_point.hour = 5
                second_time_point.hour = 8
            elif hour_string in ['早上', '早晨', '一早', '一大早']:
                first_time_point.hour = 6
                second_time_point.hour = 9
            elif hour_string == '上午':
                first_time_point.hour = 7
                second_time_point.hour = 11
            elif hour_string == '中午':
                first_time_point.hour = 12
                second_time_point.hour = 13
            elif hour_string == '下午':
                first_time_point.hour = 13
                second_time_point.hour = 17
            elif hour_string == '傍晚':
                first_time_point.hour = 13
                second_time_point.hour = 17
            elif hour_string == '晚上':
                first_time_point.hour = 17
                second_time_point.hour = 23
            elif hour_string == '晚间':
                first_time_point.hour = 20
                second_time_point.hour = 23
            elif hour_string == '深夜':
                first_time_point.hour = 23
                second_time_point.hour = 24
            elif hour_string == '半夜':
                first_time_point.hour = 0
                second_time_point.hour = 4
            elif hour_string == '凌晨':
                first_time_point.hour = 0
                second_time_point.hour = 4
            else:
                raise ValueError('the given string `{}` is illegal'.format(time_string))

        first_time_handler = first_time_point.handler()
        second_time_handler = second_time_point.handler()

        return first_time_handler, second_time_handler, 'time_point', 'blur'

    def _char_num2num(self, char_num):
        """ 将 三十一 转换为 31，用于月、日、时、分、秒的汉字转换

        :param char_num:
        :return:
        """
        res_num = self.money_standardization(char_num)
        if res_num == 'null':
            return 0
        else:
            return int(float(res_num[:-1]))

    def _char_year2num(self, char_year):
        """ 将 二零一九 年份转化为 2019

        :param char_year:
        :return:
        """
        year_list = list()
        for char in char_year:
            year_list.append(self.year_char2num_map.get(char, char))
        return ''.join(year_list)

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

            century = year_base[:2]
            return century + year_string
        else:
            return year_string

    @staticmethod
    def time_completion(time_handler, time_base_handler):
        """根据时间基，补全 time_handler，即把 time_handler 前部 -1 部分补齐

        :param time_handler:
        :param time_base_handler:
        :return:
        """

        for i in range(len(time_handler)):
            if time_handler[i] > -1:
                break
            time_handler[i] = time_base_handler[i]

        return time_handler

    @staticmethod
    def time_handler2standard_time(
            first_time_handler, second_time_handler):
        """ 将 time handler 转换为标准时间格式字符串

        :param first_time_handler:
        :param second_time_handler:
        :return:
        """
        first_handler = list()
        second_handler = list()
        for idx, (f, s) in enumerate(zip(first_time_handler, second_time_handler)):
            if f > -1:
                first_handler.append(f)
            elif f == -1:
                if idx == 1:
                    first_handler.append(1)
                elif idx == 2:
                    first_handler.append(1)
                elif idx == 3:
                    first_handler.append(0)
                elif idx == 4:
                    first_handler.append(0)
                elif idx == 5:
                    first_handler.append(0)
                else:
                    raise ValueError('first time handler {} illegal.'.format(first_handler))
            else:
                raise ValueError('before Christ {} can not be converted to standard time pattern.'.format(
                    first_time_handler))

            if s > -1:
                second_handler.append(s)
            elif s == -1:
                if idx == 1:
                    second_handler.append(12)
                elif idx == 2:
                    if second_handler[1] in [1, 3, 5, 7, 8, 10, 12]:
                        second_handler.append(31)
                    elif second_handler[1] in [4, 6, 9, 11]:
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
            first_time_string = datetime.datetime(
                first_handler[0], first_handler[1], first_handler[2],
                first_handler[3], first_handler[4], first_handler[5])
            second_time_string = datetime.datetime(
                second_handler[0], second_handler[1], second_handler[2],
                second_handler[3], second_handler[4], second_handler[5])
        except Exception:
            raise ValueError('the given time string is illegal.\n{}'.format(
                traceback.format_exc()))

        first_time_string = first_time_string.strftime('%Y-%m-%d %H:%M:%S')
        second_time_string = second_time_string.strftime('%Y-%m-%d %H:%M:%S')

        return first_time_string, second_time_string

    @staticmethod
    def check_handler(time_handler):
        """
        字符串合法校验，形如 [-1, 11, 29, -1, 23, -1] ，即中间部位有未指明时间，为非法时间字符串，
        左侧未指明时间须根据 base_time 补充完整，右侧未指明时间可省略，或按时间段补全
        """
        assert len(time_handler) == 6
        # 未识别出任何时间串，即全部为 -1：[-1, -1, -1, -1, -1, -1]
        if set(time_handler) == {-1}:
            return False

        first = False
        second = False
        for i in range(5):
            if time_handler[i] > -1 and time_handler[i+1] == -1:
                first = True
            if time_handler[i] == -1 and time_handler[i+1] > -1:
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
        else:
            raise ValueError('the given time_base is illegal.')

        return time_base_handler

    @staticmethod
    def _convert_handler2datetime(handler):
        """将 time handler转换为 datetime 类型

        :param handler:
        :return:
        """
        return datetime.datetime(
            handler[0], handler[1], handler[2],
            handler[3], handler[4], handler[5])

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
            return string2handler(solar_time_handler),\
                   string2handler(solar_time_handler)

    @staticmethod
    def _convert_solar2lunar(solar_time_handler):
        """

        :param solar_time_handler:
        :return:
        """

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

