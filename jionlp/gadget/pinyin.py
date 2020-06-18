# -*- coding=utf-8 -*-

import os
import pdb

from typing import Union

from jionlp.dictionary.dictionary_loader import pinyin_phrase_loader
from jionlp.dictionary.dictionary_loader import pinyin_char_loader
from .trie_tree import TrieTree
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
        
        # 格式转换
        self._pinyin_formater()
        
    def _pinyin_convert_standard_2_simple(self, standard_pinyin, letter_map_dict):
        suffix = '5'
        res = list()
        for letter in standard_pinyin:
            if letter in letter_map_dict:
                res.append(letter_map_dict[letter][0])
                if len(letter_map_dict[letter]) == 2:
                    suffix = letter_map_dict[letter][1]
            else:
                res.append(letter)
        
        res.append(suffix)
        return ''.join(res)
        
    def _pinyin_formater(self):
        letter_map_dict = {
            'à': 'a4', 'á': 'a2','ā': 'a1','ǎ': 'a3',
            'ò': 'o4', 'ó': 'o2','ō': 'o1','ǒ': 'o3',
            'è': 'e4', 'é': 'e2','ē': 'e1','ě': 'e3',
            'ì': 'i4', 'í': 'i2','ī': 'i1','ǐ': 'i3',
            'ù': 'u4', 'ú': 'u2','ū': 'u1','ǔ': 'u3',
            'ǜ': 'v4', 'ǘ': 'v2','ǖ': 'v1','ǚ': 'v3', 'ü' : 'v'}
        pinyin_list = list()
        for char, pinyin in self.pinyin_char.items():
            pinyin_list.extend(pinyin)
        for phrase, pinyin in self.pinyin_phrase.items():
            pinyin_list.extend(pinyin)
        pinyin_list = list(set(pinyin_list))
        
        self.pinyin_formater = dict()
        for standard_pinyin in pinyin_list:
            simple_pinyin = self._pinyin_convert_standard_2_simple(
                standard_pinyin, letter_map_dict)
            self.pinyin_formater.update({standard_pinyin: simple_pinyin})
        
    def __call__(self, text, formater: Union['standard', 'simple'] = 'standard'):
        ''' 将汉字转为拼音，并提供额外的拼音展示方案，若对应字符无拼音，或字母、字符等，
        则添加 <unk> 作为标记 
        '''
        if self.trie_tree_obj is None:
            self._prepare()
        
        record_list = list()  # 输出最终结果
        i = 0
        end = len(text)
        while i < end:
            pointer = text[i: self.trie_tree_obj.depth + i]  # 遇到标点符合暂停，有优化空间
            step, typing = self.trie_tree_obj.search(pointer)
            if typing == 'phrase':
                #print(step, typing, pointer)
                cur_pinyin = self.pinyin_phrase[pointer[0: step]]
                if formater == 'simple':
                    cur_pinyin = [self.pinyin_formater[pinyin]
                                  for pinyin in cur_pinyin]
                record_list.extend(cur_pinyin)
            elif typing == 'char':
                cur_pinyin = self.pinyin_char[pointer[0: step]][0]
                if formater == 'simple':
                    cur_pinyin = self.pinyin_formater[cur_pinyin]
                record_list.append(cur_pinyin)
            else:
                #print(step, typing, pointer[0])
                record_list.append('<unk>')
            i += step
        
        assert len(record_list) == len(text)
        return record_list



if __name__ == '__main__':
    pinyin = Pinyin()
    text = '今天L.A.洛杉矶天气好晴朗，一丘之貉，想吃方便面。你还在工作吗？在航天飞机上工作吗？'
    res = pinyin(text, formater='simple')
    for i, j in zip(text, res):
        print(i, j)















