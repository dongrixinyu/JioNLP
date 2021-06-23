# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
TODO:
    1、繁简体字、词的映射表目前并不完善。
    2、简体字主要应用在中国大陆，繁体字主要应用在香港、台湾、新加坡等地。
       各地的表述用语各不相同。因此，繁体短语融合了台湾、香港、新加坡等地
       的用法，其中绝大多数是台湾用法，如“古早味”、“呛声”等。混合多个地区
       的繁体字会对结果产生影响。港、台、大陆的繁体字写法不尽相同，且在工具
       中不做区分。
    3、繁简体短语转换有特殊情况：“勒布朗·詹姆斯”与“雷覇龍·詹姆士”，其中“·”
       是可以省略的部分，因此正向最大匹配树中，需要进行改进，即某些字符应当
       不予匹配。
    4、某些繁简体词汇存在多义，不能在所有情况均强制匹配，如“专业”和“科系”，
       “专业”必须在做名词时才可以替换，而形容词时不可替换，目前工具仍未保证
       该功能。
    5、一部分汉字简体，对应多个繁体字，在简体转繁体时，仅随机选取一个繁体字。

"""

from jionlp.dictionary.dictionary_loader import traditional_simplified_loader
from .trie_tree import TrieTree


class TSConversion(object):
    """
    给定一段文本，将其中的简体字转换为繁体字，或将繁体字转换为简体字

    """
    def __init__(self):
        self.trie_tree_obj = None
        
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
        """ 给定一段文本，将其中的繁体字转换为简体字，提供 char 和 word 两种模式：
        char 模式是按照字符逐个替换为简体字。word 模式是将港台地区的词汇表述习惯，
        替换为符合大陆表述习惯的相应词汇。采用前向最大匹配的方式执行。

        Args:
            text(str): 中文文本字符串
            mode(char|word): 选择按字逐个转换，还是按词替换。

        return:
            str: 简体文本字符串

        Examples:
            >>> import jionlp as jio
            >>> text = '今天天氣好晴朗，想喫速食麵。妳還在工作嗎？在太空梭上工作嗎？'
            >>> res1 = jio.tra2sim(text, mode='char')
            >>> res2 = jio.tra2sim(text, mode='word')
            >>> print(res1)
            >>> print(res2)

            # 今天天气好晴朗，想吃速食面。你还在工作吗？在太空梭上工作吗？
            # 今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？

        """
        if self.trie_tree_obj is None:
            self._prepare()
        
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
            record_list = list()  # 输出最终结果
            i = 0
            end = len(text)
            while i < end:
                pointer = text[i: self.trie_tree_obj.depth + i]
                step, typing = self.trie_tree_obj.search(pointer)
                if typing == 'tra':
                    # pdb.set_trace()
                    record_list.append(self.tra2sim_token[pointer[0: step]])
                else:
                    record_list.append(pointer[0: step])
                    # pdb.set_trace()
                i += step
            
            return ''.join(record_list)

    def sim2tra(self, text, mode='char'):
        """ 给定一段文本，将其中的简体字转换为繁体字，提供 char 和 word 两种模式：
        char 模式是按照字符逐个替换为简体字。word 模式是将港台地区的词汇表述习惯，
        替换为符合大陆表述习惯的相应词汇。采用前向最大匹配的方式执行。

        Args:
            text(str): 中文文本字符串
            mode(char|word): 选择按字逐个转换，还是按词替换。

        return:
            str: 繁体文本字符串

        Examples:
            >>> import jionlp as jio
            >>> text = '今天天气好晴朗，想吃方便面。你还在工作吗？在航天飞机上工作吗？'
            >>> res1 = jio.sim2tra(text, mode='char')
            >>> res2 = jio.sim2tra(text, mode='word')
            >>> print(res1)
            >>> print(res2)

            # 今天天氣好晴朗，想喫方便面。妳還在工作嗎？在航天飛機上工作嗎？
            # 今天天氣好晴朗，想喫速食麵。妳還在工作嗎？在太空梭上工作嗎？

        """
        if self.trie_tree_obj is None:
            self._prepare()
            
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
                    # pdb.set_trace()
                    record_list.append(self.sim2tra_token[pointer[0: step]])
                else:
                    assert step == 1
                    record_list.append(pointer[0: step])
                    # pdb.set_trace()
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
