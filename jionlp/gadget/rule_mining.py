# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
TODO:
    1、

"""

import os
import pdb

from typing import Union


# from .trie_tree import TrieTree


class RuleMining(object):
    """
    将给定有监督训练语料，从中寻找出各个类别的频繁模式，方便进行规则总结，可有效
    用于文本分类。


    args:
        dataset(list(str)): 待寻找规则的文本带标签数据集。
        threshold(str):

    return:
        list(str|dict): 拼音列表

    """
    
    def __init__(self):
        self.trie_tree_obj = None
        
    def _prepare(self):
        pass
        
    def __call__(self, text,
                 threshold: float = 0.3):
        pass
        

if __name__ == '__main__':
    pass
