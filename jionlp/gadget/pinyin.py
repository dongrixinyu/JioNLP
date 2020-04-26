# -*- coding=utf-8 -*-

import os
import pdb

from jionlp.dictionary.dictionary_loader import pinyin_phrase_loader
from jionlp.dictionary.dictionary_loader import pinyin_char_loader
from trie_tree import TrieTree
#from .trie_tree import TrieTree


class Pinyin(object):
    ''' 为汉字标读音 '''
    
    def __init__(self):
        self.trie_tree_obj = None
        
    def _prepare(self):
        self.pinyin_phrase = pinyin_phrase_loader()
        self.pinyin_char = pinyin_char_loader()
        
        # 加载 trie 树
        self.trie_tree_obj = TrieTree()
        self.trie_tree_obj.build_trie_tree(self.pinyin_phrase, 'phrase')
        self.trie_tree_obj.build_trie_tree(self.pinyin_char, 'char')
        
    def __call__(self, text, mode=''):
        ''' 将汉字转为拼音，并提供额外的拼音展示方案，若对应字符无拼音，则添加 <unk> 作为标记 '''
        if self.trie_tree_obj is None:
            self._prepare()
        
        record_list = list()  # 输出最终结果
        i = 0
        end = len(text)
        while i < end:
            pointer = text[i: self.trie_tree_obj.depth + i]
            step, typing = self.trie_tree_obj.search(pointer)
            if typing == 'phrase':
                record_list.extend(self.pinyin_phrase[pointer[0: step]])
            elif typing == 'char':
                record_list.append(self.pinyin_char[pointer[0: step]])
            else:
                print(step, typing, pointer[0])
                record_list.append('<unk>')
            i += step

        assert len(record_list) == len(text)
        return record_list



if __name__ == '__main__':
    pinyin = Pinyin()
    res = pinyin('今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？', mode='char')
    print(res)















