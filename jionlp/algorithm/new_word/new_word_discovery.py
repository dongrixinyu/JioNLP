# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    对于一个词，分析其内部的内聚度（PMI），和边界的分界度（左右ENTROPY）。
    内聚度越高，和边界分离度越高，则更容易成词。

1、该方法有两种处理模式，一种为本文件所实现，输入一套整体的 N 篇文本，输出一套识别到的词汇
    该模式适合临时、定期（一天、一周、一个月等）更新一遍新词
2、另一种实现模式为实时更新，也即类 NewWordDiscovery 所实现的方式（未完成）。
    该种模式着重强调将文本按时间顺序流式输入新词发现算法，算法实时对文本进行增量的词频更新，
    实时输出发现的新词。此种方式需要以服务形式进行部署，也可以在新词出现不久后，及时发现，
    不需要等待一天、一周、一个月。
    此种方式未进行支持，原因有以下几点：
    1、Python 对于这类 CPU 处理的速度是十分受限的。
    2、新词发现中需要统计巨量的 N-grams，数量十分庞大，尤其是在文本量巨大时。且低频 N-grams
        同样需要统计，因此占用内存巨量，所以不适合实时处理，会导致内存爆炸。
    3、新词发现本质为信息熵统计算法，即发现新词后，并没有确切的统计指标保证所发现词汇真的为
        准确的新词，因此按流式实时处理，会导致结果的不确定性，也就是，定时整体处理方便加入人工
        审核，代价较小。

"""

import re
from collections import Counter

import numpy as np

from jionlp.util import read_file_by_iter

__all__ = ['new_word_discovery']


class NewWordDiscovery(object):
    """ 此方法为流式处理，目前发现较为受限，故未完成 """
    def __init__(self):
        self.n_gram_num = 4
        self.max_word_len = 6
        self.min_point_wise_mutual_information = 80  # min PMI 值
        self.re_chinese = re.compile(r'[\w]+', re.U)
        # self.left_right_char = re.compile('(.)%s(.)' % word)
        self.word_freq_counter = Counter()
        self.word_freq_dict = dict()
        self.word_entropy = dict()
        self.total_word_num = 0

    # def __enter__(self, text):
    #     return self

    # def __exit__(self, *args, **kwargs):

    def enter_compute(self, text):
        current_word_freq = self.count_ngrams(text)

        # PMI
        new_candidates = self.point_wise_mutual_information_filter(current_word_freq)

        # ENTROPY

    def update_ngrams(self, text):
        """
        To get n_gram word frequency dict
        input: str of the chinese sentence ，int of n_gram
        output: word frequency dict

        """
        words = []
        for i in range(1, self.n_gram_num + 1):
            words += [text[j:j + i] for j in range(len(text) - i + 1)]

        # 应该局部更新
        self.word_freq_counter.update(words)
        self.word_freq_dict = dict(self.word_freq_counter)
        self.total_word_num = sum(self.word_freq_counter.values())

        current_words_freq = dict(Counter(words))

        return current_words_freq

    def point_wise_mutual_information_filter(self, current_word_freq):
        new_words = []

        for word in current_word_freq:
            word_length = len(word)
            if word_length == 1:
                continue
            elif word_length == 2:
                mul_info = self.word_freq_dict[word] * self.total_word_num / (self.word_freq_dict[word[0]] * self.word_freq_dict[word[1]])
            elif word_length == 3:
                mul_info_1 = self.word_freq_dict[word[1:]] * self.word_freq_dict[word[0]]
                mul_info_2 = self.word_freq_dict[word[-1]] * self.word_freq_dict[word[:-1]]
                mul_info = self.word_freq_dict[word] * self.total_word_num / max(mul_info_1, mul_info_2)

            else:
                pmi_info = max([self.word_freq_dict[word[i:]] * self.word_freq_dict[word[:i]]
                                for i in range(1, word_length)])
                mul_info = self.word_freq_dict[word] * self.total_word_num / pmi_info

            if mul_info > self.min_point_wise_mutual_information:
                new_words.append(word)

        return new_words

    def calculate_entropy(self, freq_dict):
        # 计算信息熵，其熵越高，词汇独立成词度越高
        entropy_r_dict = {}
        for word in freq_dict:
            r_list = freq_dict[word][1:]

            np_r_list = np.array(r_list)

            # 计算左右熵、自由度
            probability = np_r_list / np.sum(np_r_list)
            entropy_r = - np.sum(np.log2(probability) * probability)
            entropy_r_dict[word] = entropy_r

        return entropy_r_dict


max_word_len = 5
re_chinese = re.compile(r'[\w]+', re.U)


def count_ngrams(input_file):
    word_freq = Counter()
    for line in read_file_by_iter(input_file):

        for sentence in re_chinese.findall(line):
            length = len(sentence)
            for i in range(length):
                word_freq.update(
                    [sentence[i: j + i] for j in range(1, min(length - i + 1, max_word_len + 1))])

    return word_freq


def lrg_info(word_freq, total_word, min_freq, min_mtro):
    l_dict = {}
    r_dict = {}

    def __update_dict(side_dict, side_word, word_freq, freq):
        side_word_freq = word_freq[side_word]
        if side_word_freq > min_freq:

            # 点间互信息公式
            if len(side_word) == 2:
                mul_info = side_word_freq * total_word / (word_freq[side_word[0]] * word_freq[side_word[1]])

            else:
                mul_info_1 = word_freq[side_word[1:]] * word_freq[side_word[0]]
                mul_info_2 = word_freq[side_word[-1]] * word_freq[side_word[:-1]]
                mul_info = side_word_freq * total_word / max(mul_info_1, mul_info_2)

            if mul_info > min_mtro:
                if side_word in side_dict:
                    side_dict[side_word].append(freq)
                else:
                    side_dict[side_word] = [side_word_freq, freq]

    for word, freq in word_freq.items():
        if len(word) < 3:
            continue

        left_word = word[:-1]
        right_word = word[1:]

        __update_dict(l_dict, left_word, word_freq, freq)
        __update_dict(r_dict, right_word, word_freq, freq)

    return l_dict, r_dict


def calculate_entropy(r_dict):
    # 计算信息熵，其熵越高，词汇独立成词度越高
    entropy_r_dict = {}
    for word in r_dict:

        np_r_list = np.array(r_dict[word][1:])

        # 计算左右熵、自由度
        probability = np_r_list / np.sum(np_r_list)
        entropy_r = - np.sum(np.log2(probability) * probability)
        entropy_r_dict[word] = entropy_r

    return entropy_r_dict


def entropy_lr_fusion(entropy_r_dict, entropy_l_dict):
    """ 将左右熵词典合并，根据测算，仅取两词典的交集即可。

    在 left dict 不在 right dict 中的词，100%是没有意义的。反之也同理。

    Args:
        entropy_r_dict:
        entropy_l_dict:

    Returns:

    """
    entropy_in_rl_dict = {}
    for word in entropy_r_dict:
        if word in entropy_l_dict:
            # 左右两个都有的话，都需大于最低限熵，才算是完整的词
            entropy_in_rl_dict[word] = min(entropy_l_dict[word], entropy_r_dict[word])

    return entropy_in_rl_dict


def entropy_filter(entropy_in_rl_dict, word_freq, min_entropy):
    entropy_dict = {}
    for word, word_entropy in entropy_in_rl_dict.items():
        if word_entropy > min_entropy:
            entropy_dict[word] = [word_freq[word], word_entropy]

    return entropy_dict


def new_word_discovery(input_file, min_freq=10, min_mutual_information=80, min_entropy=3):
    """ 新词发现算法，默认发现最多四个字的词汇

    Args:
        input_file: 文本输入文件
        min_freq: 若发现新词，则新词应在语料中出现的最低词频
        min_mutual_information: 最低点间互信息值，即词汇的内聚度，该值越低，则4字长词更容易被输出，
            因此，其实可以为该值乘以一个词长 weight，确保更多的长词被识别
        min_entropy: 最低左右信息熵，即词汇和边界字的分离度

    Returns:
        dict: 新词 dict

    Examples:
        >>> import jionlp as jio
        >>> input_file = '/path/to/text_file.txt'

        # input_file 内的样例文本，即一行一条纯文本即可
        # 应采儿吸毒是怎么回事？应采儿藏毒事件始末真相
        # 但刚出道没几年应采儿就因为吸毒入狱，2004年11月6日凌晨，应采儿与朋友从KTV出来驾车经过九龙塘金巴伦道49号时
        # 董洁，1980年4月19日出生于辽宁省大连市，毕业于中国人民解放军国防大学军事文化学院舞蹈系，中国内地影视女演员。
        # ...

        >>> new_words_dict = jio.new_word.new_word_discovery(input_file)
        >>> print(new_words_dict)
        >>> print(jio.new_word.new_word_discovery.__doc__)

        # {'浑水': [34, 6.9],
        #  '贝壳': [28, 6.7],
        #  '应采儿': [17, 6.2],
        #  '证监会': [18, 5.8]}

    """

    word_freq = count_ngrams(input_file)
    total_word = sum(word_freq.values())

    l_dict, r_dict = lrg_info(word_freq, total_word, min_freq, min_mutual_information)

    entropy_r_dict = calculate_entropy(l_dict)
    entropy_l_dict = calculate_entropy(r_dict)

    entropy_in_rl_dict = entropy_lr_fusion(entropy_r_dict, entropy_l_dict)
    entropy_dict = entropy_filter(entropy_in_rl_dict, word_freq, min_entropy)
    result = dict(sorted(entropy_dict.items(), key=lambda x: x[1][1], reverse=True))

    return result

