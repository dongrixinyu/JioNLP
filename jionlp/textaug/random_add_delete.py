# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import numpy as np

from jionlp.rule import check_chinese_char
from jionlp.dictionary.dictionary_loader import char_distribution_loader


class RandomAddDelete(object):
    """ 随机增删字符。
    随机在文本中增加、删除某个字符。

    原理简述：在文本中随机增加、删除某些不影响原意的字符，对文本语义不造成影响。
        例如：“23日，山东省监狱管理局原副局长王文杰等5人玩忽职守”，增删为
             "2日，山东监狱 管理局、原副局长文杰等5人玩忽职守.."。
        随机增加的字符的选择，依据对海量文本统计字符分布规律的 char_distribution.json
        文件得到，取其中的非中文字符进行添加；该分布经过了修饰，修饰方法参考
        self._prepare 方法内的注释。

    注意事项：
        1、对于某些 NLP 任务，如抽取其中时间词汇，则以上方法很容易干扰关键时间信息，
          故方法失效。待后续优化，引入控制参数，避免某类关键信息（时间、地点等被增删）。
        2、除了增删外，有一种同义词替换，本工具未采用，原因在于对语言的通畅性与语义影响
          过大，几乎找不到可用的增强文本。
          例如：“这个东西是干什么用的？”，根据同义词词林，“东西”的同义词包括“家伙”、“货色”、
               “小崽子”、“杂种”等，“这个“ 的同义词包括”此“、”斯“等。随机替换后的结果会出现
               非常离谱的文本，如 ”斯小崽子是干什么用的？“。
          经统计，同义词替换方法的语法不连贯与语义不明确比例占总数据量的 85%，
          因此本工具不采用同义词替换方法。

    Args:
        augmentation_num(int): 数据增强对该条样本的扩展个数，默认为 3
        seed(int): 控制随机交换位置每次不变，默认为 1，当为 0 时，每次调用产生结果不固定
        add_ratio(float): 对每一个位置随机增加字符概率，默认为 0.02
        delete_ratio(float): 对每一个汉字随机做删除的概率，默认为 0.02

    Returns:
        list(str): 数据增强的结果，特殊情况可以为空列表

    Examples:
        >>> import jionlp as jio
        >>> res = jio.random_add_delete('孙俪晒11年对比照庆领证纪念日，邓超被指沧桑。')
        >>> print(res)

        # ['孙俪晒11年对比照庆领证纪念日，邓超被指沧。',
        #  '孙+俪晒11年对比照庆领证纪念日，邓超被指沧桑。',
        #  '孙俪晒 11年对比照庆领证纪念日，邓超被指沧/桑。']

    """

    def __init__(self):
        self.char_keys = None

    def _prepare(self, add_ratio=0.02, delete_ratio=0.02, seed=1):
        orig_char_distribution = char_distribution_loader()
        char_distribution = dict()
        for char, distribution in orig_char_distribution.items():
            is_chinese = check_chinese_char(char)
            # 插入的字符不可以为中文字符
            # 1、此处考虑特殊情况，对一些常见标点、常见字符的分布做删除，因其易干扰结果
            # 2、高频符号出现次数极高，为平衡高频低频的字符，须做分布平滑，采用指数函数
            if not is_chinese and char not in '，：。;“”；…！!?？':
                char_distribution.update({char: np.exp(np.log10(distribution['total_num']))})

        total_num = sum(list(char_distribution.values()))
        self.char_distribution = dict()
        for char, count in char_distribution.items():
            self.char_distribution.update({char: count / total_num})
        self.char_keys = list(self.char_distribution.keys())
        self.char_probs = list(self.char_distribution.values())

        self.char_distribution = sorted(self.char_distribution.items(), key=lambda i: i[1], reverse=True)
        # self.tmp = [item[1] for item in self.char_distribution if item[1] > 0.001]

        del self.char_distribution

        self.add_ratio = add_ratio
        self.delete_ratio = delete_ratio

        self.random = np.random
        self.seed = seed
        if seed != 0:
            self.random.seed(seed)

    def _augment_one(self, text):
        char_list = list()

        for char in text:
            if np.random.uniform(0, 1) < self.add_ratio:
                added_char = np.random.choice(self.char_keys, p=self.char_probs)
                char_list.append(added_char)

            if np.random.uniform(0, 1) < self.delete_ratio:
                pass
            else:
                char_list.append(char)

        return ''.join(char_list)

    def __call__(self, text, augmentation_num=3, seed=1,
                 add_ratio=0.02, delete_ratio=0.02):
        if self.char_keys is None or self.seed != seed \
                or self.add_ratio != add_ratio or self.delete_ratio != delete_ratio:
            self._prepare(seed=seed, add_ratio=add_ratio, delete_ratio=delete_ratio)

        augmentation_text_list = list()
        count = 0

        while len(augmentation_text_list) < augmentation_num:
            augmented_text = self._augment_one(text)
            count += 1
            if count > min(augmentation_num / (self.add_ratio + self.delete_ratio),
                           len(text) / 2):
                break

            if augmented_text == text:
                continue
            if augmented_text not in augmentation_text_list:
                augmentation_text_list.append(augmented_text)

        return augmentation_text_list

