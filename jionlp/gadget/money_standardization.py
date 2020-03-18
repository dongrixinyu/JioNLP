# -*- coding=utf-8 -*-

# import 


def turn_num_std_fmt(num, std_fmt="%.2f"):
    """将数字形式转换成`std_fmt`形式。
    使用该函数将数字形式转换成期望的`std_fmt`形式。

    Args:
        num: 一个数字，支持unicode，str，int或str格式。
        std_fmt: 希望转换后的数字格式，默认是带两位小数的float。

    Returns:
        转换后`std_fmt`形式的unicode类型的数字。

    Examples:
        >>> num = 30.5
        >>> print(bbd.turn_num_std_fmt(num))
        '30.50'
    """
    rtn_std_num = None

    if type(num) is str:
        if re.match("^\d+(\.)?\d*$", num):
            num = float(num)
            num = std_fmt % num
            rtn_std_num = num

    if type(num) is int or type(num) is float:
        num = std_fmt % num
        rtn_std_num = num
    return rtn_std_num


def turn_money_std_fmt_util1(num):
    """将中文金额形式转换成float形式。

    使用该函数将中文金额转换成易于计算的float形式，注意该函数是turn_money_std_fmt的
    辅助函数，只能方便将一万这种转换，一千万无法转换。

    Args:
      num: 一个中文格式表示的金额。

    Returns:
      转换后float类型的数字。
    """
    mult_nums = {u'分': 0.01, u'角': 0.1, u'十': 10, u'拾': 10, u'百': 100,
                 u'佰': 100, u'千': 1000, u'仟': 1000, u'万': 10000, u'亿': 100000000}
    plus_nums = {u'〇': 0, u'O': 0, u'零': 0, u'一': 1, u'二': 2, u'三': 3,
                 u'四': 4, u'五': 5, u'六': 6, u'七': 7, u'八': 8, u'九': 9,
                 u'两': 2, u'壹': 1, u'贰': 2, u'叁': 3, u'肆': 4, u'伍': 5,
                 u'陆': 6, u'柒': 7, u'捌': 8, u'玖': 9}
    rtn_std_num = 0.0
    if num.startswith('十'):
        num = '一' + num
    if num.startswith('拾'):
        num = '壹' + num
    if not num or type(num) is not str:
        return rtn_std_num

    tmp_nums = []
    for ch in list(num):
        plus_num = plus_nums.get(ch, 0)
        if plus_num != 0:
            tmp_nums.append(plus_num)
        mul_num = mult_nums.get(ch, 1)
        if len(tmp_nums) >= 1 and plus_num != 1:
            tmp_nums[-1] = tmp_nums[-1] * mul_num
    rtn_std_num = sum(tmp_nums)
    return rtn_std_num


def turn_money_std_fmt_util2(self, num):
    """将中文金额形式转换成float形式。

    使用该函数将中文金额转换成易于计算的float形式，注意该函数是turn_money_std_fmt的
    另一个辅助函数，与turn_money_std_fmt_util1搭配起来转换类似“1千万”数字。

    Args:
      num: 一个中文格式表示的金额。

    Returns:
      转换后float类型的数字。
    """
    rtn_num = 0.0
    if u"万" in num:
        seg_num = re.split(u"万", num)
        if len(seg_num) == 2:
            prev, nxt = seg_num
            tmp_prev_num = self.turn_money_std_fmt_util1(prev)
            tmp_prev_num = tmp_prev_num * 10000
            tmp_nxt_num = self.turn_money_std_fmt_util1(nxt)
            rtn_num = tmp_prev_num + tmp_nxt_num
    else:
        rtn_num = turn_money_std_fmt_util1(num)
    return rtn_num

def turn_money_std_fmt(self, inp_num, unit=u"元", std_fmt="%.2f", rtn_def_num="null"):
    """将各种金额形式转换成指定的形式。
    使用该函数将中文金额转换成易于计算的float形式，该函数可以转换如下金额格式：
    "六十四万零一百四十三元一角七分",
    "一万二千三百四十五元",
    "82，225.00元",
    "25481元",
    "1.2万元",
    "三百万",
    "45564.441111美元",
    "四百三十万",
    "二十五万三千二百美元",
    "两个亿",
    "二千九百六十美元",
    "233,333，333,434.344元"。

    Args:
        inp_num: 一个金额形式。
        unit: 金额单位，默认是”元“，支持”美元“。
        std_fmt：指定的转换后的格式，默认带两位小数
        rtn_def_num：转换失败的默认值。

    Returns:
        转换后指定格式的带`unit`的金额。

    Examples:
        >>> money = "六十四万零一百四十三元一角七分"
        >>> print(bbd.turn_money_std_fmt(money))
        "640143.17元"
    """

    suffix_nums = {
        u'万': 10000, u'亿': 100000000, u'仟万': 10000000, u'千万': 10000000,
        u'百万': 1000000, u'佰万': 1000000, u'十万': 100000, u'拾万': 100000,
    }
    rtn_money = rtn_def_num
    if not inp_num:
        return rtn_money
    inp_num = re.sub("[,， ]", "", inp_num)
    if len(inp_num) > 2 and inp_num[0:2] == u"美元":
        unit = u"美元"
        inp_num = inp_num[2:]
    if len(inp_num) > 1 and inp_num[0:1] == u"元":
        inp_num = inp_num[1:]
    if len(inp_num) > 2 and inp_num[-2:] == u"美元":
        unit = u"美元"
        inp_num = inp_num[:-2]
    if len(inp_num) > 1 and inp_num[-1] == u"元":
        inp_num = inp_num[:-1]
    if re.match("\d", inp_num):
        tmp_money = turn_num_std_fmt(inp_num, std_fmt)

        if tmp_money is not None:
            rtn_money = tmp_money + unit
            return rtn_money
        if len(inp_num) > 1:
            inp_num_suffix = inp_num[-1]
            num_suffix1 = suffix_nums.get(inp_num_suffix, 0)
            inp_num_suffix = inp_num[-2:]
            num_suffix2 = suffix_nums.get(inp_num_suffix, 0)
            if num_suffix2 != 0 or (num_suffix2 == 0 and num_suffix1 != 0):
                if num_suffix2 != 0:
                    num_suffix = num_suffix2
                    inp_num_prefix = inp_num[:-2]
                else:
                    num_suffix = num_suffix1
                    inp_num_prefix = inp_num[:-1]
                if re.match("\d+(\.)?\d*", inp_num_prefix):
                    tmp_money = float(inp_num_prefix) * num_suffix
                    rtn_money = self.turn_num_std_fmt(tmp_money, std_fmt) + unit

    else:
        if u"亿" in inp_num:
            seg_billion = re.split(u"亿", inp_num)
            if len(seg_billion) == 2:
                prev, nxt = seg_billion
                prev_num = self.turn_money_std_fmt_util2(prev)
                nxt_num = self.turn_money_std_fmt_util2(nxt)
                tmp_money = prev_num * 100000000 + nxt_num
                tmp_money = self.turn_num_std_fmt(tmp_money, std_fmt)
                rtn_money = tmp_money + unit
        else:
            tmp_money = self.turn_money_std_fmt_util2(inp_num)
            if tmp_money != 0.0:
                rtn_money = self.turn_num_std_fmt(tmp_money, std_fmt) + unit
    return rtn_money



