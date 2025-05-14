# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
给定一条数字金额，返回其汉字大写结果
"""

import re


class MoneyNum2Char(object):
    """ 给定一条数字金额，返回其汉字大写结果。

    Args:
        num(int|float|str): 数字金额
        sim_or_tra(str): 可选 'sim' 或 'tra'，控制汉字类型，默认为 'tra'

    Returns:
        str: 汉字金额

    Examples:
        >>> import jionlp as jio
        >>> num = 120402810.03
        >>> print(jio.money_num2char(num, sim_or_tra='tra'))
        >>> num = '38,009.0'
        >>> print(jio.money_num2char(num, sim_or_tra='sim'))

        # 壹亿贰仟零肆拾萬贰仟捌佰壹拾點零叁
        # 三万八千零九

    """
    def __init__(self):
        self.integer_pattern = None

    def _prepare(self):
        self.simplified_num_char = {
            '0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
            '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}
        self.traditional_num_char = {
            '0': '零', '1': '壹', '2': '贰', '3': '叁', '4': '肆',
            '5': '伍', '6': '陆', '7': '柒', '8': '捌', '9': '玖'}

        self.simplified_inner_suffix = {
            3: '千', 2: '百', 1: '十', 0: ''}
        self.simplified_outer_suffix = {
            0: '', 1: '万', 2: '亿', 3: '兆'}
        self.traditional_inner_suffix = {
            3: '仟', 2: '佰', 1: '拾', 0: ''}
        self.traditional_outer_suffix = {
            0: '', 1: '萬', 2: '亿', 3: '兆'}
        self.money_char = {1: '分', 0: '角'}
        self.integer_pattern = re.compile(r'(\d+)\.')
        self.float_pattern = re.compile(r'\.(\d+)')

        self.zero_cut_pattern = re.compile('零+$')
        self.zero_shorten_pattern = re.compile('零+')
        self.zero_delete_pattern = re.compile('^0+$')
        self.sim_deci_start_pattern = re.compile('^(一十)')
        self.tra_deci_start_pattern = re.compile('^(壹拾)')

    def __call__(self, num, sim_or_tra='tra'):
        """ 调用函数 """
        if self.integer_pattern is None:
            self._prepare()

        integer_part = None
        float_part = None
        if type(num) is int:
            num_string = str(num)
            integer_part = num_string
        elif type(num) is float:
            num_string = str(num)
            integer_part = self.integer_pattern.search(num_string).group(1)
            float_part = self.float_pattern.search(num_string).group(1)
        elif type(num) is str:
            num_string = num.replace(',', '')
            if '.' not in num_string:
                integer_part = num_string
            else:
                integer_part = self.integer_pattern.search(num_string).group(1)
                float_part = self.float_pattern.search(num_string).group(1)

        integer_seg_list = self._seg_integer_part(integer_part)

        integer_char_list = list()
        for idx, seg in enumerate(range(len(integer_seg_list) - 1, -1, -1)):
            seg_char = self._parse_integer_seg(integer_seg_list[idx], sim_or_tra=sim_or_tra)
            if sim_or_tra == 'sim':
                integer_char_list.append(seg_char + self.simplified_outer_suffix[seg])
            elif sim_or_tra == 'tra':
                integer_char_list.append(seg_char + self.traditional_outer_suffix[seg])

        integer_string = ''.join(integer_char_list)

        if float_part is not None:
            matched = self.zero_delete_pattern.match(float_part[:2])
            if matched is not None:
                return integer_string

            float_string = self._float2string(
                float_part[:2], sim_or_tra=sim_or_tra)
            if sim_or_tra == 'sim':
                dot_string = '点'
            elif sim_or_tra == 'tra':
                dot_string = '點'

            return integer_string + dot_string + float_string
        return integer_string

    @staticmethod
    def _seg_integer_part(integer_part):
        """ 将整数转换为每 4 个一节 """
        seg_list = list()
        flag = len(integer_part) % 4
        if len(integer_part) % 4 != 0:
            first_part = integer_part[:flag]
            seg_list.append(first_part)

        for i in range(flag, len(integer_part), 4):
            seg_list.append(integer_part[i: i+4])

        return seg_list

    def _parse_integer_seg(self, integer_seg, sim_or_tra='sim'):
        """ 将整数的每 4 个一节转换为汉字 """
        thousand = ''
        hundred = ''
        deci = ''
        enum = ''
        for idx, i in enumerate(range(len(integer_seg) - 1, -1, -1)):
            if idx == 0:
                if integer_seg[i] == '0':
                    enum = ''
                else:
                    if sim_or_tra == 'sim':
                        enum = self.simplified_num_char[integer_seg[i]]
                    elif sim_or_tra == 'tra':
                        enum = self.traditional_num_char[integer_seg[i]]
            elif idx == 1:
                if integer_seg[i] == '0':
                    deci = '零'
                else:
                    if sim_or_tra == 'sim':
                        deci = self.simplified_num_char[integer_seg[i]] + '十'
                    elif sim_or_tra == 'tra':
                        deci = self.traditional_num_char[integer_seg[i]] + '拾'
            elif idx == 2:
                if integer_seg[i] == '0':
                    hundred = '零'
                else:
                    if sim_or_tra == 'sim':
                        hundred = self.simplified_num_char[integer_seg[i]] + '百'
                    elif sim_or_tra == 'tra':
                        hundred = self.traditional_num_char[integer_seg[i]] + '佰'
            elif idx == 3:
                if integer_seg[i] == '0':
                    thousand = '零'
                else:
                    if sim_or_tra == 'sim':
                        thousand = self.simplified_num_char[integer_seg[i]] + '千'
                    elif sim_or_tra == 'tra':
                        thousand = self.traditional_num_char[integer_seg[i]] + '仟'

        tmp_res = ''.join([thousand, hundred, deci, enum])
        tmp_res = self.zero_cut_pattern.sub('', tmp_res)
        tmp_res = self.zero_shorten_pattern.sub('零', tmp_res)
        if sim_or_tra == 'sim':
            tmp_res = self.sim_deci_start_pattern.sub('十', tmp_res)
        elif sim_or_tra == 'tra':
            tmp_res = self.tra_deci_start_pattern.sub('拾', tmp_res)

        return tmp_res

    def _float2string(self, float_part, sim_or_tra='sim'):
        """ 将小数转换为汉字，并仅截取两位（金额只保留 2 位） """
        float_string_list = list()
        for i in float_part:
            if sim_or_tra == 'sim':
                float_string_list.append(self.simplified_num_char[i])
            elif sim_or_tra == 'tra':
                float_string_list.append(self.traditional_num_char[i])

        float_string = ''.join(float_string_list)
        return float_string

