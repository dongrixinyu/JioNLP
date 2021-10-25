# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
TODO:
    - 个
    - 某些金额为 合计/共/共计、共合计、合计共、共约1000元 类型。
    - 某些金额为单价类型，
        - 100 元每节课
        - 每桶油 1700 美元
        - 289.02 日元/本
    - 金额范围
        - 从8500元到3万元不等
    - 金额模糊表达
        - 五六百美元

"""

import re

from jionlp.util.funcs import start_end
from jionlp.rule.rule_pattern import CURRENCY_CASE, MONEY_PREFIX_STRING,\
    MONEY_PREFIX_STRING, MONEY_SUFFIX_STRING, MONEY_BLUR_STRING, \
    MONEY_MINUS_STRING, MONEY_PLUS_STRING, MONEY_SUFFIX_CASE_STRING, \
    MONEY_KUAI_MAO_JIAO_FEN_STRING


__all__ = ['MoneyParser']


class MoneyParser(object):
    """将各种金额形式转换成指定的形式。
    使用该函数将中文金额转换成易于计算的float形式，该函数可以转换如下金额格式。

    Args:
        money_string(str): 一个金额形式字符串。
        default_unit(str): 默认金额单位，默认是 ”元“（人民币），指当金额中未指明货币类型时的默认值。
        ret_format(str): 转换金额标准化的返回格式，包括 'str'|'detail' 两种，默认为 detail
            'str' 格式形如 “64000.00韩元”，
            'detail' 格式形如 “{'num': '64000.00', 'case': '韩元', 'definition': 'accurate'}”

    Returns:
        转换后指定格式的带`unit`的金额。

    Examples:
        >>> import jionlp as jio
        >>> money = "六十四万零一百四十三元一角七分"
        >>> print(jio.money_standardization(money))

        # "640143.17元"

    """
    def __init__(self):
        self.money_pattern_1 = None
        
    def _prepare(self):
        self.float_num_pattern = re.compile('\d+(\.)?\d*')
        self.punc_pattern = re.compile('[,， ]')
        self.wan_pattern = re.compile('万|萬')
        self.yi_pattern = re.compile('亿')
        self.chinese_yuan_currency_pattern = re.compile('(块钱|元|块)')
        self.chinese_jiao_currency_pattern = re.compile('(角|毛)')
        self.currency_case_pattern = re.compile(CURRENCY_CASE)
        # self.currency_case_pattern = re.compile(MONEY_SUFFIX_CASE_STRING)
        # self.chinese_kuai_jiao_mao_fen_pattern = re.compile(MONEY_KUAI_MAO_JIAO_FEN_STRING)

        self.money_modifier_pattern = re.compile(MONEY_PREFIX_STRING[:-1] + '|' + MONEY_SUFFIX_STRING[1:])

        # 判断货币金额精确度
        self.money_blur_pattern = re.compile(start_end(MONEY_BLUR_STRING))
        self.money_minus_pattern = re.compile(start_end(MONEY_MINUS_STRING))
        self.money_plus_pattern = re.compile(start_end(MONEY_PLUS_STRING))

        self.zero_seg_pattern = re.compile(r'0+\.00')

        # 纯数字的金额
        self.money_pattern_1 = re.compile(r'^\d+(\.)?\d*$')
        # 前为数字，后为汉字的金额
        self.money_pattern_2 = re.compile(r'^\d+(\.)?\d*[十拾百佰千仟万萬亿兆]{1,2}$')

        self.multi_nums = {
            '分': 0.01, '角': 0.1, '毛': 0.1, '十': 10, '拾': 10, 
            '百': 100, '佰': 100, '千': 1000, '仟': 1000, 
            '万': 10000, '萬': 10000, '亿': 100000000}
        self.plus_nums = {
            '〇': 0, 'O': 0, '零': 0, '０': 0,
            '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '壹': 1, '贰': 2, '俩': 2, '叁': 3, '弎': 3, '仨': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            '１': 0, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9,
        }
        self.suffix_nums = {
            '百': 100, '佰': 100, '千': 1000, '仟': 1000,
            '万': 10000, '萬': 10000, '亿': 100000000,
            '十万': 100000, '拾万': 100000, '百万': 1000000, '佰万': 1000000,
            '仟万': 10000000, '千万': 10000000, '万万': 100000000, '萬萬': 100000000,
            '十亿': 1000000000, '拾亿': 1000000000, '百亿': 10000000000, '佰亿': 10000000000,
            '千亿': 100000000000, '仟亿': 100000000000, '万亿': 1000000000000, '萬亿': 1000000000000,
            '兆': 1000000000000}

        self.standard_format = '{:.2f}'
        self.type_error_string = 'the given money_string `{}` is illegal.'
        
    def turn_num_standard_format(self, num):
        """将数字形式转换成`std_fmt`形式。
        使用该函数将数字形式转换成 `std_fmt` 形式。

        Args:
            num(int|str|float): 一个数字，支持 int 或 str 格式。

        Returns:
            转换后`std_fmt`形式的 str 类型的数字。

        Examples:
            >>> print(self.turn_num_standard_format(30.5))

            # '30.50'

        """
        standard_num = None

        if type(num) is str:
            if self.money_pattern_1.match(num):
                standard_num = self.standard_format.format(float(num))

        elif type(num) is int or type(num) is float:
            standard_num = self.standard_format.format(num)

        # else:
        #     raise TypeError('the type of `num` {} is not in [str, int, float].'.format(num))
            
        return standard_num

    def turn_money_std_fmt_util1(self, money_string):
        """将中文金额形式转换成 float 形式。处理以 “千百十个” 为核心的金额字符串。

        使用该函数将中文金额转换成易于计算的 float 形式，注意该函数是 turn_money_std_fmt
        辅助函数，只能方便将一万这种转换，一千万无法转换。

        Args:
            money_string: 一个中文格式表示的金额。

        Returns:
            转换后 float 类型的数字。

        """

        rtn_std_num = 0.0
        if not money_string or type(money_string) is not str:
            return rtn_std_num

        # 对 `十、百、千` 开头数字进行规范化
        if money_string[0] in '十拾百佰千仟':
            money_string = '一' + money_string

        # 对角、分进行规范化
        if self.chinese_yuan_currency_pattern.search(money_string):
            jiao_fen = self.chinese_yuan_currency_pattern.split(money_string)[-1]
            if self.chinese_jiao_currency_pattern.search(jiao_fen):
                fen = self.chinese_jiao_currency_pattern.split(jiao_fen)[-1]
                if '分' not in fen and len(fen) == 1:
                    # 分 字符串无“分”字且长度为 1
                    money_string = money_string + '分'
            else:
                if '角' not in jiao_fen and len(jiao_fen) == 1:
                    # 即 角分 字符串仅有一个字符，即角的数字
                    money_string = money_string + '角'

        # 检验字符串是否正确的中文金额
        # 两个除零外的 plus_num 不可以连续

        tmp_nums = list()
        for char in list(money_string):
            plus_num = self.plus_nums.get(char, 0)
            if plus_num != 0:
                tmp_nums.append(plus_num)

            multi_num = self.multi_nums.get(char, 1)
            if len(tmp_nums) >= 1:
                tmp_nums[-1] = tmp_nums[-1] * multi_num
                
        rtn_std_num = sum(tmp_nums)
        return rtn_std_num

    def turn_money_std_fmt_util2(self, money_string):
        """将中文金额形式转换成 float 形式。处理以 “万” 为核心的金额字符串

        使用该函数将中文金额转换成易于计算的 float 形式，注意该函数是 turn_money_std_fmt 的
        另一个辅助函数，与 turn_money_std_fmt_util1 搭配起来转换类似“1千万”数字。

        Args:
            money_string: 一个中文格式表示的金额。

        Returns:
            转换后 float 类型的数字。

        """
        if '万' in money_string or '萬' in money_string:
            if money_string[0] in '万萬':
                money_string = '一' + money_string

            seg_money_string = self.wan_pattern.split(money_string)
            if len(seg_money_string) == 2:
                prev, nxt = seg_money_string
                tmp_prev_num = self.turn_money_std_fmt_util1(prev)
                tmp_prev_num = tmp_prev_num * 10000
                tmp_nxt_num = self.turn_money_std_fmt_util1(nxt)
                rtn_std_num = tmp_prev_num + tmp_nxt_num
            else:
                raise ValueError(self.type_error_string.format(money_string))
        else:
            rtn_std_num = self.turn_money_std_fmt_util1(money_string)

        return rtn_std_num

    def turn_money_std_fmt_util3(self, money_string):
        """将中文金额形式转换成 float 形式。处理以 “亿” 为核心的金额字符串

        使用该函数将中文金额转换成易于计算的 float 形式，注意该函数是 turn_money_std_fmt 的
        另一个辅助函数，与 turn_money_std_fmt_util2 搭配起来转换类似“1千亿”数字。

        Args:
            money_string: 一个中文格式表示的金额。

        Returns:
            转换后 float 类型的数字。

        """
        if '亿' in money_string:
            if money_string.startswith('亿'):
                money_string = '一' + money_string

            seg_billion = self.yi_pattern.split(money_string)
            if len(seg_billion) == 2:
                prev, nxt = seg_billion
                prev_num = self.turn_money_std_fmt_util2(prev)
                nxt_num = self.turn_money_std_fmt_util2(nxt)
                rtn_std_num = prev_num * 100000000 + nxt_num

            else:
                raise ValueError(self.type_error_string.format(money_string))
        else:
            rtn_std_num = self.turn_money_std_fmt_util2(money_string)

        return rtn_std_num

    def _get_currency_case(self, money_string, default_unit='元'):
        """ 获取金额中的货币类型 """
        res_list = [item for item in self.currency_case_pattern.finditer(money_string)]

        if len(res_list) == 0:
            return default_unit, money_string  # 默认是人民币元
        elif len(res_list) in [1, 2]:
            # 即，要么是首词，要么是末尾词
            res = res_list[0]
            currency_unit = res.group()
            # 规定标准的货币类型
            if currency_unit in ['块钱', '人民币', '块', '元人民币']:
                unit = '元'
            elif currency_unit in ['港币', '元港币']:
                unit = '港元'
            elif currency_unit in ['日币', '元日币']:
                unit = '日元'
            elif currency_unit in ['韩币', '元韩币']:
                unit = '韩元'
            elif currency_unit in ['澳大利亚元', '澳币', '元澳币']:
                unit = '澳元'
            elif currency_unit in ['美刀', '美金']:
                unit = '美元'
            else:
                unit = currency_unit

            # 切去货币类型，保留数额，但不包括 角、分
            if len(res_list) == 1:
                if res.span()[1] == len(money_string) or res.span()[0] == 0:
                    # 货币在首部、或尾部
                    money_string = self.currency_case_pattern.sub('', money_string)
                    return unit, money_string
                else:
                    # 不在首部、尾部，说明尾部还有分、角等
                    return unit, money_string
            elif len(res_list) == 2:
                if res.span()[0] != 0:
                    raise ValueError(self.type_error_string.format(money_string))

                if res_list[1].span()[1] == len(money_string):
                    money_string = self.currency_case_pattern.sub('', money_string)
                    return unit, money_string
                else:
                    # 不在首部、尾部，说明尾部还有分、角等
                    money_string = self.currency_case_pattern.sub('', money_string, 1)
                    return unit, money_string

        else:
            raise ValueError(self.type_error_string.format(money_string))

    def _cleansing(self, money_string):
        # 去除其中的标点符号 ，,等
        money_string = self.punc_pattern.sub('', money_string)

        return money_string

    def _definition(self, money_string):
        """判断货币金额的精确度，为精确，或模糊"""

        modifiers = [item.group() for item in self.money_modifier_pattern.finditer(money_string)]

        if len(modifiers) == 0:
            minus_res, plus_res, blur_res = None, None, None
        elif len(modifiers) == 1:
            # 仅一个前缀或后缀
            blur_res = self.money_blur_pattern.search(modifiers[0])
            minus_res = self.money_minus_pattern.search(modifiers[0])
            plus_res = self.money_plus_pattern.search(modifiers[0])

        elif len(modifiers) == 2:
            # 分别有一个前缀和后缀
            blur_res_1 = self.money_blur_pattern.search(modifiers[0])
            minus_res_1 = self.money_minus_pattern.search(modifiers[0])
            plus_res_1 = self.money_plus_pattern.search(modifiers[0])
            blur_res_2 = self.money_blur_pattern.search(modifiers[1])
            minus_res_2 = self.money_minus_pattern.search(modifiers[1])
            plus_res_2 = self.money_plus_pattern.search(modifiers[1])

            blur_res = blur_res_1 or blur_res_2
            minus_res = minus_res_1 or minus_res_2
            plus_res = plus_res_1 or plus_res_2

        else:
            # 多余两个词缀，说明金额字符串有误
            raise ValueError(self.type_error_string.format(money_string))

        definition = 'accurate'
        if minus_res:  # 确定 minus_res 与 plus_res 不冲突，不同时 not None
            definition = 'blur-'
        elif plus_res:
            definition = 'blur+'
        elif blur_res:
            definition = 'blur'

        money_string = self.money_modifier_pattern.sub('', money_string)
        # print(modifiers)
        return money_string, definition

    def _accuracy(self, money_string, definition):
        """ 处理模糊金额，如 “六千多万日元”、“十几块钱”、“数十元”、“十多块钱” 等 """
        if '多' in money_string:
            money_string = money_string.replace('多', '')
            definition = 'blur+span'
            return money_string, definition,

        if '几' in money_string or '数' in money_string:
            if money_string[0] in '几数':
                money_string = money_string.replace('几', '').replace('数', '')
                definition = 'blur++span'
            else:
                money_string = money_string.replace('几', '').replace('数', '')
                definition = 'blur+span'
            return money_string, definition

        return money_string, definition

    def __call__(self, money_string, default_unit='元', ret_format='detail'):

        if self.money_pattern_1 is None:
            self._prepare()

        if not money_string:  # or len(money_string) == 1:
            raise ValueError(self.type_error_string.format(money_string))

        # 清洗字符串
        money_string = self._cleansing(money_string)

        # 判断金额精确粒度，并清除前置词汇和后置词汇
        money_string, definition = self._definition(money_string)

        # 判断货币类型
        unit, money_string = self._get_currency_case(money_string, default_unit=default_unit)

        # 处理模糊金额，如 “六千多万”、“十几块钱”、“数十元”、“十多块钱” 等
        money_string, definition = self._accuracy(money_string, definition)

        if money_string == '':
            raise ValueError(self.type_error_string.format(money_string))

        computed_money_num = 0.0
        if self.money_pattern_1.search(money_string):
            # 纯数字格式的金额，如 “549040.27”
            computed_money_num = float(money_string)

        elif self.money_pattern_2.search(money_string):
            # 前为数字，后为汉字的金额，如 “6000万”

            char_part = self.float_num_pattern.sub('', money_string)
            if char_part in self.suffix_nums:
                num_suffix = self.suffix_nums.get(char_part)
            else:
                raise ValueError(self.type_error_string.format(money_string))
            num_part = money_string.replace(char_part, '')

            if self.money_pattern_1.search(num_part):
                computed_money_num = float(num_part) * num_suffix
            else:
                raise ValueError(self.type_error_string.format(money_string))

        else:
            computed_money_num = self.turn_money_std_fmt_util3(money_string)

        # 金额标准化
        standard_money_num = self.turn_num_standard_format(computed_money_num)
        if standard_money_num is None:
            raise ValueError(self.type_error_string.format(money_string))

        standard_money_num_list = list()
        if 'span' in definition:
            if definition == 'blur+span':
                second_money_num = self._get_second_num(standard_money_num)
            elif definition == 'blur++span':
                second_money_num = self._get_second_num(standard_money_num, flag='++')

            standard_money_num_list = [standard_money_num, second_money_num]
            definition = 'blur'

        if ret_format == 'str':
            if len(standard_money_num_list) == 0:
                ret_money = standard_money_num + unit
            elif len(standard_money_num_list) == 2:
                ret_money = [standard_money_num_list[0] + unit, standard_money_num_list[1] + unit]
        elif ret_format == 'detail':
            if len(standard_money_num_list) == 0:
                ret_money = {'num': standard_money_num, 'case': unit, 'definition': definition}
            elif len(standard_money_num_list) == 2:
                ret_money = {'num': standard_money_num_list, 'case': unit, 'definition': definition}

        return ret_money

    def _get_second_num(self, num, flag='+'):
        if flag == '+':
            res = self.zero_seg_pattern.search(num)
            if res is not None:
                back_part = res.group()
                front_part = num.replace(back_part, '')
                new_front_part = str(int(front_part) + 1)
                return new_front_part + back_part
            else:
                return None
        elif flag == '++':
            num = float(num) * 10
            standard_money_num = self.turn_num_standard_format(num)
            return standard_money_num

