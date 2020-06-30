# -*- coding=utf-8 -*-
'''
TODO:
    1、偏旁部首词典基本完善准确。
    2、一些汉字有多个偏旁部首，如“岡”，既包括“山”，也包括“冂”，其字本意为“山脊”，
       因此在指定偏旁时，指定为“山”。
    3、一些变形偏旁，如“艹”、“氵”等，直接使用其原意汉字替代，如“草”、“水”等。
    4、汉字结构也有一定意义，具体为：
       0: 一体结构, 田
       1: 左右结构, 植
       2: 上下结构, 香
       3: 左中右结构, 俐
       4: 上中下结构, 意
       5: 右上包围结构, 句
       6: 左上包围结构, 病
       7: 左下包围结构, 远
       8: 全包围结构, 国
       9: 半包围结构，冈
    5、数字、字母、符号，以及一些未登录汉字等，无结构，均以 <char_radical_unk> 替代

'''


import os
import pdb

from typing import Union

from jionlp.dictionary.dictionary_loader import char_radical_loader
from .trie_tree import TrieTree


class CharRadical(object):
    ''' 
    从汉字中抽取偏旁部首，一般用于深度学习模型的特征学习。若字符没有偏旁部首，
    则添加 <char_radical_unk> 作为标记。

    args:
        text(str): 待标记偏旁的文本

    return:
        list(list(str, int)): 偏旁与结构列表

    '''
    
    def __init__(self):
        self.radicals = None
        
    def _prepare(self):
        self.radicals, self.structure_detail = char_radical_loader()
        
    def get_structure_detail(self):
        if self.radicals is None:
            self._prepare()
        
        return self.structure_detail
        
    def __call__(self, text: str):
        
        if self.radicals is None:
            self._prepare()
        
        record_list = list()  # 输出最终结果
        for char in text:
            cur_radical = self.radicals.get(
                char, ['<char_radical_unk>', 0])
            record_list.append(cur_radical)

        assert len(record_list) == len(text)
        return record_list


if __name__ == '__main__':
    char_radical = CharRadical()
    text = '今天L.A.洛杉矶天气好晴朗，一丘之貉，想吃方便面。你还在工作吗？在航天飞机上工作吗？'
    res = char_radical(text)
    for i, j in zip(text, res):
        print(i, j)

