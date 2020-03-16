# -*- coding=utf-8 -*-

import os

from .trie_tree import TrieTree


class TraditionalSimplifiedConversion(object):
    '''
    繁简体转换
    '''
    
    def __init__(self):
        self.trad2simp_trie_tree_obj = TrieTree()
        self.simp2trad_trie_tree_obj = TrieTree()
        
        
        
        self.trad2simp_trie_tree_obj.build_trie_tree()
        self.simp2trad_trie_tree_obj.build_trie_tree()

    























