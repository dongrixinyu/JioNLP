# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import re

from jionlp.rule.rule_pattern import CURRENCY_CASE


__all__ = ['MoneyStandardization']


class MoneyStandardization(object):
    """将各种金额形式转换成指定的形式。
    使用该函数将中文金额转换成易于计算的float形式，该函数可以转换如下金额格式：
    "六十四万零一百四十三元一角七分",
    "一万二千三百四十五元",
    "82，225.00元",
    "25481元",
    "1.2万元",
    "三百万",
    "45564.44美元",
    "四百三十万",
    "二十五万三千二百美元",
    "两个亿",
    "十块三毛",
    "一百三十五块六角钱"
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
        >>> import jionlp as jio
        >>> money = "六十四万零一百四十三元一角七分"
        >>> print(jio.money_standardization(money))
        "640143.17元"

    """
    def __init__(self):
        self.number_pattern = None
        
    def _prepare(self):
        self.number_pattern = re.compile('\d')
        self.float_num_boundry_pattern = re.compile('^\d+(\.)?\d*$')
        self.float_num_pattern = re.compile('\d+(\.)?\d*')
        self.punc_pattern = re.compile('[,， ]')
        self.wan_pattern = re.compile('万|萬')
        self.yi_pattern = re.compile('亿')
        self.chinese_yuan_currency_pattern = re.compile('(块钱|元|块)')
        self.chinese_jiao_currency_pattern = re.compile('(角|毛)')
        self.currency_case_pattern = re.compile(CURRENCY_CASE)
        
        self.mult_nums = {
            '分': 0.01, '角': 0.1, '毛': 0.1, '十': 10, '拾': 10, 
            '百': 100, '佰': 100, '千': 1000, '仟': 1000, 
            '万': 10000, '萬': 10000, '亿': 100000000}
        self.plus_nums = {
            '〇': 0, 'O': 0, '零': 0, '一': 1, '二': 2, '三': 3,
            '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '两': 2, '壹': 1, '贰': 2, '俩': 2, '叁': 3, '弎': 3,
            '仨': 3, '肆': 4, '伍': 5,
            '陆': 6, '柒': 7, '捌': 8, '玖': 9}
        self.suffix_nums = {
            '百': 100, '佰': 100, '千': 1000, '仟': 1000,
            '万': 10000, '亿': 100000000, '仟万': 10000000, 
            '千万': 10000000, '百万': 1000000, '佰万': 1000000,
            '十万': 100000, '拾万': 100000, '兆': 1000000000000}
        
    def turn_num_std_fmt(self, num, std_fmt='%.2f'):
        """将数字形式转换成`std_fmt`形式。
        使用该函数将数字形式转换成期望的`std_fmt`形式。

        Args:
            num: 一个数字，支持 int 或 str 格式。
            std_fmt: 希望转换后的数字格式，默认是带两位小数的float。

        Returns:
            转换后`std_fmt`形式的 str 类型的数字。

        Examples:
            >>> num = 30.5
            >>> print(self.turn_num_std_fmt(num))
            '30.50'
        """
        rtn_std_num = None

        if type(num) is str:
            if self.float_num_boundry_pattern.match(num):
                num = float(num)
                num = std_fmt % num
                rtn_std_num = num

        if type(num) is int or type(num) is float:
            num = std_fmt % num
            rtn_std_num = num
            
        return rtn_std_num

    def turn_money_std_fmt_util1(self, num):
        """将中文金额形式转换成 float 形式。

        使用该函数将中文金额转换成易于计算的 float 形式，注意该函数是 turn_money_std_fmt
        辅助函数，只能方便将一万这种转换，一千万无法转换。

        Args:
          num: 一个中文格式表示的金额。

        Returns:
          转换后 float 类型的数字。
        """
        
        rtn_std_num = 0.0
        if num.startswith('十'):
            num = '一' + num
        if num.startswith('拾'):
            num = '壹' + num
        # 对角、分进行规范化
        if self.chinese_yuan_currency_pattern.search(num):
            jiao_fen = self.chinese_yuan_currency_pattern.split(num)[-1]
            if self.chinese_jiao_currency_pattern.search(jiao_fen):
                fen = self.chinese_jiao_currency_pattern.split(jiao_fen)[-1]
                if '分' not in fen and len(fen) == 1:
                    # 分 字符串无“分”字且长度为 1
                    num = num + '分'
            else:
                if len(jiao_fen) == 1:
                    # 即 角分 字符串仅有一个字符，即角的数字
                    num = num + '角'

        if not num or type(num) is not str:
            return rtn_std_num

        tmp_nums = list()
        for ch in list(num):
            plus_num = self.plus_nums.get(ch, 0)
            if plus_num != 0:
                tmp_nums.append(plus_num)
            mul_num = self.mult_nums.get(ch, 1)
            if len(tmp_nums) >= 1 and plus_num != 1:
                tmp_nums[-1] = tmp_nums[-1] * mul_num
                
        rtn_std_num = sum(tmp_nums)
        return rtn_std_num

    def turn_money_std_fmt_util2(self, num):
        """将中文金额形式转换成 float 形式。

        使用该函数将中文金额转换成易于计算的 float 形式，注意该函数是 turn_money_std_fmt 的
        另一个辅助函数，与 turn_money_std_fmt_util1 搭配起来转换类似“1千万”数字。

        Args:
            num: 一个中文格式表示的金额。

        Returns:
            转换后 float 类型的数字。
        """
        rtn_num = 0.0
        if '万' in num or '萬' in num:
            seg_num = self.wan_pattern.split(num)
            if len(seg_num) == 2:
                prev, nxt = seg_num
                tmp_prev_num = self.turn_money_std_fmt_util1(prev)
                tmp_prev_num = tmp_prev_num * 10000
                tmp_nxt_num = self.turn_money_std_fmt_util1(nxt)
                rtn_num = tmp_prev_num + tmp_nxt_num
        else:
            rtn_num = self.turn_money_std_fmt_util1(num)
        return rtn_num

    def _get_currency_case(self, input_num):
        """ 获取金额中的货币类型 """
        res = self.currency_case_pattern.search(input_num)
        if res is not None:
            # 规定标准的货币类型
            if res.group() == '块钱':
                unit = '元'
            elif res.group() == '港元':
                unit = '港币'
            elif res.group() == '澳大利亚元':
                unit = '澳元'
            else:
                unit = res.group()
            
            if res.span()[1] == len(input_num):
                # 切去字符串末尾最后的货币类型，若不在末尾则不切
                return unit, input_num[0: res.span()[0]]
            else:
                return unit, input_num
        else:
            return '元', input_num  # 默认是人民币元

    def __call__(self, inp_num, unit='元', std_fmt='%.2f', rtn_def_num='null'):

        if self.number_pattern is None:
            self._prepare()
        
        rtn_money = rtn_def_num
        if not inp_num:
            return rtn_money
        
        # 去除其中的标点符号 ，,等
        inp_num = self.punc_pattern.sub('', inp_num)
        
        # 判断货币类型
        unit, inp_num = self._get_currency_case(inp_num)
        
        if self.number_pattern.match(inp_num): 
            tmp_money = self.turn_num_std_fmt(inp_num, std_fmt)

            if tmp_money is not None:  # 纯数字格式的金额
                rtn_money = tmp_money + unit
                return rtn_money
            
            if len(inp_num) > 1:
                inp_num_suffix = inp_num[-1]
                num_suffix1 = self.suffix_nums.get(inp_num_suffix, 0)
                inp_num_suffix = inp_num[-2:]
                num_suffix2 = self.suffix_nums.get(inp_num_suffix, 0)
                if num_suffix2 != 0 or (num_suffix2 == 0 and num_suffix1 != 0):
                    if num_suffix2 != 0:
                        num_suffix = num_suffix2
                        inp_num_prefix = inp_num[:-2]
                    else:
                        num_suffix = num_suffix1
                        inp_num_prefix = inp_num[:-1]
                        
                    if self.float_num_pattern.match(inp_num_prefix):
                        
                        tmp_money = float(inp_num_prefix) * num_suffix
                        rtn_money = self.turn_num_std_fmt(tmp_money, std_fmt) + unit

        else:
            if '亿' in inp_num:
                seg_billion = self.yi_pattern.split(inp_num)
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

