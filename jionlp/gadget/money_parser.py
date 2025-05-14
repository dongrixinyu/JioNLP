# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: www.jionlp.com


"""
TODO:
    - 某些金额为 合计/共/共计、共合计、合计共、共约1000元 类型。
    - 某些金额为单价类型，
        - 100 元每节课
        - 每桶油 1700 美元
        - 289.02 日元/本
    - 金额模糊表达
        - 五六百美元
    - 货币标识符
        - ￥5600、$85、€¥£、85,000$

"""

import re

from jionlp.util.funcs import start_end
from jionlp.rule.rule_pattern import CURRENCY_CASE, \
    MONEY_PREFIX_STRING, MONEY_SUFFIX_STRING, MONEY_BLUR_STRING, \
    MONEY_MINUS_STRING, MONEY_PLUS_STRING, MONEY_NUM_STRING, \
    MONEY_KUAI_MAO_JIAO_FEN_STRING, MONEY_NUM_MIDDLE_STRING
from jionlp.rule import extract_parentheses, remove_parentheses


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
        标准解析格式的金额（见下例）。

    Examples:
        >>> import jionlp as jio
        >>> money = "六十四万零一百四十三元一角七分"
        >>> print(jio.parse_money(money))

        # {'num': '640143.17元', 'definition': 'accurate', 'case': '元'}

    """
    def __init__(self):
        self.money_pattern_1 = None
        
    def _prepare(self):
        self.int_num_pattern = re.compile(r'\d+')
        self.float_num_pattern = re.compile(r'\d+(\.)?\d*')
        self.punc_pattern = re.compile(MONEY_NUM_MIDDLE_STRING)
        self.bai_pattern = re.compile('百|佰')
        self.qian_pattern = re.compile('千|仟|k')
        self.wan_pattern = re.compile('万|萬|w')
        self.yi_pattern = re.compile('亿')
        self.chinese_yuan_currency_pattern = re.compile('(块钱|元|块)')
        self.chinese_jiao_currency_pattern = re.compile('(角|毛)')
        self.currency_case_pattern = re.compile(CURRENCY_CASE)
        # self.currency_case_pattern = re.compile(MONEY_SUFFIX_CASE_STRING)
        # self.chinese_kuai_jiao_mao_fen_pattern = re.compile(MONEY_KUAI_MAO_JIAO_FEN_STRING)

        self.money_modifier_pattern = re.compile(
            MONEY_PREFIX_STRING[:-1] + '|' + MONEY_SUFFIX_STRING[1:])

        # 判断货币金额精确度
        self.money_blur_pattern = re.compile(start_end(MONEY_BLUR_STRING))
        self.money_minus_pattern = re.compile(start_end(MONEY_MINUS_STRING))
        self.money_plus_pattern = re.compile(start_end(MONEY_PLUS_STRING))

        self.zero_seg_pattern = re.compile(r'0+\.00')

        # 检测货币金额数值是否符合要求，不符合要求将直接报错，必须为数值字符与单位字符，可包括 角、分等
        self.money_num_string_pattern = re.compile(
            ''.join([MONEY_NUM_STRING[:-3], '元钱', MONEY_KUAI_MAO_JIAO_FEN_STRING[1:], '+$']))

        # 纯数字的金额
        self.money_pattern_1 = re.compile(r'^\d+(\.)?\d*$')
        # 前为数字，后为汉字的金额
        self.money_pattern_2 = re.compile(r'^\d+(\.)?\d*[十拾百佰k千仟w万萬亿兆]{1,2}$')

        # 金额范围抽取
        self.first_1_span_pattern = re.compile(
            r'(?<=(从))([^起到至\-—~]+)(?=(起|(?<![达不])到|至(?!少)|—|－|-|~))|'
            r'(?<=(从))([^起到至\-—~]+)')
        self.first_2_span_pattern = re.compile(r'(.+)(?=(——|--|~~|－－))')
        self.first_3_span_pattern = re.compile(r'([^起到至\-—~]+)(?=(起|(?<![达不])到|至(?!少)|－|—|-|~))')

        self.second_0_span_pattern = re.compile(r'(?<=(——|--|~~|－－))(.+)')
        self.second_1_span_pattern = re.compile(r'(?<=(起|(?<![达不])到|至(?!少)|\-|—|\~|－))([^起到至\-—~－]+)')

        self.multi_nums = {
            '分': 0.01, '角': 0.1, '毛': 0.1, '十': 10, '拾': 10, 
            '百': 100, '佰': 100, '千': 1000, '仟': 1000, 
            '万': 10000, '萬': 10000, '亿': 100000000}
        self.plus_nums = {
            '〇': 0, 'O': 0, '零': 0, '０': 0,
            '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9,
            '壹': 1, '弌': 1, '贰': 2, '弍': 2, '俩': 2, '叁': 3, '弎': 3, '仨': 3, '肆': 4, '伍': 5, '陆': 6, '柒': 7, '捌': 8, '玖': 9,
            '1': 1, '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9,
            '１': 0, '２': 2, '３': 3, '４': 4, '５': 5, '６': 6, '７': 7, '８': 8, '９': 9,
        }
        self.suffix_nums = {
            '百': 100, '佰': 100, '千': 1000, '仟': 1000, 'k': 1000,
            '万': 10000, '萬': 10000, 'w': 10000, '亿': 100000000,
            '十万': 100000, '拾万': 100000, '百万': 1000000, '佰万': 1000000,
            '仟万': 10000000, '千万': 10000000, '万万': 100000000, '萬萬': 100000000,
            '十亿': 1000000000, '拾亿': 1000000000, '百亿': 10000000000, '佰亿': 10000000000,
            '千亿': 100000000000, '仟亿': 100000000000, '万亿': 1000000000000, '萬亿': 1000000000000,
            '兆': 1000000000000}

        self.sequential_char_num_pattern = re.compile(
            r'(一二|二三|两三|三四|三五|四五|五六|六七|七八|八九|'
            r'壹贰|弌弍|贰叁|贰弎|弍弎|贰仨|两叁|两弎|两仨|叁肆|弎肆|仨肆|叁伍|弎伍|仨伍|肆伍|伍陆|陆柒|柒捌|捌玖)')

        self.alias_RMB_case = {'块钱人民币', '块钱', '人民币', '块', '元人民币', '圆', '圆整'}
        self.alias_HK_case = {'港币', '元港币'}
        self.alias_JP_case = {'日币', '元日币'}
        self.alias_KR_case = {'韩币', '元韩币'}
        self.alias_TW_case = {'台币', '元新台币', '元台币'}
        self.alias_AUS_case = {'澳大利亚元', '澳币', '元澳币'}
        self.alias_USA_case = {'美刀', '美金'}

        self.standard_format = '{:.2f}'
        self.type_error = 'the given money_string `{}` is illegal.'
        
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

        # TODO: 检验字符串是否正确的中文金额
        # 两个除零外的 plus_num 不可以连续

        # 此时，角分确定了，但是 元 之前的金额形式仍未确定，并不一定是中文汉字形式.
        yuan = self.chinese_yuan_currency_pattern.split(money_string)[0]
        jiao_fen = self.chinese_yuan_currency_pattern.split(money_string)[-1]

        # 第一种情况：整数金额全是阿拉伯数字，如 `123元1角1分`
        matched_res = self.int_num_pattern.search(yuan)
        if matched_res and (matched_res.span()[0] == 0) and (matched_res.span()[1] == len(yuan)):
            yuan_number = int(yuan)
            jiao_fen_number = self.compute_plus_multi(jiao_fen)

            return yuan_number + jiao_fen_number

        else:
            return self.compute_plus_multi(money_string)

    def compute_plus_multi(self, money_string):
        tmp_nums = []
        for char in list(money_string):
            plus_num = self.plus_nums.get(char, 0)
            if plus_num != 0:
                tmp_nums.append(plus_num)

            multi_num = self.multi_nums.get(char, 1)
            if len(tmp_nums) >= 1:
                tmp_nums[-1] = tmp_nums[-1] * multi_num
                
        standard_num = sum(tmp_nums)
        return standard_num

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
                raise ValueError(self.type_error.format(money_string))
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
                raise ValueError(self.type_error.format(money_string))
        else:
            rtn_std_num = self.turn_money_std_fmt_util2(money_string)

        return rtn_std_num

    def _get_currency_case(self, money_string, default_unit='元'):
        """ 获取金额中的货币类型 """
        res_list = [item for item in self.currency_case_pattern.finditer(money_string)]

        if len(res_list) == 0:
            return default_unit, money_string  # 默认是人民币元

        elif len(res_list) in {1, 2}:
            # 存在一种特殊情况，即 “三万元欧元”，可以得到 res_list 长度为2，但它其实只属于欧元
            matched_case = False
            if len(res_list) == 2:
                first_res = res_list[0]
                second_res = res_list[1]
                if first_res.group() == '元' and (first_res.span()[1] == second_res.span()[0]):
                    matched_case = True
                    # 第一个字符是 元，且两个单位相邻，则选取后一个单位作为真正的货币单位
                    unit = second_res.group()
                    money_string = money_string.replace('元', '', 1)
                    money_string = self.currency_case_pattern.sub('', money_string)
                    return unit, money_string

            if not matched_case:
                # 除此之外，它按以下条件进行解析
                # 即，要么是首词，要么是末尾词
                res = res_list[0]
                currency_unit = res.group()
                # 规定标准的货币类型
                if currency_unit in self.alias_RMB_case:
                    unit = '元'
                elif currency_unit in self.alias_HK_case:
                    unit = '港元'
                elif currency_unit in self.alias_JP_case:
                    unit = '日元'
                elif currency_unit in self.alias_KR_case:
                    unit = '韩元'
                elif currency_unit in self.alias_TW_case:
                    unit = '新台币'
                elif currency_unit in self.alias_AUS_case:
                    unit = '澳元'
                elif currency_unit in self.alias_USA_case:
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
                        # 若字符串中还不包含 分角毛 等字符，说明这个金额文本有误，如“70000元 2022”
                        if ('分' not in money_string) and ('角' not in money_string) and ('毛' not in money_string):
                            raise ValueError(self.type_error.format(money_string))
                        return unit, money_string

                elif len(res_list) == 2:
                    if res.span()[0] != 0:
                        raise ValueError(self.type_error.format(money_string))

                    if res_list[1].span()[1] == len(money_string):
                        money_string = self.currency_case_pattern.sub('', money_string)
                        return unit, money_string

                    else:
                        # 不在首部、尾部，说明尾部还有分、角等
                        # 若字符串中还不包含 分角毛 等字符，说明这个金额文本有误，如“70000元 2022”
                        if ('分' not in money_string) and ('角' not in money_string) and ('毛' not in money_string):
                            raise ValueError(self.type_error.format(money_string))

                        money_string = self.currency_case_pattern.sub('', money_string, 1)
                        return unit, money_string

        else:
            raise ValueError(self.type_error.format(money_string))

    def _cleansing(self, money_string):
        # 去除其中的标点符号 ，,等
        money_string = self.punc_pattern.sub('', money_string)

        # 去除其中的括号，如 “50万元（含）以上”
        sub_parentheses = extract_parentheses(money_string, parentheses='()（）')
        if '含' in ''.join(sub_parentheses):
            money_string = remove_parentheses(money_string, parentheses='()（）')

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
            raise ValueError(self.type_error.format(money_string))

        definition = 'accurate'
        if minus_res:  # 确定 minus_res 与 plus_res 不冲突，不同时 not None
            definition = 'blur-'
        elif plus_res:
            definition = 'blur+'
        elif blur_res:
            definition = 'blur'

        money_string = self.money_modifier_pattern.sub('', money_string)
        return money_string, definition

    def _accuracy(self, money_string, definition):
        """ 处理模糊金额，如 “六千多万日元”、“十几块钱”、“数十元”、“十多块钱” 等 """
        if '多' in money_string:
            money_string = money_string.replace('多', '')
            definition = 'blur+span'
            return money_string, definition

        if '余' in money_string:
            money_string = money_string.replace('余', '')
            definition = 'blur+span'
            return money_string, definition

        if '几' in money_string or '数' in money_string:
            if money_string[0] in '几数':
                money_string = money_string.replace('几', '').replace('数', '')
                definition = 'blur++span'
            else:
                money_string = money_string.replace('几', '').replace('数', '')
                definition = 'blur+span'
            return money_string, definition

        return money_string, definition

    def _expand_sequential_string(self, money_string):
        """ 对某些字符串进行扩展，如 “五六百美元” 需要扩展为 “五到六百美元” """
        if self.sequential_char_num_pattern.search(money_string):
            sequential_string = self.sequential_char_num_pattern.search(money_string).group()
            money_string_pattern = self.sequential_char_num_pattern.sub('{}', money_string)
            sub_token = sequential_string[0] + '到' + sequential_string[1]
            money_string = money_string_pattern.format(sub_token)

        return money_string

    def _split_money_span(self, money_string):
        """检测字符串，并将其分解为两个 money """
        # 找第一个字符串
        if self.first_1_span_pattern.search(money_string):
            first_res = self.first_1_span_pattern.search(money_string)
        elif self.first_2_span_pattern.search(money_string):
            first_res = self.first_2_span_pattern.search(money_string)
        elif self.first_3_span_pattern.search(money_string):
            first_res = self.first_3_span_pattern.search(money_string)
        else:
            first_res = None

        first_string = None if first_res is None else first_res.group()

        # 找第二个字符串
        if self.second_0_span_pattern.search(money_string):
            second_res = self.second_0_span_pattern.search(money_string)
        elif self.second_1_span_pattern.search(money_string):
            second_res = self.second_1_span_pattern.search(money_string)
        else:
            second_res = None

        second_string = None if second_res is None else second_res.group()

        return first_string, second_string

    def _compensate_first_money_string(
            self, first_money_string, second_money_string):
        """ 根据情况，对金额范围的第一个金额进行单位补全
        例如： 3到5万港币，被拆分为 3，5万港币，须将 3 补全为 3万港币
        思路：第二个字符串一般为完全字符串，不须补全，
            且默认第二个字符串是 数字、汉字单位混合字符串，
            此时考察第一个字符串，若其数值低于 第二个字符串的数字值，
            则为其添加第二个字符串的汉字单位。

        TODO:该函数有较多错误和纰漏。

            十八到三十万元
            一百二十到一百五十万元
            一千到两千万元
            一千到两千亿元
            三到五百
            八到九千
        """
        # 先分析第一个字符串的金额，确定其信息，是否需要补全
        if self.money_pattern_1.search(first_money_string):
            first_computed_money_num = float(first_money_string)

        elif self.money_pattern_2.search(first_money_string):
            # 前为数字，后为汉字的金额，如 “6000万”
            # 若第一个字符串属于该种类型，且其 char_part 非空，说明可以直接返回
            char_part = self.float_num_pattern.sub('', first_money_string)
            if char_part in self.suffix_nums:
                return first_money_string
            else:
                raise ValueError(self.type_error.format(first_money_string))

        else:
            # 若第一个字符串有单位，则直接返回结果
            res_list = [item for item in self.currency_case_pattern.finditer(first_money_string)]

            if len(res_list) != 0:
                # 有货币单位
                if res_list[-1].span()[1] == len(first_money_string):
                    # 即第一个字符串末尾为单位，则直接跳过
                    return first_money_string

            first_computed_money_num = self.turn_money_std_fmt_util3(first_money_string)

        # 前置操作，需要重复执行一次，因此较为耗时
        second_money_string = self._cleansing(second_money_string)
        second_money_string, definition = self._definition(second_money_string)
        unit, second_money_string = self._get_currency_case(second_money_string)
        second_money_string, definition = self._accuracy(second_money_string, definition)

        # 分析第二个字符串的类型，并按类型对其进行判断，是否对第一个字符串添加信息
        if self.money_pattern_2.search(second_money_string):
            char_part = self.float_num_pattern.sub('', second_money_string)
            if char_part not in self.suffix_nums:
                raise ValueError(self.type_error.format(second_money_string))

            num_part = second_money_string.replace(char_part, '')
            if self.money_pattern_1.search(num_part):
                second_computed_money_num = float(num_part)
            else:
                raise ValueError(self.type_error.format(second_money_string))

            if first_computed_money_num < second_computed_money_num:
                # 此时需要添加单位
                return first_money_string + char_part
            else:
                return first_money_string

        else:
            if self.yi_pattern.search(second_money_string):
                seg_billion = self.yi_pattern.split(second_money_string)
                if len(seg_billion) == 2:
                    second_computed_money_num = self.turn_money_std_fmt_util2(seg_billion[0])
                else:
                    raise ValueError(self.type_error.format(second_money_string))

                if first_computed_money_num < second_computed_money_num:
                    return first_money_string + '亿'
                else:
                    return first_money_string

            elif self.wan_pattern.search(second_money_string):
                seg_wan = self.wan_pattern.split(second_money_string)
                if len(seg_wan) == 2:
                    second_computed_money_num = self.turn_money_std_fmt_util1(seg_wan[0])
                else:
                    raise ValueError(self.type_error.format(second_money_string))

                if first_computed_money_num < second_computed_money_num:
                    return first_money_string + '万'
                else:
                    return first_money_string

            elif self.qian_pattern.search(second_money_string):
                seg_qian = self.qian_pattern.split(second_money_string)
                if len(seg_qian) == 2:
                    second_computed_money_num = self.turn_money_std_fmt_util1(seg_qian[0])
                else:
                    raise ValueError(self.type_error.format(second_money_string))

                if first_computed_money_num < second_computed_money_num:
                    return first_money_string + '千'
                else:
                    return first_money_string
            elif self.bai_pattern.search(second_money_string):
                seg_bai = self.bai_pattern.split(second_money_string)
                if len(seg_bai) == 2:
                    second_computed_money_num = self.turn_money_std_fmt_util1(seg_bai[0])
                else:
                    raise ValueError(self.type_error.format(second_money_string))

                if first_computed_money_num < second_computed_money_num:
                    return first_money_string + '百'
                else:
                    return first_money_string

            return first_money_string

    def __call__(self, money_string, default_unit='元', ret_format='detail'):

        if self.money_pattern_1 is None:
            self._prepare()

        if not money_string:  # or len(money_string) == 1:
            raise ValueError(self.type_error.format(money_string))

        # 若检测到需要扩展的类型，如 “五六百美元” 需要扩展为 “五到六百美元”
        money_string = self._expand_sequential_string(money_string)

        first_money_string, second_money_string = self._split_money_span(money_string)

        if first_money_string is None or second_money_string is None:
            # 按单金额字符串返回
            return self.parse_single_money(
                money_string, default_unit=default_unit, ret_format=ret_format)

        else:
            first_money_string = self._compensate_first_money_string(
                first_money_string, second_money_string)

            first_money_res = self.parse_single_money(
                first_money_string, default_unit=default_unit, ret_format=ret_format)
            second_money_res = self.parse_single_money(
                second_money_string, default_unit=default_unit, ret_format=ret_format)

            # 将两个货币金额合并
            if ret_format == 'str':
                if type(first_money_res) is str and type(second_money_res) is str:
                    ret_money = [first_money_res, second_money_res]
                elif type(first_money_res) is str and type(second_money_res) is list:
                    ret_money = [first_money_res, second_money_res[1]]
                elif type(first_money_res) is list and type(second_money_res) is str:
                    ret_money = [first_money_res[0], second_money_res]
                elif type(first_money_res) is list and type(second_money_res) is list:
                    ret_money = [first_money_res[0], second_money_res[1]]

            elif ret_format == 'detail':
                first_unit = first_money_res['case']
                second_unit = second_money_res['case']

                if second_unit != '元':
                    unit = second_unit
                elif first_unit != '元':
                    unit = first_unit
                else:
                    unit = '元'

                definition = 'blur'

                if type(first_money_res['num']) is str and type(second_money_res['num']) is str:
                    ret_money = [first_money_res['num'], second_money_res['num']]
                elif type(first_money_res['num']) is str and type(second_money_res['num']) is list:
                    ret_money = [first_money_res['num'], second_money_res['num'][1]]
                elif type(first_money_res['num']) is list and type(second_money_res['num']) is str:
                    ret_money = [first_money_res['num'][0], second_money_res['num']]
                elif type(first_money_res['num']) is list and type(second_money_res['num']) is list:
                    ret_money = [first_money_res['num'][0], second_money_res['num'][1]]

                ret_money = {'num': ret_money, 'case': unit, 'definition': definition}

            return ret_money

    def parse_single_money(self, money_string, default_unit='元', ret_format='detail'):
        """ 解析单个金额字符串，可由解析两个组成金额范围 """

        # 清洗字符串
        money_string = self._cleansing(money_string)

        # 判断金额精确粒度，并清除前置词汇和后置词汇
        money_string, definition = self._definition(money_string)

        # 判断货币类型
        unit, money_string = self._get_currency_case(money_string, default_unit=default_unit)

        # 处理模糊金额，如 “六千多万”、“十几块钱”、“数十元”、“十多块钱”、“2000余元” 等
        money_string, definition = self._accuracy(money_string, definition)

        if money_string == '':
            raise ValueError(self.type_error.format(money_string))

        # 若货币的金额字符串部分有误，则报错返回。
        if self.money_num_string_pattern.search(money_string) is None:
            raise ValueError(self.type_error.format(money_string))

        if self.money_pattern_1.search(money_string):
            # 纯数字格式的金额，如 “549040.27”
            computed_money_num = float(money_string)

        elif self.money_pattern_2.search(money_string):
            # 前为数字，后为汉字的金额，如 “6000万”

            char_part = self.float_num_pattern.sub('', money_string)
            if char_part in self.suffix_nums:
                num_suffix = self.suffix_nums.get(char_part)
            else:
                raise ValueError(self.type_error.format(money_string))

            num_part = money_string.replace(char_part, '')
            if self.money_pattern_1.search(num_part):
                computed_money_num = float(num_part) * num_suffix
            else:
                raise ValueError(self.type_error.format(money_string))

        else:
            computed_money_num = self.turn_money_std_fmt_util3(money_string)

        # 金额标准化
        standard_money_num = self.turn_num_standard_format(computed_money_num)
        if standard_money_num is None:
            raise ValueError(self.type_error.format(money_string))

        standard_money_num_list = []
        if 'span' in definition:
            if definition == 'blur+span':
                second_money_num = self._get_second_num(standard_money_num)
            elif definition == 'blur++span':
                second_money_num = self._get_second_num(standard_money_num, flag='++')

            standard_money_num_list = [standard_money_num, second_money_num]
            definition = 'blur'

        # 组织返回格式
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

