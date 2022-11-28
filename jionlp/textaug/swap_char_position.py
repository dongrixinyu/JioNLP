# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import random
import numpy as np

from jionlp.rule import check_any_chinese_char


class SwapCharPosition(object):
    """ 邻近汉字换位。
    随机交换相邻近字符的位置，且交换位置的距离以正态分布得到，scale 参数为1，默认比例为
    相邻字符交换占 76.4%，中间隔1个字符占比 21.8%，中间隔两个字符占比为 1.8%

    Args:
        augmentation_num(int): 数据增强对该条样本的扩展个数，默认为 3
        swap_ratio(float): 对每一个汉字的调整其位置概率，默认为 0.02
        seed(int): 控制随机交换位置每次不变，默认为 1，当为 0 时，每次调用产生结果不固定
        scale(float): 针对每个汉字与哪个位置的汉字做交换，遵循高斯分布，scale 即为分布尺度，
            scale 值越大，则交换位置的两汉字相距越远，反之越近，默认为 1.0

    Returns:
        list(str): 数据增强的结果，特殊情况可以为空列表

    Examples:
        >>> import jionlp as jio
        >>> res = jio.swap_char_position('民盟发言人：昂山素季目前情况良好')
        >>> print(res)

        # ['民盟发言人：昂季素山目前情况良好',
        #  '民盟发言人：昂山季素目前情况良好',
        #  '民盟发言人：素山昂季目前情况良好']

    """
    def __init__(self):
        self.random = None

    def _prepare(self, swap_ratio=0.03, seed=1, scale=1.0):
        self.random = random
        self.seed = seed
        self.scale = scale
        if seed != 0:
            self.random.seed(seed)
        self.swap_ratio = swap_ratio

    def _augment_one(self, text):
        char_list = list(text)
        for i in range(len(char_list)):
            if np.random.uniform(0, 1) < self.swap_ratio:
                if not check_any_chinese_char(char_list[i]):
                    continue
                change_i = self._swap_position(char_list, i)
                # print(i, change_i)
                # print(char_list[i], char_list[change_i])
                char_list[i], char_list[change_i] = char_list[change_i], char_list[i]

        return ''.join(char_list)

    def _swap_position(self, char_list, orig_pos):
        # 找到可交换取值范围
        start_pos = 0
        end_pos = -1
        while orig_pos + start_pos > 0 \
                and check_any_chinese_char(char_list[orig_pos + start_pos - 1]):
            start_pos -= 1

        while orig_pos + end_pos < len(char_list) - 1 \
                and check_any_chinese_char(char_list[orig_pos + end_pos + 1]):
            end_pos += 1
        # print(orig_pos + start_pos, orig_pos + end_pos)

        if orig_pos + start_pos == orig_pos + end_pos:
            # 孤立汉字直接返回
            return orig_pos

        # 以高斯分布选取交换值，越靠近
        while True:
            res = round(np.random.normal(0, self.scale))
            if res == 0:
                continue
            if start_pos <= res <= end_pos:
                break

        return res + orig_pos

    def __call__(self, text, augmentation_num=3, swap_ratio=0.02,
                 seed=1, scale=1.0):
        if self.random is None or self.swap_ratio != swap_ratio \
                or self.seed != seed or self.scale != scale:
            self._prepare(swap_ratio=swap_ratio,
                          seed=seed, scale=scale)

        augmentation_text_list = list()
        count = 0

        while len(augmentation_text_list) < augmentation_num:
            augmented_text = self._augment_one(text)
            count += 1
            if count > min(augmentation_num / self.swap_ratio, len(text) / 2):
                break

            if augmented_text == text:
                continue
            if augmented_text not in augmentation_text_list:
                augmentation_text_list.append(augmented_text)

        return augmentation_text_list

