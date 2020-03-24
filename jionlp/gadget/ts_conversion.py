# -*- coding=utf-8 -*-

import os
import pdb
#from .trie_tree import TrieTree

from dictionary_loader import traditional_simplified_loader


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
        
        # 加载 trie 树
        #self.trad2simp_trie_tree_obj = TrieTree()
        #self.simp2trad_trie_tree_obj = TrieTree()
        
        
        
        #self.trad2simp_trie_tree_obj.build_trie_tree()
        #self.simp2trad_trie_tree_obj.build_trie_tree()
    


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
            pass

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
            pass



if __name__ == '__main__':
    ts = TSConversion()
    res = ts.sim2tra('今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？')
    print(res)
    res = ts.tra2sim('今天天氣好晴朗，想吃方便面。你還在工作嗎？在航天飛機上工作嗎？')
    print(res)




