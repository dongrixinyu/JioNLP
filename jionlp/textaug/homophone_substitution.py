# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import numpy as np
import jieba

from jionlp.gadget.pinyin import Pinyin
from jionlp.dictionary.dictionary_loader import word_distribution_loader


class HomophoneSubstitution(object):
    """
    采用同音词汇进行原文替换，达到数据增强的目的。

    原理简述：汉语输入法中，拼音输入法为目前使用最广泛的一种打字法，使用率占比约 97%。
        在实际使用中，常常出现同音词的打字错误，例如：原句为
        “人口危机如果无法得到及时解决，80后、90后们将受到巨大的冲击”，拼音输入法结果为
        “人口危机如果无法得到即时解决，80后、90后门将受到巨大的冲击”。
        从输入的错误来看，完全不影响人的阅读理解。
        因此，可以利用同音词汇替换，达到数据增强的目的。

        该工具中，方法具体实施时：
        1、不考虑拼音声调，因为拼音输入法基本不输入声调；
        2、考虑常见方言读音误读，如 zh 与 z 不分，eng 与 en 不分，f 与 h 不分，l 与 n 不分等情况；
        3、替换时，优先使用常用词汇（依据词频而定）；原因在于拼音输入法优先以常见词进行替换。

    Args:
        text(str): 原始文本
        augmentation_num(int): 数据增强对该条样本的扩展个数，默认为 3
        homo_ratio(float): 对每一个词汇的同音词替换概率，默认为 0.02
        allow_mispronounce(bool): 是否允许方言读音误读，如 zh 与 z 卷舌不分，默认为 True，允许词汇错音
        seed(int): 控制随机替换词汇每次不变，默认为 1，当为 0 时，每次调用产生结果不固定

    Returns:
        list(str): 数据增强的结果，特殊情况可以为空列表

    Examples:
        >>> import jionlp as jio
        >>> res = jio.homophone_substitution(
                      '中国驻英记者一向恪守新闻职业道德，为增进中英两国人民之间的了解和沟通发挥了积极作用。')
        >>> print(res)

        # ['中国驻英记者一向刻手信问职业道德，为增进中英两国人民之间的了解和沟通发挥了积极作用。',
        #  '中国驻英记者一向恪守新闻职业道德，为增进中英两国人民指尖的了解和沟通发挥了积极作用。',
        #  '中国驻英记者一向恪守新闻职业道德，为增进中英两国人民之间的了解和沟通发挥了积积作用。']

    """
    def __init__(self):
        self.word_pinyin_dict = None

    def _prepare(self, homo_ratio=0.02, seed=1):
        self.jieba_obj = jieba
        self.jieba_obj.initialize()

        self.random = np.random
        self.seed = seed
        if seed != 0:
            self.random.seed(seed)
        self.homo_ratio = homo_ratio

        self.pinyin = Pinyin()
        self._construct_word_pinyin_dict()
        self.pinyin_mispronounce = {
            'zh': 'z', 'ch': 'c', 'sh': 's',
            'z': 'zh', 'c': 'ch', 's': 'sh',
            'l': 'n', 'n': 'l', 'f': 'h', 'h': 'f',
            'in': 'ing', 'an': 'ang', 'en': 'eng',
            'ing': 'in', 'ang': 'an', 'eng': 'en'}

    def _construct_word_pinyin_dict(self):
        word_dict = word_distribution_loader()
        word_pinyin_dict = dict()
        for word, info in word_dict.items():
            word_pinyin = self.pinyin(word, formater='detail')
            word_pinyin = ''.join([item['consonant'] + item['vowel']
                                   for item in word_pinyin])

            if word_pinyin in word_pinyin_dict:
                word_pinyin_dict[word_pinyin].update({word: info['total_num']})
            else:
                word_pinyin_dict.update({word_pinyin: {word: info['total_num']}})

        # 对于总频次过低，拼音对应词汇数量过少的，予以剔除。
        self.word_pinyin_dict = dict()
        for pinyin, word_dict in word_pinyin_dict.items():
            if len(word_dict) <= 1:  # 拼音对应词汇数量过少
                continue
            word_keys = [item[0] for item in word_dict.items()]
            word_values = [item[1] for item in word_dict.items()]
            total_num = sum(word_values)
            if total_num < 10000:  # 该拼音对应的词汇总频次过低，即非常见词，不予替换
                continue
            word_values = [val / total_num for val in word_values]
            self.word_pinyin_dict.update({pinyin: [word_keys, word_values]})

        del word_pinyin_dict

    def __call__(self, text, augmentation_num=3, homo_ratio=0.02,
                 allow_mispronounce=True, seed=1):
        if self.word_pinyin_dict is None or self.homo_ratio != homo_ratio \
                or self.seed != seed:
            self._prepare(homo_ratio=homo_ratio, seed=seed)

        segs = self.jieba_obj.lcut(text)
        pinyin_segs = [self.pinyin(seg, formater='detail') for seg in segs]

        augmentation_text_list = list()
        count = 0

        while len(augmentation_text_list) < augmentation_num:
            augmented_text = self._augment_one(
                pinyin_segs, segs, allow_mispronounce=allow_mispronounce)
            count += 1
            if count > min(augmentation_num / self.homo_ratio, len(text)):
                break

            if augmented_text == text:
                continue
            if augmented_text not in augmentation_text_list:
                augmentation_text_list.append(augmented_text)

        return augmentation_text_list

    def _augment_one(self, pinyin_segs, segs, allow_mispronounce=True):
        selected_segs = list()
        for pinyin_word, word in zip(pinyin_segs, segs):
            if self.random.random() < self.homo_ratio:
                # 找到该词的拼音
                pinyin_list = list()
                for pinyin_char in pinyin_word:
                    # if pinyin_char['consonant'] in self.pinyin_mispronounce:
                    pinyin_list.append(pinyin_char['consonant'])
                    pinyin_list.append(pinyin_char['vowel'])

                if '' in pinyin_list:  # 若无对应拼音则跳过
                    selected_segs.append(word)
                    continue

                if allow_mispronounce:
                    # 找到该词的所有变音误读拼音
                    # 仅支持单独一个字的变音，不允许多个字变音，造成过大的误差
                    candidate_pinyin_list = [''.join(pinyin_list)]
                    for idx, pinyin in enumerate(pinyin_list):
                        if pinyin in self.pinyin_mispronounce:
                            candidate_pinyin_list.append(
                                ''.join([pinyin if idx != i else self.pinyin_mispronounce[pinyin]
                                         for i, pinyin in enumerate(pinyin_list)]))

                    # 确保原正确拼音的概率要大于变音误读的拼音
                    # 进行两次随机选择，若第一次选择非原正确拼音，则再选一次
                    selected_pinyin = self.random.choice(candidate_pinyin_list)
                    if selected_pinyin != ''.join(pinyin_list):
                        selected_pinyin = self.random.choice(candidate_pinyin_list)

                    if selected_pinyin in self.word_pinyin_dict:
                        selected_word = ''
                        for _ in range(len(self.word_pinyin_dict[selected_pinyin][0])):
                            selected_word = self.random.choice(
                                self.word_pinyin_dict[selected_pinyin][0],
                                p=self.word_pinyin_dict[selected_pinyin][1])
                            if selected_word != word:
                                break
                        selected_segs.append(selected_word)
                    else:
                        selected_segs.append(word)
                else:
                    selected_pinyin = ''.join(pinyin_list)
                    if selected_pinyin in self.word_pinyin_dict:
                        selected_word = ''
                        for _ in range(len(self.word_pinyin_dict[selected_pinyin][0])):
                            selected_word = self.random.choice(
                                self.word_pinyin_dict[selected_pinyin][0],
                                p=self.word_pinyin_dict[selected_pinyin][1])
                            if selected_word != word:
                                break
                        selected_segs.append(selected_word)
                    else:
                        selected_segs.append(word)
            else:
                selected_segs.append(word)
        return ''.join(selected_segs)

