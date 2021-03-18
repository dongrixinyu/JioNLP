# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import numpy as np


class ReplaceEntity(object):
    """
    利用实体识别（也包括其他恰当的序列标注任务的实体）的语料，进行实体替换，达到数据增强。

    原理简述：中文中的语义理解不依赖具体的实体，因此可以对实体进行替换，达到数据增强。
        例如：
        “新疆历史悠久，风景优美，阿美石油公司的CEO鲍威尔曾在这里建分厂。”，替换地名、机构、人名等为
        “巴西历史悠久，风景优美，阿里巴巴的CEOJack马曾在这里建分厂。”。
        当 NLP 任务与被替换的实体语义无关时，该方法成立；反之，则不应影响标签结果的实体类型。
        同时此替换方法易造成语法合理，语言通畅，但语义上存在矛盾的句子。

    Args:
        text(str): 原始文本
        augmentation_num(int): 数据增强对该条样本的扩展个数，默认为 3
        replace_ratio(float): 对每一个词汇的同音词替换概率，默认为 0.02
        seed(int): 控制随机替换词汇每次不变，默认为 1，当为 0 时，每次调用产生结果不固定

    Returns:
        list(str): 数据增强的结果，特殊情况可以为空列表

    Examples:
        >>> import jionlp as jio
        >>> replace_entity = jio.ReplaceEntity(
                {'Person':{'张守住': 3, '三矢水介':1, '刘美婷':2},
                 'Country':{'马来西亚': 2}})
        >>> aug_texts, aug_entities = jio.replace_entity(
                      '一位名叫“伊藤慧太”的男子身着日本匠人常穿的作务衣，面带微笑，用日语侃侃而谈',
                      [{'text': '伊藤慧太', 'type': 'Person', 'offset': (5, 9)},
                       {'text': '日本', 'type': 'Country', 'offset': (15, 17)}])
        >>> print(aug_texts, aug_entities)

        # aug_texts:
        # ['一位名叫“伊藤慧太”的男子身着马来西亚匠人常穿的作务衣，面带微笑，用日语侃侃而谈',
        #  '一位名叫“刘美婷”的男子身着日本匠人常穿的作务衣，面带微笑，用日语侃侃而谈',  # 语义矛盾，但不影响任务训练
        #  '一位名叫“张守住”的男子身着日本匠人常穿的作务衣，面带微笑，用日语侃侃而谈'],
        # aug_entities:
        # [[{'text': '伊藤慧太', 'type': 'Person', 'offset': (5, 9)},
        #   {'text': '马来西亚', 'type': 'Country', 'offset': [15, 19]}],
        #  [{'text': '刘美婷', 'type': 'Person', 'offset': [5, 8]},
        #   {'text': '日本', 'type': 'Country', 'offset': (14, 16)}],
        #  [{'text': '张守住', 'type': 'Person', 'offset': [5, 8]},
        #   {'text': '日本', 'type': 'Country', 'offset': (14, 16)}]])

    """
    def __init__(self, entities_dict):
        self.entities_dict = entities_dict
        self._prepare()

    def _prepare(self, replace_ratio=0.1, seed=1):
        self.random = np.random
        self.seed = seed
        if seed != 0:
            self.random.seed(seed)
        self.replace_ratio = replace_ratio

    def __call__(self, text, entities, augmentation_num=3, replace_ratio=0.1, seed=1):

        if self.replace_ratio != replace_ratio or self.seed != seed:
            self._prepare(replace_ratio=replace_ratio, seed=seed)

        entities = sorted(entities, key=lambda i: i['offset'][0])
        augmentation_text_list = list()
        augmentation_entities_list = list()
        count = 0

        while len(augmentation_text_list) < augmentation_num:
            augmented_text, augmented_entities = self._augment_one(text, entities)
            count += 1
            if count > min(augmentation_num / self.replace_ratio, len(text)):
                break

            if augmented_text == text:
                continue
            if augmented_text not in augmentation_text_list:
                augmentation_text_list.append(augmented_text)
                augmentation_entities_list.append(augmented_entities)

        return augmentation_text_list, augmentation_entities_list

    def _augment_one(self, text, entities):
        """ 根据实体词典，对文本进行扩展 """
        orig_text = text
        count = 0
        while orig_text == text or count > 20:
            count += 1
            if self.random.random() < self.replace_ratio:
                # 将该实体从词典中随机选择一个做替换
                orig_entity = self.random.choice(entities)

                candidate_list = list(self.entities_dict[orig_entity['type']].keys())
                if len(candidate_list) == 0:
                    continue
                new_entity_text = self.random.choice(candidate_list)

                orig_len = len(orig_entity['text'])
                new_len = len(new_entity_text)

                len_bias = new_len - orig_len
                new_entity = {'text': new_entity_text, 'type': orig_entity['type'],
                              'offset': [orig_entity['offset'][0],
                                         orig_entity['offset'][1] + len_bias]}

                text = ''.join([text[:orig_entity['offset'][0]], new_entity_text,
                                text[orig_entity['offset'][1]:]])
                orig_index = entities.index(orig_entity)
                new_entities = entities[:orig_index]
                new_entities.append(new_entity)
                for _entity in entities[orig_index + 1:]:
                    _entity = {'text': _entity['text'], 'type': _entity['type'],
                               'offset': (_entity['offset'][0] + len_bias,
                                          _entity['offset'][1] + len_bias)}
                    new_entities.append(_entity)

                entities = new_entities

        return text, entities

