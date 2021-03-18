# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、功能包括：NER 标注数据集的分割，列出各个类别的数据量以及占比，并计算训练集
        (training set)、验证集(validation set / dev set)、测试集(test set)的相对熵
        判断数据集分割是否合理。
    2、info dismatch 信息，百分比越小，说明数据子集类别分布越合理

"""


import os
import pdb
import random
import collections

import numpy as np

from jionlp import logging


def _stat_class(dataset_y):
    """ 统计标签集合的结果
    """
    
    convert_y = list()
    for item in dataset_y:
        convert_y.extend([i['type']for i in item])

    dataset_res = collections.Counter(convert_y).most_common()
    stat_result = dict()
    for item in dataset_res:
        stat_result.update({item[0]: [item[1], item[1] / len(convert_y)]})

    return stat_result


def _compute_kl_divergence(vector_1, vector_2):
    """ 计算两个概率分布的 kl 散度，其中 vector_1 为真实分布，vector_2 为估计分布 """
    kl_value = np.sum(np.multiply(vector_1, np.log2(
        np.multiply(vector_1, 1 / vector_2))))

    entropy_value = np.sum(np.multiply(vector_1, np.log2(1 / vector_1)))  # 交叉熵
    
    ratio = kl_value / entropy_value  # 信息量损失比例
    return kl_value, ratio


def collect_dataset_entities(dataset_y):
    """ 收集样本数据集内，所有的实体，并按照类型进行汇总。
    主要用于整理实体词典，用于 NER 的数据增强等。

    Args:
         dataset_y: 数据集的所有样本中，包含的实体的输出标签，如样例所示

    Return:
        dict(dict):
            各个类型实体的词典(实体类型、出现频数)

    Examples:
        >>> import jionlp as jio
        >>> dataset_y = [[{'type': 'Person', 'text': '马成宇', 'offset': (0, 3)},
                          {'type': 'Company', 'text': '百度', 'offset': (10, 12)}],
                         [{'type': 'Company', 'text': '国力教育公司', 'offset': (2, 8)}],
                         [{'type': 'Organization', 'text': '延平区人民法院', 'offset': (0, 7)}],
                         ...]  #
        >>> entities_dict = jio.ner.collect_dataset_entities(dataset_y)
        >>> print(entities_dict)

        # {'Person': {'马成宇': 1, '小倩': 1},
        #  'Company': {'百度': 4, '国力教育公司': 2},
        #  'Organization': {'延平区人民法院': 1, '教育局': 3}}

    """
    entities_dict = dict()
    for sample_y in dataset_y:
        for entity in sample_y:
            if entity['type'] in entities_dict:
                if entity['text'] in entities_dict[entity['type']]:
                    entities_dict[entity['type']][entity['text']] += 1
                else:
                    entities_dict[entity['type']].update({entity['text']: 1})
            else:
                entities_dict.update({entity['type']: dict()})
                entities_dict[entity['type']].update({entity['text']: 1})

    return entities_dict


def analyse_dataset(dataset_x, dataset_y, ratio=[0.8, 0.05, 0.15], shuffle=True):
    """ 将 NER 数据集按照训练、验证、测试进行划分，统计数据集中各个类别实体的数量和占比，
    计算训练、验证、测试集的相对熵，判断数据集分割是否合理。其中，dismatch 信息比例越低，
    证明数据集划分的各类别比例越贴近数据全集的分布。

    Args:
        dataset_x: 数据集的输入数据部分
        dataset_y: 数据集的输出标签
        ratio: 训练集、验证集、测试集的比例
        shuffle: 打散数据集

    Return:
        train_x, train_y, valid_x, valid_y, test_x, test_y, stats(dict):
            stats 为数据集的统计信息(数量、占比、相对熵)

    Examples:
        >>> import jionlp as jio
        >>> dataset_x = ['马成宇在...',
                         '金融国力教育公司...',
                         '延平区人民法院曾经...',
                         ...]
        >>> dataset_y = [[{'type': 'Person', 'text': '马成宇', 'offset': (0, 3)}],
                         [{'type': 'Company', 'text': '国力教育公司', 'offset': (2, 8)}],
                         [{'type': 'Organization', 'text': '延平区人民法院', 'offset': (0, 7)}],
                         ...]
        >>> train_x, train_y, valid_x, valid_y, test_x, test_y, stats = \
            ... jio.ner.analyse_dataset(dataset_x, dataset_y)
        >>> print(stats)

            whole dataset:
            Company                    573        39.68%
            Person                     495        34.28%
            Organization               376        26.04%
            total                    3,000        100.00%

            train dataset: 80.00%
            Company                    464        40.38%
            Person                     379        32.99%
            Organization               306        26.63%
            total                    2,400        100.00%

            valid dataset: 5.00%
            Person                      32        47.06%
            Company                     22        32.35%
            Organization                14        20.59%
            total                      150        100.00%

            test dataset: 15.00%
            Company                     87        38.33%
            Person                      84        37.00%
            Organization                56        24.67%
            total                      450        100.00%

            train KL divergence: 0.000546, info dismatch: 0.03%
            valid KL divergence: 0.048423, info dismatch: 3.10%
            test KL divergence: 0.002364, info dismatch: 0.15%

    """
    dataset = [[sample_x, sample_y] for sample_x, sample_y
               in zip(dataset_x, dataset_y)]
    
    if shuffle:
        random.shuffle(dataset)

    has_kl = False
    for i in range(3):
        # 为获得最佳的数据子集切分，在切分情况不好（相对熵较高，类别不全）时，需要重新
        # 切分，以获得最佳的子集类别分布。在三次都不满足的情况下，则照常返回。
        # 统计各个类别的数据数量及占比
        stats = {'train': None, 'valid': None, 'test': None, 'total': None}
        dataset_stat = _stat_class(dataset_y)
        stats['total'] = dataset_stat

        tmp_ds = list()
        current = 0
        for s in ratio:
            num = int(len(dataset) * s)
            tmp_ds.append(dataset[current: current + num])
            current += num

        train_x = [item[0] for item in tmp_ds[0]]
        train_y = [item[1] for item in tmp_ds[0]]
        valid_x = [item[0] for item in tmp_ds[1]]
        valid_y = [item[1] for item in tmp_ds[1]]
        test_x = [item[0] for item in tmp_ds[2]]
        test_y = [item[1] for item in tmp_ds[2]]

        # 统计各数据子集的统计信息
        train_stat = _stat_class(train_y)
        stats['train'] = train_stat
        valid_stat = _stat_class(valid_y)
        stats['valid'] = valid_stat
        test_stat = _stat_class(test_y)
        stats['test'] = test_stat
        
        if not (len(train_stat) == len(valid_stat) == len(test_stat)):
            # 各子集的类别数量不一致，则重新进行切分
            continue

        # 计算 KL 散度
        has_kl = True
        train_kl_value, train_ratio = _compute_kl_divergence(
            np.array([item[1][1] for item in sorted(dataset_stat.items())]),
            np.array([item[1][1] for item in sorted(train_stat.items())]))
        valid_kl_value, valid_ratio = _compute_kl_divergence(
            np.array([item[1][1] for item in sorted(dataset_stat.items())]),
            np.array([item[1][1] for item in sorted(valid_stat.items())]))
        test_kl_value, test_ratio = _compute_kl_divergence(
            np.array([item[1][1] for item in sorted(dataset_stat.items())]),
            np.array([item[1][1] for item in sorted(test_stat.items())]))

        if (train_ratio > 0.05) or (valid_ratio > 0.05) or (test_ratio > 0.05):
            # kl 散度阈值过大，说明切分的类别分布比例不一致，需要重新切分
            continue
            
        break

    # 打印信息
    stats_fmt = '{0:<20s}\t{1:>8,d}\t{2:>2.2%}'
    total_fmt = stats_fmt + '\n'
    logging.info('whole dataset:')
    for _class, info in stats['total'].items():
        logging.info(stats_fmt.format(_class, info[0], info[1]))
    sum_res = sum([info[0] for info in stats['total'].values()])
    logging.info(total_fmt.format('total', sum_res, 1.))
    
    logging.info('train dataset: {:.2%}'.format(ratio[0]))
    for _class, info in stats['train'].items():
        logging.info(stats_fmt.format(_class, info[0], info[1]))
    sum_res = sum([info[0] for info in stats['train'].values()])
    logging.info(total_fmt.format('total', sum_res, 1.))
    
    logging.info('valid dataset: {:.2%}'.format(ratio[1]))
    for _class, info in stats['valid'].items():
        logging.info(stats_fmt.format(_class, info[0], info[1]))
    sum_res = sum([info[0] for info in stats['valid'].values()])
    logging.info(total_fmt.format('total', sum_res, 1.))
    
    logging.info('test dataset: {:.2%}'.format(ratio[2]))
    for _class, info in stats['test'].items():
        logging.info(stats_fmt.format(_class, info[0], info[1]))
    sum_res = sum([info[0] for info in stats['test'].values()])
    logging.info(total_fmt.format('total', sum_res, 1.))
    
    if has_kl:
        kl_fmt = 'KL divergence: {0:.>2f}, info dismatch: {1:.2%}'
        logging.info('train ' + kl_fmt.format(train_kl_value, train_ratio))
        logging.info('valid ' + kl_fmt.format(valid_kl_value, valid_ratio))
        logging.info('test ' + kl_fmt.format(test_kl_value, test_ratio))
    
    return train_x, train_y, valid_x, valid_y, test_x, test_y, stats
