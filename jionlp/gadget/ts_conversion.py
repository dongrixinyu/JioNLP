# -*- coding=utf-8 -*-

import os
import pdb
#from .trie_tree import TrieTree

from jionlp.dictionary.dictionary_loader import traditional_simplified_loader
from trie_tree import TrieTree


class TSConversion(object):
    '''
    繁简体转换
    '''
    def __init__(self):
        self._prepare()
        
    def _prepare(self):
        self.tra2sim_char = traditional_simplified_loader('tra2sim_char.txt')
        self.sim2tra_char = traditional_simplified_loader('sim2tra_char.txt')
        tra2sim_word = traditional_simplified_loader('tra2sim_word.txt')
        sim2tra_word = traditional_simplified_loader('sim2tra_word.txt')
        
        self.tra2sim_token = dict(self.tra2sim_char, **tra2sim_word)
        self.sim2tra_token = dict(self.sim2tra_char, **sim2tra_word)
        
        # 加载 trie 树
        self.trie_tree_obj = TrieTree()
        self.trie_tree_obj.build_trie_tree(self.tra2sim_token, 'tra')
        self.trie_tree_obj.build_trie_tree(self.sim2tra_token, 'sim')

    def tra2sim(self, text, mode='char'):
        ''' 将繁体转换为简体 '''
        if mode == 'char':
            res_list = list()
            for char in text:
                if char in self.tra2sim_char:
                    res_list.append(self.tra2sim_char[char])
                else:
                    res_list.append(char)
            assert len(res_list) == len(text)
            return ''.join(res_list)
            
        elif mode == 'word':
            record_list = []  # 输出最终结果
            i = 0
            end = len(text)
            while i < end:
                pointer = text[i: self.trie_tree_obj.depth + i]
                step, typing = self.trie_tree_obj.search(pointer)
                if typing == 'tra':
                    #pdb.set_trace()
                    record_list.append(self.tra2sim_token[pointer[0: step]])
                else:
                    record_list.append(pointer[0: step])
                    #pdb.set_trace()
                i += step
            
            return ''.join(record_list)

    def sim2tra(self, text, mode='char'):
        ''' 将简体转换为繁体 '''
        if mode == 'char':
            res_list = list()
            for char in text:
                if char in self.sim2tra_char:
                    res_list.append(self.sim2tra_char[char])
                else:
                    res_list.append(char)
            assert len(res_list) == len(text)
            return ''.join(res_list)
            
        elif mode == 'word':
            record_list = []  # 输出最终结果
            i = 0
            end = len(text)
            while i < end:
                pointer = text[i: self.trie_tree_obj.depth + i]
                step, typing = self.trie_tree_obj.search(pointer)
                if typing == 'sim':
                    #pdb.set_trace()
                    record_list.append(self.sim2tra_token[pointer[0: step]])
                else:
                    assert step == 1
                    record_list.append(pointer[0: step])
                    #pdb.set_trace()
                i += step
            
            return ''.join(record_list)



if __name__ == '__main__':
    ts = TSConversion()
    res = ts.sim2tra('今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？', mode='char')
    print(res)
    res = ts.sim2tra('今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？', mode='word')
    print(res)
    res = ts.tra2sim('今天天氣好晴朗，想吃方便面。你還在工作嗎？在航天飛機上工作嗎？', mode='word')
    print(res)
    res = ts.tra2sim('今天天氣好晴朗，想吃速食麵。你還在工作嗎？在太空梭上工作嗎？', mode='word')
    print(res)



