# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

import os
import time

from jionlp import logging
from jionlp.gadget.trie_tree import TrieTree


class LexiconNER(object):
    """ 构建基于 Trie 词典的前向最大匹配算法，做实体识别。

    Args:
        entity_dicts(dict): 每个类型对应的实体词典
            e.g.
            {
                'Person': ['张大山', '岳灵珊', '岳不群']
                'Organization': ['成都市第一人民医院', '四川省水利局']
            }
        text: str 类型，被搜索的文本内容。

    Return:
        entity_list: 基于字 token 的实体列表

    Examples:
        >>> import jionlp as jio
        >>> entity_dicts = {
                'Person': ['张大山', '岳灵珊', '岳不群'],
                'Organization': ['成都市第一人民医院', '四川省水利局']}
        >>> lexicon_ner = jio.ner.LexiconNER(entity_dicts)
        >>> text = '岳灵珊在四川省水利局上班。'
        >>> result = lexicon_ner(text)
        >>> print(result)

        # [{'type': 'Person', 'text': '岳灵珊', 'offset': [0, 3]},
        #  {'type': 'Organization', 'text': '四川省水利局', 'offset': [4, 10]}]

    """
    def __init__(self, entity_dicts):
        self.trie_tree_obj = TrieTree()
        for typing, entity_list in entity_dicts.items():
            self.trie_tree_obj.build_trie_tree(entity_list, typing)

    def __call__(self, text):
        """
        标注数据，给定一个文本字符串，标注出所有的数据

        Args:
            text: 给定的文本 str 格式
        Return:
            entity_list: 标注的实体列表数据

        """

        record_list = list()  # 输出最终结果
        i = 0
        text_length = len(text)
        
        while i < text_length:
            pointer_orig = text[i: self.trie_tree_obj.depth + i]
            pointer = pointer_orig.lower()
            step, typing = self.trie_tree_obj.search(pointer)
            if typing is not None:
                record = {'type': typing,
                          'text': pointer_orig[0: step],
                          'offset': [i, step + i]}
                record_list.append(record)
            i += step
            
        return record_list
