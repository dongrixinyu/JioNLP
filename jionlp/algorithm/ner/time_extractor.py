# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

import re
import time

from jionlp.rule.rule_pattern import TIME_CHAR_STRING, \
    FAKE_POSITIVE_START_STRING, FAKE_POSITIVE_END_STRING
from jionlp.gadget.time_parser import TimeParser


class TimeExtractor(object):
    """ 时间实体抽取器。不依赖模型，将文本中的时间实体进行抽取，并对其做时间语义解析。

    Args:
        text: 输入待抽取时间实体的文本
        time_base: 若对文本中的时间实体进行语义解析，则须指定解析的时间基，默认为当前时间 time.time()
        with_parsing: bool 类型，指示返回结果是否包含解析信息，默认为 True

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

    def __call__(self, text, time_base=time.time(), with_parsing=True):
        if self.parse_time is None:
            self._prepare()

        candidates_list = self.extract_time_candidates(text)

        time_entity_list = list()
        for candidate in candidates_list:
            offset = [0, 0]
            bias = 0
            while candidate['offset'][0] + offset[1] < candidate['offset'][1]:

                true_string, result, offset = self.grid_search(
                    candidate['time_candidate'][bias:])
                if true_string is not None:
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

        for item in time_entity_list:
            assert item['text'] == text[item['offset'][0]: item['offset'][1]]
            print(item)
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

        return True

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

                    result = self.parse_time(sub_string, strict=True)

                    return sub_string, result, offset
                except (ValueError, Exception):
                    continue

        return None, None, None

    def _grid_search(self, time_candidate):
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
                    # 可能误打 “春”、“夏” 等单字符时间表达
                    time_candidates_list.append(
                        {'time_candidate': matched_res.group(),
                         'offset': [idx_count + matched_res.span()[0],
                                    idx_count + matched_res.span()[1]]})
                idx_count += matched_res.span()[1]
            else:
                break

        return time_candidates_list


if __name__ == '__main__':
    text = '''        【标题：中秋国庆双节都加班，可拿24天的日工资】
        8月临近尾声，中秋、国庆两个假期已在眼前。2021年中秋节是9月21日，星期二。 有不少小伙伴翻看放假安排后，发现中秋节前后两个周末都要"补"假。
        记者注意到，根据放假安排，9月18日（星期六）上班，9月19日至21日放假调休，也就是从周日开始放假3天。由于中秋节后上班不到 10天，又将迎来一个黄金周—国庆长假，因此工作也就"安排"上了。
        双节来袭，仍有人要坚守岗位。加班费怎么算？记者为辛勤的小伙伴们算了一笔账。今年中秋加上国庆，两个假日加在一起共有10个加班日，如果全部加班，则可以拿到相当于24天的日工资。
        根据规定，9月21日中秋节和10月1日、2日、3日均为法定假日，用人单位安排劳动者加班工作，应按照不低于劳动者本人日或小时工资的300%支付加班工资；
        9月19日、20日和10月4日、5日、6日、7 日，用人单位可选择给予补休或按照不低于劳动者本人日或小时工资的200%支付加班工资。也就是说，如果10天全部加班，就可以拿到24天的日工资收入。
        人社部门提醒，当然这只是按照最低工资标准算的最低加班费，实际情况中，加班工资应该与个人实际工资挂钩。'''

    extract_time = TimeExtractor()
    res = extract_time(text, with_parsing=False)
    print(res)

