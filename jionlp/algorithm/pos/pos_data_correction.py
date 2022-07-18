# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


"""
DESCRIPTION:
    1、词性标注数据矫正工具，用于对有误的词性标注数据进行统一调整和矫正。

"""

from typing import List
import numpy as np

from jionlp import logging
from jionlp.gadget.trie_tree import TrieTree
from .pos_data_converter import tag2pos, pos2tag


class POSDCWithStandardWords(object):
    """ 给定一条词性标注数据，依据标准的词汇-词性库，调整词性标注数据
    例如，样本数据为 [['学习', 'v'], ['区', 's'], ['块链', 'n'], ['。', 'w']],
    标准词典为 {'区块链': 'n', '有条不紊': 'a'}
    被矫正的数据为 [['学习': 'v'], ['区块链': 'n'], ['。', 'w']]
    该方法默认采用了 BI 标注标注对数据进行处理。

    注意：
        此种方法是采用词典来调整词性标注数据，其基本条件为，标准词汇数据不可以具有前后歧义，例如：
        ['女领导', '亲口', '交代', '工作', '业务']，标准词典为 {'代工': 'v', '振作': 'v'}
        则最后处理结果为 ['女领导', '亲口', '交', '代工', '作', '业务']，反而造成错误。

    Args:
        pos_list(list[list[str]]): 待矫正的词性标注数据列表
        verbose(bool): 打印修正的数据

    Returns:
        correction_sample_list(list[list[str]]): 被标准词汇调整过的词性标注数据。

    """
    def __init__(self, standard_pos_dict):
        # 将标准词典构建为 Trie 树
        self.standard_pos_tree = TrieTree()
        for word, pos_tag in standard_pos_dict.items():
            self.standard_pos_tree.add_node(word, pos_tag)

    def __call__(self, pos_list: List[List[str]], verbose=False):

        text, tags = pos2tag(pos_list)

        i = 0
        end = len(text)
        while i < end:
            pointer = text[i: self.standard_pos_tree.depth + i]
            step, typing = self.standard_pos_tree.search(pointer)
            if typing is not None:
                if verbose:
                    # 当原标签非正确的打标结果，则需要打印出详细日志
                    if i + step < end:
                        if (not tags[i].startswith('B')) \
                                or (not np.all([k[0] for k in tags[i + 1: i + step]] == 'I')) \
                                or (not tags[i + step].startswith('B')):
                            logging.info('text: `{}`, word: `{}`.'.format(
                                text[max(0, i - 3): min(end, i + step + 3)], pointer[0: step]))
                    else:
                        if (not tags[i].startswith('B')) \
                                or (not np.all([k[0] for k in tags[i + 1: i + step]] == 'I')):
                            logging.info('text: `{}`, word: `{}`.'.format(
                                text[max(0, i - 3): min(end, i + step + 3)], pointer[0: step]))

                tags[i] = 'B-' + typing
                tags[i + 1: i + step] = 'I-' + typing

                if i + step < end:
                    tags[i + step] = 'B-' + typing

            i += step

        word_pos_list = tag2pos(text, tags)

        return word_pos_list

