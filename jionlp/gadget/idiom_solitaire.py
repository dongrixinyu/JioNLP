# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import random
import numpy as np

from jionlp import logging
from jionlp.dictionary.dictionary_loader import chinese_idiom_loader
from .pinyin import Pinyin


__all__ = ['IdiomSolitaire']


class IdiomSolitaire(object):
    """ 成语接龙，即前一成语的尾字和后一成语的首字（读音）相同，简单语言游戏接口。

    Args:
        cur_idiom(str): 当前输入的成语，为其寻找下一个接龙成语
        check_idiom(bool): 检查当前输入的 cur_idiom 是否是成语，默认为 False
        same_pinyin(bool): 拼音一致即可接龙，否则必须同一个汉字才可接龙，默认 True
        same_tone(bool): same_pinyin 为 True 时有效，即拼音的音调一致才可接龙，否则算错，默认为 True
        with_prob(bool): 以成语的使用频率进行返回，即常见成语更容易返回，否则更易返回罕见成语
        restart(bool): 重新开始新一轮成语接龙，即清空已使用成语列表，默认 False

    Returns:
        str: 接龙下去的成语，若接不下去，
        若返回 'wrong input idiom'，输入的不是成语
        若返回 'can not find next'，从成语词典中找不到下一个成语

    Examples:
        >>> import jionlp as jio
        >>> res = jio.idiom_solitaire(
                '见异思迁', same_pinyin=True, same_tone=True, with_prob=True)
        >>> print(res)

        # 千方百计  # 每次结果不一

    """
    def __init__(self):
        self.idiom_list = None

    def _prepare(self):
        self.pinyin_obj = Pinyin()

        idiom_dict = chinese_idiom_loader()
        self.idiom_list = list()
        for key, value in idiom_dict.items():
            pinyin = self.pinyin_obj(key, formater='simple')
            self.idiom_list.append(
                {'idiom': key, 'freq': value['freq'], 'pinyin': pinyin})

        self.pure_idiom_list = [item['idiom'] for item in self.idiom_list]

        self.already_used_idioms = set()

    def __call__(self, cur_idiom, same_pinyin=True, check_idiom=False,
                 same_tone=True, with_prob=True, restart=False):
        if self.idiom_list is None:
            self._prepare()

        if restart:
            # 重新开始游戏，清空历史记录
            self.already_used_idioms = set()

        if cur_idiom not in self.pure_idiom_list:
            logging.warning('{} may not be a Chinese idiom.'.format(cur_idiom))
            if check_idiom:
                return 'wrong input idiom'
            else:
                pass
        else:
            # add cur idiom into the already-list
            self.already_used_idioms.add(cur_idiom)

        if same_pinyin:
            cur_last_pinyin = self.pinyin_obj(cur_idiom, formater='simple')[-1]
            backup_idioms = list()
            if same_tone:
                for idiom_obj in self.idiom_list:
                    if idiom_obj['idiom'] in self.already_used_idioms:
                        continue

                    if cur_last_pinyin == idiom_obj['pinyin'][0]:
                        backup_idioms.append(idiom_obj)

            else:
                for idiom_obj in self.idiom_list:
                    if idiom_obj['idiom'] in self.already_used_idioms:
                        continue

                    if cur_last_pinyin[:-1] == idiom_obj['pinyin'][0][:-1]:
                        backup_idioms.append(idiom_obj)

        else:
            cur_last_char = cur_idiom[-1]
            backup_idioms = list()
            for idiom_obj in self.idiom_list:
                if idiom_obj in self.already_used_idioms:
                    continue

                if cur_last_char == idiom_obj['idiom'][0]:
                    backup_idioms.append(idiom_obj)

        if len(backup_idioms) == 0:
            return 'can not find next'

        if not with_prob:
            result = random.choice(backup_idioms)
            self.already_used_idioms.add(result['idiom'])
            return result['idiom']
        else:
            result = self._random_select(backup_idioms)
            self.already_used_idioms.add(result['idiom'])
            return result['idiom']

    @staticmethod
    def _random_select(backup_idioms):
        """ 按频率概率选择一个成语 """
        freq_list = [item['freq'] for item in backup_idioms]
        sum_freq = sum(freq_list)
        prob_list = [item / sum_freq for item in freq_list]
        prob = np.array(prob_list)

        result = np.random.choice(backup_idioms, p=prob.ravel())
        return result

