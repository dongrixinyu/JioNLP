# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
TODO:
    - "2021年4月20日11:00时至2021年4月25日17:00时" 无法被正确抽取，原因在于 “时” 字与规则多余，
        与 "string_strict" 相悖。
    - ”据预测，到2025年，全球数据“ 无法将 到 识别出来
    - ”机怎么了：9年间四个子品“ 中，”9年间“ 无法被抽取，会抽取得到 ”9年“

"""


import re
import time

from jionlp.rule.rule_pattern import TIME_CHAR_STRING, \
    FAKE_POSITIVE_START_STRING, FAKE_POSITIVE_END_STRING
from jionlp.gadget.time_parser import TimeParser


class TimeExtractor(object):
    """ 时间实体抽取器。不依赖模型，将文本中的时间实体进行抽取，并对其做时间语义解析。

    - TODO: ”2000“ 此类时间表达容易与某些金额、数量单位造成混淆，如”2000万美金“，”2000多台发动机“，因此需要
        首先考虑数量词表达，在2000非数量表达的情况下，再判定为 ”2000年“ 进行返回。
        目前就简，按四位数后是否有 ”万、亿、多万、多亿“ 进行判断，单位抽取与解析完成后再修复完整版。
    - 默认大概率非时间含义的时间表达默认不进行返回。
    - 若文本中包含 ”的“ 字，则在 parse_time 之前，先将此字消除后再进行解析。

    Args:
        text(str): 输入待抽取时间实体的文本
        time_base(int|datetime|dict|list): 若对文本中的时间实体进行语义解析，则须指定解析的时间基，默认为当前时间 time.time()
        with_parsing(bool): 指示返回结果是否包含解析信息，默认为 True
        ret_all(bool): 某些时间表达，在大多数情况下并非表达时间，如 ”一点“ 之于 ”他一点也不友善“，默认按绝大概率处理，
            即不返回此类伪时间表达，该参数默认为 False；若希望返回所有抽取到的时间表达，须将该参数置 True。

    Returns:
        list(dict): 包含时间实体的列表，其中包括 text、type、offset 三个字段，和工具包中 NER 标准处理格式一致。

    Example：
        >>> import jionlp as jio
        >>> text = '8月临近尾声，中秋、国庆两个假期已在眼前。2021年中秋节是9月21日，星期二。'
                    有不少小伙伴翻看放假安排后，发现中秋节前要"补"假。
                    记者注意到，根据放假安排，9月18日（星期六）上班，9月19日至21日放假调休，也就是从周日开始放假3天。
                    由于中秋节后上班不到 10天，又将迎来一个黄金周—国庆长假，因此工作也就"安排"上了。
                    双节来袭，仍有人要坚守岗位。'
        >>> res = jio.ner.extract_time(text, time_base=time.time(), with_parsing=False)
        >>> print(res)
            {'text': '8月', 'offset': [41, 43], 'type': 'time_point'}
            {'text': '中秋', 'offset': [48, 50], 'type': 'time_point'}
            {'text': '国庆', 'offset': [51, 53], 'type': 'time_point'}
            {'text': '2021年中秋节', 'offset': [62, 70], 'type': 'time_point'}
            {'text': '9月21日', 'offset': [71, 76], 'type': 'time_point'}
            {'text': '星期二', 'offset': [77, 80], 'type': 'time_point'}
            {'text': '中秋节前', 'offset': [98, 102], 'type': 'time_span'}
            {'text': '9月18日', 'offset': [136, 141], 'type': 'time_point'}
            {'text': '星期六', 'offset': [142, 145], 'type': 'time_point'}
            {'text': '9月19日至21日', 'offset': [149, 158], 'type': 'time_span'}

    """
    def __init__(self):
        self.parse_time = None

    def _prepare(self):
        self.parse_time = TimeParser()
        self.time_string_pattern = re.compile(TIME_CHAR_STRING)  # 该正则存在假阴风险

        self.fake_positive_start_pattern = re.compile(FAKE_POSITIVE_START_STRING)
        self.fake_positive_end_pattern = re.compile(FAKE_POSITIVE_END_STRING)

        # 此类表达虽然可按时间解析，但是文本中很大概率并非表示时间，故以大概率进行排除，
        # 并设参数 ret_all，即返回所有进行控制，默认为 False，即根据词典进行删除
        self.non_time_string_list = ['一点', '0时']

        self.four_num_year_pattern = re.compile(r'^[\d]{4}$')
        self.unit_pattern = re.compile(r'(多)?[万亿元]')  # 四数字后接单位，说明非年份

        self.single_char_time = ['春', '夏', '秋', '冬']

    def __call__(self, text, time_base=time.time(), with_parsing=True,
                 ret_all=False):
        if self.parse_time is None:
            self._prepare()

        candidates_list = self.extract_time_candidates(text)

        time_entity_list = list()
        for candidate in candidates_list:
            offset = [0, 0]
            bias = 0
            while candidate['offset'][0] + offset[1] < candidate['offset'][1]:
                # 此循环意在找出同一个 candidate 中包含的多个 time_entity

                true_string, result, offset = self.grid_search(
                    candidate['time_candidate'][bias:])

                if true_string is not None:

                    # rule 1: 判断字符串是否为大概率非时间语义
                    if (true_string in self.non_time_string_list) and (not ret_all):
                        bias += offset[1]
                        continue

                    # rule 2: 判断四数字 ”2033“ 是否后接货币、非年份量词
                    if self.four_num_year_pattern.search(true_string):
                        back_start = candidate['offset'][0] + bias + offset[1]
                        if self.unit_pattern.search(text[back_start: back_start + 2]):
                            # 说明非真实年份，跳回
                            bias += offset[1]
                            continue

                    if with_parsing:
                        time_entity_list.append(
                            {'text': true_string,
                             'offset': [candidate['offset'][0] + bias + offset[0],
                                        candidate['offset'][0] + bias + offset[1]],
                             'type': result['type'],
                             'detail': result})
                    else:
                        time_entity_list.append(
                            {'text': true_string,
                             'offset': [candidate['offset'][0] + bias + offset[0],
                                        candidate['offset'][0] + bias + offset[1]],
                             'type': result['type']})
                    bias += offset[1]
                else:
                    break

        # for item in time_entity_list:
        #     assert item['text'] == text[item['offset'][0]: item['offset'][1]]
        #     print(item)
        return time_entity_list

    def _filter(self, sub_string):
        """ 对某些易造成实体错误的字符进行过滤。
        此问题产生的原因在于，parse_time 工具对某些不符合要求的字符串也能成功解析，造成假阳性。
        """
        if self.fake_positive_start_pattern.search(sub_string[0]):
            return False

        if self.fake_positive_end_pattern.search(sub_string[-1]):
            return False

        if len(sub_string) != len(sub_string.strip()):
            return False

        # 的 不可以在句首或句尾
        if '的' in sub_string[0] or '的' in sub_string[-1]:
            return False

        return True

    def _grid_search_1(self, time_candidate):
        """ 取消 parse_time 中 strict 限制，从长至短，先左后右依次缩短 time_candidate，
        直到解析错误或解析结果出错
        """

    def grid_search(self, time_candidate):
        """ 全面搜索候选时间字符串，从长至短，较优 """
        length = len(time_candidate)
        for i in range(length):  # 控制总长，若想控制单字符的串也被返回考察，此时改为 length + 1
            for j in range(i):  # 控制偏移
                try:
                    offset = [j, length - i + j + 1]
                    sub_string = time_candidate[j: offset[1]]

                    # 处理假阳性。检查子串，对某些产生歧义的内容进行过滤。
                    # 原因在于，parse_time 会对某些不符合要求的字符串做正确解析.
                    if not self._filter(sub_string):
                        continue

                    # rule 3: 若子串中包含 ”的“ 字会对结果产生影响，则先将 ”的“ 字删除后再进行解析。
                    sub_string_for_parse = sub_string.replace('的', '')
                    result = self.parse_time(sub_string_for_parse, strict=True)

                    return sub_string, result, offset
                except (ValueError, Exception):
                    continue

        return None, None, None

    def _grid_search_2(self, time_candidate):
        """ 全面搜索候选时间字符串，从前至后，从长至短 """
        print(time_candidate)
        length = len(time_candidate)
        for i in range(length - 1):  # 控制起始点
            for j in range(length, i, -1):  # 控制终止点
                try:
                    offset = [i, j]
                    sub_string = time_candidate[i: j]
                    print(sub_string)
                    # 处理假阳性。检查子串，对某些产生歧义的内容进行过滤。
                    # 原因在于，parse_time 会对某些不符合要求的字符串做正确解析.
                    if not TimeExtractor._filter(sub_string):
                        continue

                    result = self.parse_time(sub_string, strict=True)

                    return sub_string, result, offset
                except (ValueError, Exception):
                    continue

        return None, None, None

    def extract_time_candidates(self, text):
        """ 获取所有的候选时间字符串，其中包含了时间实体 """
        text_length = len(text)
        idx_count = 0
        time_candidates_list = list()
        while idx_count < text_length:
            matched_res = self.time_string_pattern.search(text[idx_count:])
            # print(matched_res)
            if matched_res is not None:
                if len(matched_res.group()) > 1:
                    time_candidates_list.append(
                        {'time_candidate': matched_res.group(),
                         'offset': [idx_count + matched_res.span()[0],
                                    idx_count + matched_res.span()[1]]})
                elif matched_res.group() in self.single_char_time:
                    # 可能误打 “春”、“夏” 等单字符时间表达，故在此加入
                    time_candidates_list.append(
                        {'time_candidate': matched_res.group(),
                         'offset': [idx_count + matched_res.span()[0],
                                    idx_count + matched_res.span()[1]]})
                idx_count += matched_res.span()[1]
            else:
                break

        return time_candidates_list


if __name__ == '__main__':
    text = '''【标题：中秋国庆双节都加班，可拿24天的日工资】
        8月临近尾声，中秋、国庆两个假期已在眼前。2021年中秋节是9月21日，星期二。 有不少小伙伴翻看放假安排后，发现中秋节前后两个周末都要"补"假。
        记者注意到，根据放假安排，9月18日（星期六）上班，9月19日至21日放假调休，也就是从周日开始放假3天。由于中秋节后上班不到 10天，又将迎来一个黄金周—国庆长假，因此工作也就"安排"上了。
        双节来袭，仍有人要坚守岗位。加班费怎么算？记者为辛勤的小伙伴们算了一笔账。今年中秋加上国庆，两个假日加在一起共有10个加班日，如果全部加班，则可以拿到相当于24天的日工资。
        根据规定，9月21日中秋节和10月1日、2日、3日均为法定假日，用人单位安排劳动者加班工作，应按照不低于劳动者本人日或小时工资的300%支付加班工资；
        9月19日、20日和10月4日、5日、6日、7 日，用人单位可选择给予补休或按照不低于劳动者本人日或小时工资的200%支付加班工资。也就是说，如果10天全部加班，就可以拿到24天的日工资收入。
        人社部门提醒，当然这只是按照最低工资标准算的最低加班费，实际情况中，加班工资应该与个人实际工资挂钩。'''

    extract_time = TimeExtractor()
    res = extract_time(text, with_parsing=False)
    print(res)

