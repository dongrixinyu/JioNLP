# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、CWS（分词）数据集有两种存储格式
        word 格式，e.g.
            ["他", "指出", "：", "近", "几", "年", "来", "，", "足球场", "风气", "差劲", "。"]
        tag 格式，e.g.
            [['他', '指', '出', '：', '近', '几', '年', '来', '，', '足', '球', '场', '风', '气', '差', '劲', '。'],
             ['B', 'B', 'I', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'I', 'I', 'B', 'I', 'B', 'I', 'B']]

        所有的 CWS 数据均在这两者之间进行转换，为保证数据中 \n\r\t 以及空格等转义
        字符的稳定一致性，均采用 json 格式存储数据。

    2、默认采用的标注标准为 BI 标签格式
        分词有多套标注标准，如 BI、BIES 等等，相差均不大，为了明确词汇边界考虑，
        并减少转移函数错误，默认选择 B(Begin)I(Inside|End)标签标注。

"""

import numpy as np
from typing import List

from jionlp import logging


__all__ = ['word2tag', 'tag2word']


def word2tag(word_list: List[str]):
    """ 将实体 entity 格式转为 tag 格式，若标注过程中有重叠标注，则会自动将靠后的
    实体忽略、删除。针对单条处理，不支持批量处理。默认采用 BI 标注标准。

    Args:
        word_list(List[str]): 分词词汇的 list
    return:
        List[str, numpy.ndarray[str]]: tag 格式的数据

    Examples:
        >>> word_list = ["他", "指出", "：", "近", "几", "年", "来", "，", "足球场", "风气", "差劲", "。"]
        >>> print(jio.cws.word2tag(word_list))

        # ['他指出：近几年来，足球场风气差劲。',
        #  numpy.ndarray(['B', 'B', 'I', 'B', 'B', 'B', 'B', 'B', 'B',
        #                 'B', 'I', 'I', 'B', 'I', 'B', 'I', 'B'], dtype='<U1')]

    """

    chars = ''.join(word_list)
    tags = np.empty(len(chars), dtype=np.unicode)

    offset = 0
    for word in word_list:
        word_length = len(word)
        tags[offset] = 'B'
        if word_length >= 1:
            tags[offset + 1: offset + word_length] = 'I'
        offset += word_length

    assert len(chars) == tags.shape[0]
    return [chars, tags]


def tag2word(chars: str, tags: List[str], verbose=False):
    """ 将 tag 格式转为词汇列表，
    若格式中有破损不满足 BI 标准，则不转换为词汇并支持报错。
    该函数针对单条数据处理，不支持批量处理。

    Args:
        chars(str): 输入的文本字符串
        tags(List[str]): 文本序列对应的标签
        verbose(bool): 是否打印出抽取实体时的详细错误信息，该函数并不处理报错返回，
            仍按一定形式将有标签逻辑错误数据进行组织并返回。

    Returns:
        list: 词汇列表

    Examples:
        >>> chars = '他指出：近几年来，足球场风气差劲。'
        >>> tags = ['B', 'B', 'I', 'B', 'B', 'B', 'B', 'B', 'B', 'B', 'I', 'I', 'B', 'I', 'B', 'I', 'B']
        >>> print(jio.cws.tag2word(chars, tags))

        # ["他", "指出", "：", "近", "几", "年", "来", "，", "足球场", "风气", "差劲", "。"]

    """

    tag_length = len(tags)
    assert len(chars) == tag_length, 'the length of `chars` and `tags` is not same.'

    if tag_length == 1:
        return [chars]

    def _wrong_message(_idx, ts):
        logging.info(chars)
        logging.info(tags)
        logging.warning('wrong tag: {}'.format(
            ts[start if start is not None else max(0, _idx - 2): _idx + 2]))

    word_list = list()
    start = None

    for idx, (tag, char) in enumerate(zip(tags, chars)):

        if tag == 'I':
            if idx == 0:
                if verbose:
                    _wrong_message(idx, tags)
                start = idx
                continue
            elif idx == tag_length - 1:
                word = chars[start:]
            else:
                continue

        elif tag == 'B':
            if idx == 0:
                start = idx
                continue
            elif idx == tag_length - 1:
                word_list.append(chars[start: idx])
                word = chars[-1]
            else:
                if start is None:
                    if verbose:
                        _wrong_message(idx, tags)
                    continue
                word = chars[start: idx]
                start = idx
        else:
            if verbose:
                _wrong_message(idx, tags)
            return word_list

        word_list.append(word)

    assert len(''.join(word_list)) == len(chars), \
        'the length of char list must be same.'

    return word_list
