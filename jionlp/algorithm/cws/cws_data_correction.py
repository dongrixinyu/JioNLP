# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP

"""
DESCRIPTION:
    1、分词数据矫正工具，用于对有误的分词标注数据进行统一调整和矫正。

    2、默认采用的标注标准为 BI 标签格式
        分词有多套标注标准，如 BI、BIES 等等，相差均不大，为了明确词汇边界考虑，
        并减少转移函数错误，默认选择 B(Begin)I(Inside|End)标签标注。

"""


from typing import List
import numpy as np

from jionlp import logging
from jionlp.gadget.trie_tree import TrieTree
from .cws_data_converter import word2tag, tag2word


class CWSDCWithStandardWords(object):
    """ 给定一条分词标注数据，依据标准的词汇库，调整分词标注数据
    例如，样本数据为 ['学习', '区', '块链', '。'], 标准词典为 ['区块链', '有条不紊']
    被矫正的数据为 ['学习', '区块链', '。']
    该方法默认采用了 BI 标注标注对数据进行处理。

    注意：
        此种方法是采用词典来调整分词数据，其基本条件为，标准词汇数据不可以具有前后歧义，例如：
        ['女领导', '亲口', '交代', '工作', '业务']，标准词典为 ['代工', '振作']
        则最后处理结果为 ['女领导', '亲口', '交', '代工', '作', '业务']。反而造成错误。

    Args:
        word_list(list[str]): 待矫正的分词数据列表
        verbose(bool): 打印修正的数据

    Returns:
        correction_sample_list(list[str]): 被标准词汇调整过的分词数据。

    """
    def __init__(self, standard_word_list):
        # 将标准词典构建为 Trie 树
        self.standard_word_tree = TrieTree()
        self.standard_word_tree.build_trie_tree(standard_word_list, 'w')

    def __call__(self, word_list: List[str], verbose=False):

        char_list, tags = word2tag(word_list)
        text = ''.join(word_list)

        i = 0
        end = len(text)
        while i < end:
            pointer = text[i: self.standard_word_tree.depth + i]
            step, typing = self.standard_word_tree.search(pointer)
            if typing is not None:
                if verbose:
                    # 当原标签非正确的打标结果，则需要打印出详细日志
                    if i + step < end:
                        if tags[i] != 'B' or (not np.all(tags[i + 1: i + step] == 'I')) or tags[i + step] != 'B':
                            logging.info('text: `{}`, word: `{}`.'.format(
                                text[max(0, i - 3): min(end, i + step + 3)], pointer[0: step]))
                    else:
                        if tags[i] != 'B' or (not np.all(tags[i + 1: i + step] == 'I')):
                            logging.info('text: `{}`, word: `{}`.'.format(
                                text[max(0, i - 3): min(end, i + step + 3)], pointer[0: step]))

                tags[i] = 'B'
                tags[i + 1: i + step] = 'I'

                if i + step < end:
                    tags[i + step] = 'B'

            i += step

        words_list = tag2word(char_list, tags)

        return words_list
