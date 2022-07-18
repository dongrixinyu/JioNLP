# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import numpy as np
from typing import List

from jionlp import logging


__all__ = ['pos2tag', 'tag2pos']


def pos2tag(pos_list):
    """ 将实体 entity 格式转为 tag 格式，若标注过程中有重叠标注，则会自动将靠后的
    实体忽略、删除。针对单条处理，不支持批量处理。默认采用 BI 标注标准。

    Args:
        pos_list(List[List[str, str]]): 分词词汇的 list
    return:
        List[str, numpy.ndarray[str]]: tag 格式的数据

    Examples:
        >>> import jionlp as jio
        >>> pos_list = [["他", "r"], ["指出", "v"], ["：", "w"], ["近", "a"]]
        >>> print(jio.pos.pos2tag(pos_list))

        # ['他指出：近几年来，足球场风气差劲。',
        #  numpy.ndarray(['B-r', 'B-v', 'I-v', 'B-w', 'B-a'], dtype='<U1')]

    """

    chars = ''.join([item[0] for item in pos_list])
    tags = np.empty(len(chars), dtype='<U7')

    offset = 0
    for item in pos_list:
        word, tag = item
        word_length = len(word)

        tags[offset] = 'B-' + tag
        if word_length >= 1:
            tags[offset + 1: offset + word_length] = 'I-' + tag

        offset += word_length

    assert len(chars) == tags.shape[0]
    return [chars, tags]


def tag2pos(chars: str, tags: List[str], verbose=False):
    """ 将 tag 格式转为词汇-词性列表，
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
        >>> import jionlp as jio
        >>> chars = '他指出：近'
        >>> tags = ['B-r', 'B-v', 'I-v', 'B-w', 'B-a']
        >>> print(jio.pos.tag2pos(chars, tags))

        # [["他", "r"], ["指出", "v"], ["：", "w], ["近", "a"]]

    TODO:
        该方法默认是未验证 I-type 标签的前后一致性的，
        即 B-n, I-v, I-a 这样的序列串是无效的，但该方法无法检验出。

    """

    tag_length = len(tags)
    assert len(chars) == tag_length, 'the length of `chars` and `tags` is not same.'

    if tag_length == 1:
        return [[chars, tags[0].split('-')[1]]]

    def _wrong_message(_idx, ts):
        logging.info(chars)
        logging.info(tags)
        logging.warning('wrong tag: {}'.format(
            ts[start if start is not None else max(0, _idx - 2): _idx + 2]))

    pos_list = list()
    start = None
    pos_tag = None

    for idx, (tag, char) in enumerate(zip(tags, chars)):

        if tag.startswith('I'):
            if idx == 0:
                if verbose:
                    _wrong_message(idx, tags)
                start = idx
                continue
            elif idx == tag_length - 1:
                word = chars[start:]
                pos_tag = tag.split('-')[1]
            else:
                continue

        elif tag.startswith('B'):
            if idx == 0:
                start = idx
                continue
            elif idx == tag_length - 1:
                pos_list.append([chars[start: idx], tags[start].split('-')[1]])
                word = chars[-1]
                pos_tag = tag.split('-')[1]
            else:
                if start is None:
                    if verbose:
                        _wrong_message(idx, tags)
                    continue
                word = chars[start: idx]
                pos_tag = tags[start].split('-')[1]
                start = idx
        else:
            if verbose:
                _wrong_message(idx, tags)

            return pos_list

        pos_list.append([word, pos_tag])

    assert len(''.join([item[0] for item in pos_list])) == len(chars), \
        'the length of char list must be same.'

    return pos_list

