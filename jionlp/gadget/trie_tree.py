# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from jionlp import logging


class TrieTree(object):
    """
    Trie 树的基本方法，用途包括：
    - 词典 NER 的前向最大匹配计算
    - 繁简体词汇转换的前向最大匹配计算

    """
    def __init__(self):
        self.dict_trie = dict()
        self.depth = 0

    def add_node(self, word, typing):
        """
        向 Trie 树添加节点
        :param word: 字典中的词汇
        :param typing: 词汇类型
        :return: None
        """
        word = word.strip()
        if word not in ['', '\t', ' ', '\r']:
            tree = self.dict_trie
            depth = len(word)
            word = word.lower()  # 将所有的字母全部转换成小写
            for char in word:
                if char in tree:
                    tree = tree[char]
                else:
                    tree[char] = dict()
                    tree = tree[char]
            if depth > self.depth:
                self.depth = depth
            if 'type' in tree and tree['type'] != typing:
                logging.warning(
                    '`{}` belongs to both `{}` and `{}`.'.format(
                        word, tree['type'], typing))
            else:
                tree['type'] = typing

    def build_trie_tree(self, dict_list, typing):
        """ 创建 trie 树 """
        for word in dict_list:
            self.add_node(word, typing)

    def search(self, word):
        """ 搜索给定word字符串中与词典匹配的 entity，
        返回值 None 代表字符串中没有要找的实体，
        如果返回字符串，则该字符串就是所要找的词汇的类型
        """
        tree = self.dict_trie
        res = None
        step = 0  # step 计数索引位置
        for char in word:
            if char in tree:
                tree = tree[char]
                step += 1
                if 'type' in tree:
                    res = (step, tree['type'])
            else:
                break
        if res:
            return res
        return 1, None
