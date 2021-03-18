# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、NER 数据集有两种存储格式
        entity 格式，e.g.
            ['胡静静在水利局工作。',
             [{'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
             {'text': '水利局', 'offset': [4, 7], 'type': 'Orgnization'}]]
        tag 格式，e.g.
            [['胡', '静', '静', '在', '水', '利', '局', '工', '作', '。'],
             ['B-Person', 'I-Person', 'E-Person', 'O', 'B-Orgnization',
             'I-Orgnization', 'E-Orgnization', 'O', 'O', 'O']]

        所有的 NER 数据均在这两者之间进行转换，重叠标注的 NER 模型暂不在本项目的
        考虑范围内，为保证数据中 \n\r\t 等转义字符的稳定一致性，均采用 json 格式
        存储数据。

    2、默认采用的标注标准为 BIOES
        NER 有多套标注标准，如 BIO、BMOE、BMOES 等等，相差均不大，为了明确实体边
        界考虑，默认选择 B(Begin)I(Inside)O(Others)E(End)S(Single) 标注标注。

    3、NER 数据集常见的有两种 token 级别，字级别与词级别，两者的相互转换需要考虑分
        词器的错分、字词 offset 变化等情况。

"""


import pdb
import json
from typing import Dict, Any, Tuple, Optional, List

from jionlp import logging


__all__ = ['entity2tag', 'tag2entity', 'char2word', 'word2char']


def entity2tag(token_list: List[str], entities: List[Dict[str, Any]], 
               formater='BIOES'):
    """ 将实体 entity 格式转为 tag 格式，若标注过程中有重叠标注，则会自动将靠后的
    实体忽略、删除。针对单条处理，不支持批量处理。

    Args:
        token_list(List[str]): token 化的文本的 list
        entities(List[str, Dict[str, Any]]): 文本相应的实体。
        formater(str): 选择的标注标准
    return:
        List[List[str], List[str]]: tag 格式的数据

    Examples:
        >>> token_list = '胡静静在水利局工作。'  # 字级别
        >>> token_list = ['胡', '静', '静', '在', '水',
                          '利', '局', '工', '作', '。']  # 字或词级别
        >>> ner_entities =
                [{'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
                 {'text': '水利局', 'offset': [4, 7], 'type': 'Orgnization'}]
        >>> print(jio.ner.entity2tag(token_list, ner_entities))
            ['B-Person', 'I-Person', 'E-Person', 'O', 'B-Orgnization',
             'I-Orgnization', 'E-Orgnization', 'O', 'O', 'O']

    """
    tags = ['O' for i in range(len(token_list))]
    
    flag = 0  # 判断重叠标注
    
    entities = sorted(entities, key=lambda i: i['offset'][0])

    for idx, entity in enumerate(entities):
        if entity['offset'][1] < flag:  # 说明重叠标注，要删除
            if 1 < idx + 1 < len(entities):
                logging.warning(
                    'The entity {} is overlapped with {}.'.format(
                        json.dumps(entity, ensure_ascii=False),
                        json.dumps(entities[idx - 1], ensure_ascii=False)))
            
        else:
            if entity['offset'][1] - entity['offset'][0] == 1:
                tags[entity['offset'][0]] = 'S-' + entity['type']
            else:
                tags[entity['offset'][0]] = 'B-' + entity['type']
                if entity['offset'][1] - entity['offset'][0] > 2:
                    for j in range(entity['offset'][0] + 1,
                                   entity['offset'][1] - 1):
                        tags[j] = 'I-' + entity['type']
                tags[entity['offset'][1] - 1] = 'E-' + entity['type']
            flag = entity['offset'][1]

    return tags
    

def tag2entity(token_list: List[str], tags: List[str], verbose=False):
    """ 将 tag 格式转为实体 entity 格式，若格式中有破损不满足 BIOES 标准，则不转
    换为实体并支持报错。针对单条数据处理，不支持批量处理。

    Args:
        token_list(List[str]): 输入的文本 token 序列
        tags(List[str]): 文本 token 序列对应的标签
        verbose(bool): 是否打印出抽取实体时的详细错误信息( BIOES 标准错误)

    Returns:
        list: 实体列表

    Examples:
        >>> token_list = '胡静静在水利局工作。'  # 字级别
        >>> token_list = ['胡', '静', '静', '在', '水',
                          '利', '局', '工', '作', '。']  # 字或词级别
        >>> tags = ['B-Person', 'I-Person', 'E-Person', 'O', 'B-Orgnization',
                    'I-Orgnization', 'E-Orgnization', 'O', 'O', 'O']
        >>> print(jio.ner.tag2entity(token_list, tags))
            [{'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
             {'text': '水利局', 'offset': [4, 7], 'type': 'Orgnization'}]]

    """
    entities = list()
    start = None

    def _wrong_message(_idx, ts):
        if verbose:
            logging.info(token_list)
            logging.info(tags)
            logging.warning('wrong tag: {}'.format(
                ts[start if start is not None
                   else max(0, _idx - 2): _idx + 2]))

    for idx, (tag, token) in enumerate(zip(tags, token_list)):
        prefix = tag[0]
        if tag == 'O':
            start = None
            continue
        elif prefix in 'I':
            if start is None:
                _wrong_message(idx, tags)
            continue
        elif prefix == 'E':
            if start is None:
                _wrong_message(idx, tags)
                continue
            key, value = tags[start][2:], token_list[start: idx + 1]
        else:
            if prefix in 'S':
                key, value = tag[2:], token
                start = idx
            elif prefix == 'B':
                start = idx
                continue
            else:
                _wrong_message(idx, tags)
                return entities
        
        entities.append({'type': key, 'text': ''.join(value),
                         'offset': (start, idx + 1)})
        start = None

    return entities
    
    
def char2word(char_entity_list, word_token_list, verbose=False):
    """ 将字 token 的 ner 训练数据组织成词 token，数据结构不变。针对单条数据处理，
    不支持批量处理。
    根据经验，jieba 分词的分词错误造成实体被丢弃，其错误率在 4.62%，
    而 pkuseg 分词器造成的错误率在 3.44%。

    Args:
        char_entity_list: 以字 token 为基准对应的实体列表
        word_token_list: 采用分词器分词后的 list
        verbose(bool): 字级别数据转换为词级别时，由于分词器误差，会有数据错漏，
            此处选择是否打印详细错漏

    Returns:
        list: 词 token 数据

    Examples:
        >>> char_token_list = '胡静静喜欢江西红叶建筑公司'  # 字级别
        >>> char_token_list = [
                '胡', '静', '静', '喜', '欢', '江', '西',
                '红', '叶', '建', '筑', '公', '司']  # 字或词级别
        >>> char_entity_list = [
                {'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
                {'text': '江西红叶建筑公司', 'offset': [5, 13], 'type': 'Company'}]
        >>> word_token_list = ['胡静静', '喜欢', '江西', '红叶', '建筑', '公司']
        >>> print(jio.ner.char2word(char_entity_list, word_token_list))
            [{'text': '胡静静', 'offset': [0, 1], 'type': 'Person'},
             {'text': '江西红叶建筑公司', 'offset': [2, 6], 'type': 'Company'}]

    """

    idx_flag = 0
    idx_list = [0]
    for word in word_token_list:
        idx_flag += len(word)
        idx_list.append(idx_flag)

    word_entity_list = list()
    for char_entity in char_entity_list:
        # 判断该实体有没有与分词产生冲突
        try:
            start = idx_list.index(char_entity['offset'][0])
            end = idx_list.index(char_entity['offset'][1])

            word_entity_list.append(
                {'type': char_entity['type'], 'offset': [start, end],
                 'text': char_entity['text']})

        except ValueError:
            if verbose:
                # 确定该实体的具体位置，给出日志
                if char_entity['offset'][0] not in idx_list:
                    start = idx_list.index(
                        max([idx for idx in idx_list
                             if idx < char_entity['offset'][0]]))
                else:
                    start = idx_list.index(char_entity['offset'][0])
                    
                if char_entity['offset'][1] not in idx_list:
                    end = idx_list.index(
                        min([idx for idx in idx_list
                             if idx > char_entity['offset'][1]]))
                else:
                    end = idx_list.index(char_entity['offset'][1])
                logging.warning(
                    'the entity {} =/=> {}'.format(
                        char_entity, word_token_list[start: end]))
        
    return word_entity_list

    
def word2char(word_entity_list, word_token_list):
    """ 将 ner 数据由词级别转换为字级别，结构不变。针对单条数据处理，
    不支持批量处理。

    Args:
        word_entity_list: 词 token 的实体列表
        word_token_list: 词 token 的文本序列列表

    Returns:
        list: 字级别的 ner 数据

    Examples:
        >>> word_entity_list = [
                {'type': 'Person', 'offset': [0, 1], 'text': '胡静静'},
                {'type': 'Company', 'offset': [2, 6], 'text': '江西红叶建筑公司'}]
        >>> word_token_list = ['胡静静', '喜欢', '江西', '红叶', '建筑', '公司']
        >>> print(jio.ner.word2char(word_entity_list, word_token_list))
                [{'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
                 {'text': '江西红叶建筑公司', 'offset': [5, 13], 'type': 'Company'}]

    """

    idx_flag = 0
    idx_list = list()
    for word in word_token_list:
        idx_list.append(idx_flag)
        idx_flag += len(word)
    idx_list.append(idx_flag)
    
    char_entity_list = list()
    for word_entity in word_entity_list:
        char_entity_list.append(
            {'type': word_entity['type'],
             'offset': [idx_list[word_entity['offset'][0]],
                        idx_list[word_entity['offset'][1]]],
             'text': ''.join(
                 word_token_list[word_entity['offset'][0]:
                                 word_entity['offset'][1]])})
        
    return char_entity_list

