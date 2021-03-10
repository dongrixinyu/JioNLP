# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
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
    6、一些汉字的偏旁部首确实与本意有较大差别，如“爱”字，其部首为“爪”，而实际繁体字部
       首为“心”，“矮”字部首为“矢”，部首与字本意已无联系。因此，词典尽量以靠近本意的部
       首为准，且汉字和偏旁意义相差很大情况下，可以考虑以 <char_radical_unk> 标识。
    7、utf8编码的汉字，基本上是按照核心部首，以及笔画数量进行排序的，因此面对无法识别的
       字，可以选择使用 utf8 编码排序进行寻找，99% 是正确的。
    8、四角编码主要以字形笔画为基础进行编码设计，因此，其包含信息与拆字部件、字形结构等
       信息有重复之处。

"""


import os

from typing import Union

from jionlp.dictionary.dictionary_loader import char_radical_loader
from jionlp.dictionary.dictionary_loader import STRUCTURE_DICT


class CharRadical(object):
    """
    从汉字中抽取偏旁部首，一般用于深度学习模型的特征学习。若字符没有偏旁部首，
    则添加 <cr_unk> 作为标记。针对每个字，输出的结果依次是：核心偏旁部首、
    字形结构、四角编码（五位）、拆字部件。

    args:
        text(str): 待标记偏旁的文本

    return:
        list(list(str, int, str, str)): 偏旁与结构列表

    """
    
    def __init__(self):
        self.radicals = None
        
    def _prepare(self):
        self.radicals = char_radical_loader()
        self.cr_unk = '<cr_unk>'
        self.corner_coding_unk = '00000'
        self.wubi_coding_unk = 'XXXX'
        self.stroke_order_unk = '<so_unk>'
        
    def __call__(self, text: str):
        
        if self.radicals is None:
            self._prepare()
        
        record_list = list()  # 输出最终结果
        for char in text:
            radical = self.radicals.get(
                char, {'radical': self.cr_unk,
                       'structure': '一体结构',
                       'corner_coding': self.corner_coding_unk,
                       'stroke_order': self.stroke_order_unk,
                       'wubi_coding': self.wubi_coding_unk})
            record_list.append(radical)

        assert len(record_list) == len(text)
        return record_list
    
    def convert_to_vector(self, char_info):
        """ 将各类的字形与结构转换为向量，方便输入模型 """
        

if __name__ == '__main__':
    char_radical = CharRadical()
    text = '今天L.A.洛杉矶天气好晴朗，一丘之貉，想吃方便面。你还在工作吗？在航天飞机上工作吗？'
    res = char_radical(text)
    for i, j in zip(text, res):
        print(i, j)
