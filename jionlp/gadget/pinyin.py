# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
TODO:
    1、拼音词典并不完善
    2、拼音词典并不能完全涵盖所有多音字情况，如“任性”与“任家萱”，在人名中，“任”
       字读音为 2 声，但词典无法覆盖所有人名。
    3、若干汉字有复音，如“瓩”。
    4、数字、字母、符号等，并非没有读音，但均以 <py_unk> 替代
    5、汉语中轻声标记为数字 5
    6、声母共计 23 个，韵母共计 35 个，可以直接使用 embedding 对其进行编码

"""


from typing import Union

from jionlp.dictionary.dictionary_loader import pinyin_phrase_loader
from jionlp.dictionary.dictionary_loader import pinyin_char_loader
from .trie_tree import TrieTree


class Pinyin(object):
    """
    将汉字转为拼音，并提供额外的拼音展示方案，若对应字符无拼音，或字母、字符等，
    则添加 <py_unk> 作为标记，并且提供两种格式的返回形式。

    args:
        text(str): 待标记拼音的文本。
        formater(str): 可选择 standard、simple、detail，
            当为 standard 时，返回结果为 “佛山 ['fó', 'shān']”，方便展示查看，
            当为 simple 时，返回结果为 “佛山 ['fo2', 'shan1']”，方便输入深度
            学习模型；
            当为 detail 时，返回声母、韵母、声调。

    return:
        list(str|dict): 拼音列表
        
    Examples:
        >>> import jionlp as jio
        >>> text = '中华人民共和国。'
        >>> res1 = jio.pinyin(text)
        >>> res2 = jio.pinyin(text, formater='simple')
        >>> res3 = jio.pinyin('中国', formater='detail')
        >>> print(res1)
        >>> print(res2)
        >>> print(res3)
        
        # ['zhōng', 'huá', 'rén', 'mín', 'gòng', 'hé', 'guó', '<unk>']
        # ['zhong1', 'hua2', 'ren2', 'min2', 'gong4', 'he2', 'guo2', '<unk>']
        # [{'consonant': 'zh', 'vowel': 'ong', 'tone': '1'}, 
        #  {'consonant': 'g', 'vowel': 'uo', 'tone': '2'}]

    """
    
    def __init__(self):
        self.trie_tree_obj = None
        
    def _prepare(self):
        self.py_unk = '<py_unk>'
        self.py_unk_detail = {
            'consonant': '', 'vowel': '', 'tone': ''}
        
        consonants = 'bcdfghjklmnpqrstwxyz'
        consonants = list(consonants)
        self.consonants = ['zh', 'ch', 'sh', 'ng', 'hm', 'hng']
        self.consonants.extend(consonants)
        
        self.tones = '12345'
        
        self.pinyin_phrase = pinyin_phrase_loader()
        self.pinyin_char = pinyin_char_loader()

        # 加载 trie 树
        self.trie_tree_obj = TrieTree()
        self.trie_tree_obj.build_trie_tree(self.pinyin_phrase, 'phrase')
        self.trie_tree_obj.build_trie_tree(self.pinyin_char, 'char')
        
        # 格式转换
        self._pinyin_formater()

    @staticmethod
    def _pinyin_convert_standard_2_simple(standard_pinyin, letter_map_dict):
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
        
    def _get_consonant_vowel_tone(self, simple_pinyin):
        match_flag = False
        consonant = ''
        vowel = ''
        tone = ''
        for cur_consonant in self.consonants:
            if simple_pinyin.startswith(cur_consonant):
                consonant = cur_consonant
                break
        
        vowel_tone = simple_pinyin.replace(consonant, '', 1)
        
        for cur_tone in self.tones:
            if cur_tone in vowel_tone:
                tone = cur_tone
                break
        
        vowel = vowel_tone.replace(tone, '', 1)
        
        consonant_vowel_tone = {
            'consonant': consonant, 'vowel': vowel, 'tone': tone}
        return consonant_vowel_tone
        
    def _pinyin_formater(self):
        letter_map_dict = {
            'à': 'a4', 'á': 'a2', 'ā': 'a1', 'ǎ': 'a3',
            'ò': 'o4', 'ó': 'o2', 'ō': 'o1', 'ǒ': 'o3',
            'è': 'e4', 'é': 'e2', 'ē': 'e1', 'ě': 'e3',
            'ì': 'i4', 'í': 'i2', 'ī': 'i1', 'ǐ': 'i3',
            'ù': 'u4', 'ú': 'u2', 'ū': 'u1', 'ǔ': 'u3',
            'ǜ': 'v4', 'ǘ': 'v2', 'ǖ': 'v1', 'ǚ': 'v3',
            'ǹ': 'n4', 'ń': 'n2', 'ň': 'n3', 'ü': 'v',
            'ḿ': 'm2'}
        
        pinyin_list = list()
        for char, pinyin in self.pinyin_char.items():
            pinyin_list.extend(pinyin)
        for phrase, pinyin in self.pinyin_phrase.items():
            pinyin_list.extend(pinyin)
        pinyin_list = list(set(pinyin_list))
        
        self.pinyin_formater = dict()
        for standard_pinyin in pinyin_list:
            
            if standard_pinyin == self.py_unk:
                self.pinyin_formater.update(
                    {standard_pinyin: [standard_pinyin, self.py_unk_detail]})
            else:
                simple_pinyin = self._pinyin_convert_standard_2_simple(
                    standard_pinyin, letter_map_dict)

                consonant_vowel_tone = self._get_consonant_vowel_tone(
                    simple_pinyin)
                self.pinyin_formater.update(
                    {standard_pinyin: [simple_pinyin, consonant_vowel_tone]})
        
    def __call__(self, text: str,
                 formater: Union['standard', 'simple', 'detail'] = 'standard'):

        if self.trie_tree_obj is None:
            self._prepare()
        
        if formater not in ['standard', 'simple', 'detail']:
            raise ValueError(
                '`formater` should be either `standard` or `simple`.')
        
        record_list = list()  # 输出最终结果
        i = 0
        end = len(text)
        while i < end:
            pointer = text[i: self.trie_tree_obj.depth + i]  # 遇到标点符合暂停，有优化空间
            step, typing = self.trie_tree_obj.search(pointer)
            if typing == 'phrase':
                cur_pinyin = self.pinyin_phrase[pointer[0: step]]
                
                if formater == 'standard':
                    pass
                elif formater == 'simple':
                    cur_pinyin = [self.pinyin_formater[pinyin][0]
                                  for pinyin in cur_pinyin]
                elif formater == 'detail':
                    cur_pinyin = [self.pinyin_formater[pinyin][1]
                                  for pinyin in cur_pinyin]
                
                record_list.extend(cur_pinyin)
            elif typing == 'char':
                cur_pinyin = self.pinyin_char[pointer[0: step]][0]
                if formater == 'standard':
                    pass
                elif formater == 'simple':
                    cur_pinyin = self.pinyin_formater[cur_pinyin][0]
                elif formater == 'detail':
                    cur_pinyin = self.pinyin_formater[cur_pinyin][1]

                record_list.append(cur_pinyin)
            else:
                # print(step, typing, pointer[0])
                if formater == 'standard':
                    record_list.append(self.py_unk)
                elif formater == 'simple':
                    record_list.append(self.py_unk)
                elif formater == 'detail':
                    record_list.append(self.py_unk_detail)

            i += step
        
        assert len(record_list) == len(text)
        return record_list


if __name__ == '__main__':
    pinyin = Pinyin()
    text = '今天L.A.洛杉矶天气好晴朗，一丘之貉，想吃方便面。你还在工作吗？在航天飞机上工作吗？'
    res = pinyin(text, formater='detail')
    for i, j in zip(text, res):
        print(i, j)
