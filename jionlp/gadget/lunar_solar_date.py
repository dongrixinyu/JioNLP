# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
从 1900 年到 2100 年的农历月份数据代码 20 位二进制代码表示一个年份的数据。
    前 4 位：0 表示闰月为 29 天，1 表示闰月为 30 天；
    中间 12 位：从左起表示 1-12 月每月的大小，1 为 30 天，0 为 29 天；
    最后 4 位：表示闰月的月份，0 表示当年无闰月；
    前 4 位和最后 4 位应该结合使用，如果最后四位为 0，则不考虑前四位。
    例：
        - 1901年代码为 19168，转成二进制为 0b100101011100000, 最后四位为0，当年无闰月，月份数据为 010010101110 分别代表12月的大小情况
        - 1903年代码为 21717，转成二进制为 0b101010011010101，最后四位为5，当年为闰五月，首四位为0，闰月为29天，月份数据为 010101001101，
            分别代表12月的大小情况

"""


from datetime import datetime, timedelta
from itertools import accumulate


class LunarSolarDate(object):
    """农历日期与公历日期转换 """
    # 中文年份编码
    CHINESE_YEAR_CODE = [
        19416, 19168, 42352, 21717, 53856, 55632, 91476, 22176, 39632, 21970, 19168, 42422,
        42192, 53840, 119381, 46400, 54944, 44450, 38320, 84343, 18800, 42160, 46261, 27216,
        27968, 109396, 11104, 38256, 21234, 18800, 25958, 54432, 59984, 92821, 23248, 11104,
        100067, 37600, 116951, 51536, 54432, 120998, 46416, 22176, 107956, 9680, 37584, 53938,
        43344, 46423, 27808, 46416, 86869, 19872, 42416, 83315, 21168, 43432, 59728, 27296,
        44710, 43856, 19296, 43748, 42352, 21088, 62051, 55632, 23383, 22176, 38608, 19925,
        19152, 42192, 54484, 53840, 54616, 46400, 46752, 103846, 38320, 18864, 43380, 42160,
        45690, 27216, 27968, 44870, 43872, 38256, 19189, 18800, 25776, 29859, 59984, 27480,
        23232, 43872, 38613, 37600, 51552, 55636, 54432, 55888, 30034, 22176, 43959, 9680,
        37584, 51893, 43344, 46240, 47780, 44368, 21977, 19360, 42416, 86390, 21168, 43312,
        31060, 27296, 44368, 23378, 19296, 42726, 42208, 53856, 60005, 54576, 23200, 30371,
        38608, 19195, 19152, 42192, 118966, 53840, 54560, 56645, 46496, 22224, 21938, 18864,
        42359, 42160, 43600, 111189, 27936, 44448, 84835, 37744, 18936, 18800, 25776, 92326,
        59984, 27296, 108228, 43744, 37600, 53987, 51552, 54615, 54432, 55888, 23893, 22176,
        42704, 21972, 21200, 43448, 43344, 46240, 46758, 44368, 21920, 43940, 42416, 21168,
        45683, 26928, 29495, 27296, 44368, 84821, 19296, 42352, 21732, 53600, 59752, 54560,
        55968, 92838, 22224, 19168, 43476, 41680, 53584, 62034, 54560]

    # 从 1900 年，至 2100 年每年的农历春节的公历日期
    CHINESE_NEW_YEAR = [
        '19000131',
        '19010219', '19020208', '19030129', '19040216', '19050204', '19060125', '19070213',
        '19080202', '19090122', '19100210', '19110130', '19120218', '19130206', '19140126',
        '19150214', '19160203', '19170123', '19180211', '19190201', '19200220', '19210208',
        '19220128', '19230216', '19240205', '19250124', '19260213', '19270202', '19280123',
        '19290210', '19300130', '19310217', '19320206', '19330126', '19340214', '19350204',
        '19360124', '19370211', '19380131', '19390219', '19400208', '19410127', '19420215',
        '19430205', '19440125', '19450213', '19460202', '19470122', '19480210', '19490129',
        '19500217', '19510206', '19520127', '19530214', '19540203', '19550124', '19560212',
        '19570131', '19580218', '19590208', '19600128', '19610215', '19620205', '19630125',
        '19640213', '19650202', '19660121', '19670209', '19680130', '19690217', '19700206',
        '19710127', '19720215', '19730203', '19740123', '19750211', '19760131', '19770218',
        '19780207', '19790128', '19800216', '19810205', '19820125', '19830213', '19840202',
        '19850220', '19860209', '19870129', '19880217', '19890206', '19900127', '19910215',
        '19920204', '19930123', '19940210', '19950131', '19960219', '19970207', '19980128',
        '19990216', '20000205', '20010124', '20020212', '20030201', '20040122', '20050209',
        '20060129', '20070218', '20080207', '20090126', '20100214', '20110203', '20120123',
        '20130210', '20140131', '20150219', '20160208', '20170128', '20180216', '20190205',
        '20200125', '20210212', '20220201', '20230122', '20240210', '20250129', '20260217',
        '20270206', '20280126', '20290213', '20300203', '20310123', '20320211', '20330131',
        '20340219', '20350208', '20360128', '20370215', '20380204', '20390124', '20400212',
        '20410201', '20420122', '20430210', '20440130', '20450217', '20460206', '20470126',
        '20480214', '20490202', '20500123', '20510211', '20520201', '20530219', '20540208',
        '20550128', '20560215', '20570204', '20580124', '20590212', '20600202', '20610121',
        '20620209', '20630129', '20640217', '20650205', '20660126', '20670214', '20680203',
        '20690123', '20700211', '20710131', '20720219', '20730207', '20740127', '20750215',
        '20760205', '20770124', '20780212', '20790202', '20800122', '20810209', '20820129',
        '20830217', '20840206', '20850126', '20860214', '20870203', '20880124', '20890210',
        '20900130', '20910218', '20920207', '20930127', '20940215', '20950205', '20960125',
        '20970212', '20980201', '20990121', '21000209'
    ]

    def __init__(self):
        self.tian = '甲乙丙丁戊己庚辛壬癸'
        self.di = '子丑寅卯辰巳午未申酉戌亥'
        self.sheng_xiao = '鼠牛虎兔龙蛇马羊猴鸡狗猪'
        self.chinese_nums = '零一二三四五六七八九十'

    def to_solar_date(self, lunar_year, lunar_month, lunar_day, leap_month=False):
        """农历日期转换为公历日期，若农历日期不存在，则报错

        Args:
            lunar_year(int): 农历年
            lunar_month(int): 农历月份
            lunar_day(int): 农历日
            leap_month(bool): 是否是在农历闰月中，默认 False

        Returns:
            datetime: 当前农历对应的公历日期

        Examples:
            >>> import datetime
            >>> import jionlp as jio
            >>> res = jio.lunar2solar(1989, 9, 23, False)
            >>> print('1989-9-23 非闰月 ==> ', res)

            # 1989-9-23 非闰月 ==> 1989-10-22 00:00:00

        """
        if not self._validate(lunar_year, lunar_month, lunar_day, leap_month):
            raise ValueError('农历日期不支持 => 1.超出农历1900年1月1日~2100年12月29日，2.日期不存在')

        new_year = datetime.strptime(self.CHINESE_NEW_YEAR[lunar_year - 1900], '%Y%m%d')
        time_delta = timedelta(days=self._lunar_days_passed(
            lunar_year, lunar_month, lunar_day, leap_month))
        return new_year + time_delta

    def to_lunar_date(self, solar_date):
        """从公历日期生成农历日期

        Arguments:
            solar_date(datetime): 公历的日期

        Returns:
            tuple: 生成的农历日期，4元组，分别为农历年、月、日、是否为闰月

        Examples:
            >>> import datetime
            >>> import jionlp as jio
            >>> res = jio.solar2lunar(datetime.datetime(1989, 10, 22))
            >>> print('1989-10-22 ==> ', res)

            # 1989-10-22 ==> (1989, 9, 23, False)

        """
        lunar_year = solar_date.year
        if (datetime.strptime(self.CHINESE_NEW_YEAR[lunar_year - 1900], '%Y%m%d') - solar_date).days > 0:
            lunar_year -= 1

        new_year_date = datetime.strptime(self.CHINESE_NEW_YEAR[lunar_year - 1900], '%Y%m%d')
        days_passed = (solar_date - new_year_date).days
        year_code = self.CHINESE_YEAR_CODE[lunar_year - 1900]
        month_days = LunarSolarDate._decode(year_code)

        for pos, days in enumerate(accumulate(month_days)):
            if days_passed + 1 <= days:
                month = pos + 1
                lunar_day = month_days[pos] - (days - days_passed) + 1
                break

        leap_month = False
        if (year_code & 0xf) == 0 or month <= (year_code & 0xf):
            lunar_month = month
        else:
            lunar_month = month - 1

        if (year_code & 0xf) != 0 and month == (year_code & 0xf) + 1:
            leap_month = True

        return lunar_year, lunar_month, lunar_day, leap_month

    def _lunar_days_passed(self, lunar_year, lunar_month, lunar_day, leap_month):
        """计算当前农历日期和当年农历新年之间的天数差值

        Returns:
            int: 差值天数
        """
        year_code = self.CHINESE_YEAR_CODE[lunar_year - 1900]

        month_days = LunarSolarDate._decode(year_code)
        month_leap = year_code & 0xf  # 当前农历年的闰月，为0表示无润叶

        if (month_leap == 0) or (lunar_month < month_leap):  # 当年无闰月，或者有闰月但是当前月小于闰月
            days_passed_month = sum(month_days[:lunar_month - 1])
        elif (not leap_month) and (lunar_month == month_leap):  # 当前不是闰月，并且当前月份和闰月相同
            days_passed_month = sum(month_days[:lunar_month - 1])
        else:
            days_passed_month = sum(month_days[:lunar_month])

        return days_passed_month + lunar_day - 1

    def chinese_lunar_date(self, lunar_year, lunar_month, lunar_day, leap_month):
        zh_year = ''
        for i in range(0, 4):
            zh_year += self.chinese_nums[int(str(lunar_year)[i])]
        zh_year += '年'

        if leap_month:
            zh_month = '闰'
        else:
            zh_month = ''

        if lunar_month == 1:
            zh_month += '正'
        elif lunar_month == 12:
            zh_month += '腊'
        elif lunar_month <= 10:
            zh_month += self.chinese_nums[lunar_month]
        else:
            zh_month += '十{}'.format(self.chinese_nums[lunar_month - 10])
        zh_month += '月'

        if lunar_day <= 10:
            zh_day = '初{}'.format(self.chinese_nums[lunar_day])
        elif lunar_day < 20:
            zh_day = '十{}'.format(self.chinese_nums[lunar_day - 10])
        elif lunar_day == 20:
            zh_day = '二十'
        elif lunar_day < 30:
            zh_day = '二十{}'.format(self.chinese_nums[lunar_day - 20])
        else:
            zh_day = '三十'

        year_tian_di = '{}{}'.format(
            self.tian[(lunar_year - 1900 + 36) % 10],
            self.di[(lunar_year - 1900 + 36) % 12]) + '年'

        return '{}{}{} {} ({}年)'.format(
            zh_year, zh_month, zh_day, year_tian_di,
            self.sheng_xiao[(lunar_year - 1900) % 12])

    def _validate(self, year, month, day, leap):
        """农历日期校验

        Args:
            year(int): 农历年份
            month(int): 农历月份
            day(int): 农历日期
            leap(bool): 农历是否为闰月日期

        Returns:
            bool: 校验是否通过
        """
        # 年份低于1900，大于2100，或者月份不属于 1-12，或者日期不属于 1-30，返回校验失败
        if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 30):
            return False

        year_code = self.CHINESE_YEAR_CODE[year - 1900]

        # 有闰月标志
        if leap:
            if (year_code & 0xf) != month:  # 年度闰月和校验闰月不一致的话，返回校验失败
                return False
            elif day == 30:  # 如果日期是30的话，直接返回年度代码首位是否为1，即闰月是否为大月
                return (year_code >> 16) == 1
            else:  # 年度闰月和当前月份相同，日期不为30的情况，返回通过
                return True
        elif day <= 29:  # 非闰月，并且日期小于等于29，返回通过
            return True
        else:  # 非闰月日期为30，返回年度代码中的月份位是否为1，即是否为大月
            return ((year_code >> (12 - month) + 4) & 1) == 1

    @staticmethod
    def _decode(year_code):
        """解析年度农历代码函数

        Arguments:
            year_code(int): 从年度代码数组中获取的代码整数

        Returns:
            int: 当前年度代码解析以后形成的每月天数数组，已将闰月嵌入对应位置，即有闰月的年份返回长度为 13，否则为 12

        """
        month_days = list()
        for i in range(5, 17):
            if (year_code >> (i - 1)) & 1:
                month_days.insert(0, 30)
            else:
                month_days.insert(0, 29)
        if year_code & 0xf:
            if year_code >> 16:
                month_days.insert((year_code & 0xf), 30)
            else:
                month_days.insert((year_code & 0xf), 29)
        return month_days


if __name__ == '__main__':
    ls = LunarSolarDate()
    res = ls.to_lunar_date(datetime(1989, 10, 22))
    print(res)
    res = ls.to_solar_date(1989, 9, 23, False)
    print(type(res))

