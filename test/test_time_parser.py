# -*- coding=utf-8 -*-

import time
import datetime
import unittest

import jionlp as jio


class TestTimeParser(unittest.TestCase):
    """ 测试时间解析工具 """

    def test_time_parser(self):
        """ test func time_parser """

        print('time stamp for test: ',
              time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(1623604000)))

        time_string_list = [
            # 年、月、日（标准）
            ['2015年8月12日', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2015-08-12 00:00:00', '2015-08-12 23:59:59']}],
            ['15年3月2日', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2015-03-02 00:00:00', '2015-03-02 23:59:59']}],
            ['03年2月28日', datetime.datetime(2021, 5, 6), {'type': 'time_point', 'definition': 'accurate', 'time': ['2003-02-28 00:00:00', '2003-02-28 23:59:59']}],
            ['9月30日', [2008, 3, 13], {'type': 'time_point', 'definition': 'accurate', 'time': ['2008-09-30 00:00:00', '2008-09-30 23:59:59']}],
            ['98年4月', [1997, 7, 1, 12, 30, 0], {'type': 'time_point', 'definition': 'accurate', 'time': ['1998-04-01 00:00:00', '1998-04-30 23:59:59']}],
            ['12月30号', {'year': 1837}, {'type': 'time_point', 'definition': 'accurate', 'time': ['1837-12-30 00:00:00', '1837-12-30 23:59:59']}],
            ['零七年八月二十九号', 1509329124., {'type': 'time_point', 'definition': 'accurate', 'time': ['2007-08-29 00:00:00', '2007-08-29 23:59:59']}],
            ['九零年9月十号', 109329124., {'type': 'time_point', 'definition': 'accurate', 'time': ['1990-09-10 00:00:00', '1990-09-10 23:59:59']}],
            ['十二月20号', 109329124., {'type': 'time_point', 'definition': 'accurate', 'time': ['1973-12-20 00:00:00', '1973-12-20 23:59:59']}],
            ['二零零三年十二月', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2003-12-01 00:00:00', '2003-12-31 23:59:59']}],
            ['二〇〇六年十二月', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2006-12-01 00:00:00', '2006-12-31 23:59:59']}],

            # 年、季度（公历）
            ['07年第三季度', [2008, 3, 2, 0], {'type': 'time_span', 'definition': 'accurate', 'time': ['2007-07-01 00:00:00', '2007-09-30 23:59:59']}],
            ['2021年前两个季度', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-01-01 00:00:00', '2021-06-30 23:59:59']}],
            ['2022年首季度', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2022-01-01 00:00:00', '2022-03-31 23:59:59']}],
            ['九七年一季度', [1999, 9, 2], {'type': 'time_span', 'definition': 'accurate', 'time': ['1997-01-01 00:00:00', '1997-03-31 23:59:59']}],
            ['一季度', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-01-01 00:00:00', '2021-03-31 23:59:59']}],

            # 年、模糊月份指示信息
            ['19年底', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2019-11-01 00:00:00', '2019-12-31 23:59:59']}],
            ['1993年上半年', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1993-01-01 00:00:00', '1993-06-30 23:59:59']}],
            ['二零二二年伊始', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2022-01-01 00:00:00', '2022-01-31 23:59:59']}],

            # 年（限定）、模糊月
            ['明年初', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2022-01-01 00:00:00', '2022-02-28 23:59:59']}],
            ['明年年初', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2022-01-01 00:00:00', '2022-02-28 23:59:59']}],
            ['次年年末', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2022-11-01 00:00:00', '2022-12-31 23:59:59']}],
            ['去年暑假', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2020-07-01 00:00:00', '2020-08-31 23:59:59']}],

            # 模糊月、日
            # 同月9号17点
            ['上个月15号', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-05-15 00:00:00', '2021-05-15 23:59:59']}],
            ['下月九号', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-07-09 00:00:00', '2021-07-09 23:59:59']}],

            # 世纪、年代
            ['18世纪', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1700-01-01 00:00:00', '1799-12-31 23:59:59']}],
            ['上世纪80年代', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1980-01-01 00:00:00', '1989-12-31 23:59:59']}],
            ['十九世纪七十年代', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1870-01-01 00:00:00', '1879-12-31 23:59:59']}],
            ['二十世纪九十年代末期', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1997-01-01 00:00:00', '1999-12-31 23:59:59']}],
            ['11世纪初', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1000-01-01 00:00:00', '1019-12-31 23:59:59']}],
            ['20世纪60年代前期', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1960-01-01 00:00:00', '1962-12-31 23:59:59']}],
            # -> 公元前二世纪，可以检测到，但无法转换为标准时间而报错

            # 年、范围月
            ['2022年前十一个月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2022-01-01 00:00:00', '2022-11-30 23:59:59']}],
            ['70年第8个月', [1965, 10, 1, 12, 30, 0], {'type': 'time_span', 'definition': 'accurate', 'time': ['1970-08-01 00:00:00', '1970-08-31 23:59:59']}],
            ['2005年首月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2005-01-01 00:00:00', '2005-01-31 23:59:59']}],
            ['五八年前七个月', 10, {'type': 'time_span', 'definition': 'accurate', 'time': ['1958-01-01 00:00:00', '1958-07-31 23:59:59']}],
            ['二零二一年后三月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-10-01 00:00:00', '2021-12-31 23:59:59']}],
            ['1967年前两月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['1967-01-01 00:00:00', '1967-02-28 23:59:59']}],

            # 年（限定）、月、日
            ['去年3月3号', {'year': 1966}, {'type': 'time_span', 'definition': 'accurate', 'time': ['1965-03-03 00:00:00', '1965-03-03 23:59:59']}],
            ['今年六月', {'year': 1966}, {'type': 'time_span', 'definition': 'accurate', 'time': ['1966-06-01 00:00:00', '1966-06-30 23:59:59']}],
            ['明年3月份', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2022-03-01 00:00:00', '2022-03-31 23:59:59']}],

            # 年（模糊限定）
            ['3年后', {'year': 2021}, {'type': 'time_span', 'definition': 'blur', 'time': ['2024-01-01 00:00:00', '2024-12-31 23:59:59']}],
            ['两年前', {'year': 2021}, {'type': 'time_span', 'definition': 'blur', 'time': ['2019-01-01 00:00:00', '2019-12-31 23:59:59']}],
            ['一年半以前', {'year': 2021}, {'type': 'time_span', 'definition': 'blur', 'time': ['2020-01-01 00:00:00', '2020-12-31 23:59:59']}],
            ['一年半以前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2019-09-01 00:00:00', '2020-03-31 23:59:59']}],
            ['半年之后', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2021-09-01 00:00:00', '2022-03-31 23:59:59']}],
            ['40多年前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1971-01-01 00:00:00', '1981-12-31 23:59:59']}],
            ['二十几年前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['1991-01-01 00:00:00', '2001-12-31 23:59:59']}],
            ['1000多年之后', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['3021-01-01 00:00:00', '4021-12-31 23:59:59']}],
            ['几十年之后', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2041-01-01 00:00:00', '2121-12-31 23:59:59']}],

            # time span 式 `从……至……` 年、月、日（不包括时分秒）
            ['2017年8月11日至8月22日', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2017-08-11 00:00:00', '2017-08-22 23:59:59']}],
            ['2017年8月15日至2018年3月29日', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2017-08-15 00:00:00', '2018-03-29 23:59:59']}],
            ['2017年8月至11月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2017-08-01 00:00:00', '2017-11-30 23:59:59']}],
            ['2017年五月至2018年四月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2017-05-01 00:00:00', '2018-04-30 23:59:59']}],
            ['二〇一九年5月8日起', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2019-05-08 00:00:00', '2021-06-14 01:06:40']}],
            ['从去年9月起', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2020-09-01 00:00:00', '2021-06-14 01:06:40']}],
            ['从2001年起至今', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2001-01-01 00:00:00', '2021-06-14 01:06:40']}],
            ['从2008年——2018年', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2008-01-01 00:00:00', '2018-12-31 23:59:59']}],
            ['从2015年1月至12月', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2015-01-01 00:00:00', '2015-12-31 23:59:59']}],
            ['从2018年12月九号到十五号', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2018-12-09 00:00:00', '2018-12-15 23:59:59']}],
            ['2019年感恩节到2021年母亲节', {'year': 2020}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2019-11-28 00:00:00', '2021-05-09 23:59:59']}],
            ['去年春节到元宵节', {'year': 2020}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2019-02-05 00:00:00', '2019-02-19 23:59:59']}],
            ['明年6月之前', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 01:06:40', '2022-06-30 23:59:59']}],

            # ['2018年2——4月'], 未决
            ['明年底前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2021-06-14 01:06:40', '2022-12-31 23:59:59']}],
            ['明年初之前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2021-06-14 01:06:40', '2022-02-28 23:59:59']}],
            ['2025年前', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 01:06:40', '2025-12-31 23:59:59']}],
            ['二零四九年十月一号以前', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 01:06:40', '2049-10-01 23:59:59']}],
            ['三年前', 1623604000, {'type': 'time_span', 'definition': 'blur', 'time': ['2018-01-01 00:00:00', '2018-12-31 23:59:59']}],
            ['二〇三五年前', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 01:06:40', '2035-12-31 23:59:59']}],

            # 农历年、月、日
            ['二零一二年农历正月十五', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2012-02-06 00:00:00', '2012-02-06 23:59:59']}],
            ['农历二〇二一年六月', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-07-10 00:00:00', '2021-08-07 23:59:59']}],
            ['五月廿二', {'year': 2022}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2022-06-20 00:00:00', '2022-06-20 23:59:59']}],
            ['腊月初十', {'year': 2022}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2023-01-01 00:00:00', '2023-01-01 23:59:59']}],
            ['农历十月', {'year': 2022}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2022-10-25 00:00:00', '2022-11-23 23:59:59']}],
            ['农历闰四月', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2020-05-23 00:00:00', '2020-06-20 23:59:59']}],
            ['闰四月', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2020-05-23 00:00:00', '2020-06-20 23:59:59']}],
            ['闰4月', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2020-05-23 00:00:00', '2020-06-20 23:59:59']}],
            ['廿一', {'year': 2021, 'month': 5}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-30 00:00:00', '2021-06-30 23:59:59']}],
            ['正月', {'year': 2021, 'month': 5}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-02-12 00:00:00', '2021-03-12 23:59:59']}],
            ['去年五月初五', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2020-06-25 00:00:00', '2020-06-25 23:59:59']}],
            ['后年九月廿二', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2023-11-05 00:00:00', '2023-11-05 23:59:59']}],
            ['明年腊月', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2022-12-23 00:00:00', '2023-01-21 23:59:59']}],

            # 年、节气
            ['2017年大寒', time.time(), {'type': 'time_point', 'definition': 'accurate', 'time': ['2018-01-20 00:00:00', '2018-01-20 23:59:59']}],
            ['20年小寒', time.time(), {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-01-06 00:00:00', '2021-01-06 23:59:59']}],
            ['芒种', {'year': 2021, 'month': 5}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-05 00:00:00', '2021-06-05 23:59:59']}],

            # 年、季节
            ['2021年春', {'year': 2021, 'month': 5}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-02-03 00:00:00', '2021-05-04 23:59:59']}],
            ['冬季', {'year': 2021, 'month': 5}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-11-07 00:00:00', '2022-02-02 23:59:59']}],

            # 年、月、星期
            ['上周', 1623604000, {'type': 'time_point', 'definition': 'blur', 'time': ['2021-06-07 00:00:00', '2021-06-13 23:59:59']}],
            ['这周', 1623604000, {'type': 'time_point', 'definition': 'blur', 'time': ['2021-06-14 00:00:00', '2021-06-20 23:59:59']}],
            ['上上周', 1623604000, {'type': 'time_point', 'definition': 'blur', 'time': ['2021-05-31 00:00:00', '2021-06-06 23:59:59']}],
            ['下周六', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-26 00:00:00', '2021-06-26 23:59:59']}],
            ['下周周六', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-26 00:00:00', '2021-06-26 23:59:59']}],
            ['前两周', 1623604000, {'type': 'time_point', 'definition': 'blur', 'time': ['2021-05-31 00:00:00', '2021-06-14 01:06:40']}],
            ['4个星期之后', 1623604000, {'type': 'time_point', 'definition': 'blur', 'time': ['2021-07-12 00:00:00', '2021-07-18 23:59:59']}],
            ['星期天', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-20 00:00:00', '2021-06-20 23:59:59']}],
            ['下个星期一', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-21 00:00:00', '2021-06-21 23:59:59']}],
            ['6月第3个星期日', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-20 00:00:00', '2021-06-20 23:59:59']}],
            ['八月份的第一个周二', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-08-03 00:00:00', '2021-08-03 23:59:59']}],

            # 年、月、旬
            ['6月上旬', {'year': 2021}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-01 00:00:00', '2021-06-10 23:59:59']}],
            ['1999年7月下旬', time.time(), {'type': 'time_span', 'definition': 'accurate', 'time': ['1999-07-11 00:00:00', '1999-07-31 23:59:59']}],
            ['九月下旬', {'year': 2021}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-09-11 00:00:00', '2021-09-30 23:59:59']}],

            # 限定性 日
            ['后天', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-16 00:00:00', '2021-06-16 23:59:59']}],
            ['今天', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-14 00:00:00', '2021-06-14 23:59:59']}],
            ['昨晚8时35分', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-13 20:35:00', '2021-06-13 20:35:59']}],
            ['当晚十时', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-14 22:00:00', '2021-06-14 22:59:59']}],

            # 年，节日
            ['教师节', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-09-10 00:00:00', '2021-09-10 23:59:59']}],
            ['十一', {'year': 2001}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2001-10-01 00:00:00', '2001-10-01 23:59:59']}],
            ['去年元旦', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2019-01-01 00:00:00', '2019-01-01 23:59:59']}],
            ['去年春节', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2019-02-05 00:00:00', '2019-02-05 23:59:59']}],
            ['零六年端午', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2006-05-31 00:00:00', '2006-05-31 23:59:59']}],
            ['明年母亲节', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-05-09 00:00:00', '2021-05-09 23:59:59']}],
            ['2019年感恩节', {'year': 2020}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2019-11-28 00:00:00', '2019-11-28 23:59:59']}],

            # 年月日 时分秒
            ['7月4日晚上7点09分18秒', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-07-04 19:09:18', '2021-07-04 19:09:18']}],
            ['去年7月4日晚上7点09分', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2020-07-04 19:09:00', '2020-07-04 19:09:59']}],
            ['早上7点', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-14 07:00:00', '2021-06-14 07:59:59']}],
            ['下月15号下午6点', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-07-15 18:00:00', '2021-07-15 18:59:59']}],
            # 存在6点前，包不包含6点的问题，须设置参数判定
            ['下月15号下午6点前', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 01:06:40', '2021-07-15 18:59:59']}],
            ['农历8月十五晚8点', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-09-21 20:00:00', '2021-09-21 20:59:59']}],
            ['上周六中午12点', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-12 12:00:00', '2021-06-12 12:59:59']}],
            ['大前年七夕节半夜11点', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2018-08-17 23:00:00', '2018-08-17 23:59:59']}],
            # 某日夜晚指第二天夜晚还是当天夜晚，须设置参数判定，原因在于人的认知是早晨才是一天的开始  '21时~凌晨1时'
            ['大前年七夕节半夜1点', {'year': 2021}, {'type': 'time_point', 'definition': 'accurate', 'time': ['2018-08-17 01:00:00', '2018-08-17 01:59:59']}],
            ['下个月9号早上8点到中午12点', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-07-09 08:00:00', '2021-07-09 12:59:59']}],
            ['昨天9点20', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-13 09:20:00', '2021-06-13 09:20:59']}],
            ['上个月23号晚上九点零九', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-05-23 21:09:00', '2021-05-23 21:09:59']}],
            ['12月9日零时至12月16日24时', {'year': 2021}, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-12-09 00:00:00', '2021-12-16 23:59:59']}],
            ['13:20~次日05:40', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-14 13:20:00', '2021-06-15 05:40:59']}],


            # 时分秒 标准格式按 `:` 区隔
            ['上月30号12:37', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-05-30 12:37:00', '2021-05-30 12:37:59']}],
            ['35:37', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-14 01:35:37', '2021-06-14 01:35:37']}],
            ['15:37', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-06-14 15:37:00', '2021-06-14 15:37:59']}],
            ['2019年6月28日下午3:00', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2019-06-28 15:00:00', '2019-06-28 15:00:59']}],
            ['2019年6月28日9:30~11:30', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2019-06-28 09:30:00', '2019-06-28 11:30:59']}],

            # 时、限定性 分
            ['4月26日20时1刻', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-04-26 20:15:00', '2021-04-26 20:15:59']}],
            ['去年十一月廿九下午4点半', 1623604000, {'type': 'time_point', 'definition': 'accurate', 'time': ['2021-01-12 16:30:00', '2021-01-12 16:30:59']}],
            ['9日0时至18时三刻', 1623604000, {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-06-09 00:00:00', '2021-06-09 18:45:59']}],

        ]

        for item in time_string_list:
            time_res = jio.parse_time(item[0], time_base=item[1])

            self.assertEqual(time_res, item[2])
            # if time_res != item[2]:
            #     print('test: ', item[0], time_res)


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_time_norm = [TestTimeParser('test_time_normalizer')]
    suite.addTests(test_time_norm)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

