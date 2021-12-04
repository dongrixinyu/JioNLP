# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、计算 分词 任务的 F1 值。

"""


import numpy as np
from jionlp import logging


class F1(object):
    """ 计算 分词 任务的 F1 值。

    Args:
        gold_lists(list(list(str))): 真实标注的样本标签序列
        pred_lists(list(list(str))): 模型预测的样本标签序列

    Returns:
        float: precision、recall、F1 值、标签准确率等

    Examples:
        >>> import jionlp as jio
        >>> gold_lists = [['B', 'I', 'I', 'B', 'I', 'B', 'B'], ['B', 'B', 'I', 'I']]
        >>> pred_lists = [['B', 'B', 'I', 'B', 'I', 'B', 'I'], ['B', 'I', 'B', 'I']]
        >>> precision, recall, average_f1 = jio.cws.f1(gold_lists, pred_lists)
        >>> print(precision, recall, average_f1)

        # 0.941, 0.934, 0.937

    """
    def __init__(self):
        self.records = list()
        self.stats = dict()

        self.labels = dict()
        self.max_label_length = 10
        self.SKIP_LABEL = ['I', 'E']

    def __call__(self, gold_lists, pred_lists):

        assert len(gold_lists) == len(pred_lists), 'the sample num must be same.'
        for sample_idx, (gold_list, pred_list) in enumerate(zip(gold_lists, pred_lists)):
            assert len(gold_list) == len(pred_list), \
                'the tag num of the {}th sample must be same.'.format(sample_idx)
            for gold_tag, pred_tag in zip(gold_list, pred_list):
                self.records.append([gold_tag, pred_tag, sample_idx])

        self._update_results()

        self.print_confusion_matrix()
        return self.print_f1_metric()

    def _update_results(self):
        self.labels = sorted(list(set(np.asarray(self.records)[:, :2].flatten())))
        self.max_label_length = max([len(label) for label in self.labels])
        num_label = len(self.labels)

        self.confusion_matrix = np.zeros(shape=[num_label, num_label], dtype=np.int8)

        label2id = {label: idx for idx, label in enumerate(self.labels)}

        num_records = len(self.records)
        for idx in range(num_records):
            gold, pred, file_idx = self.records[idx]
            gold_idx = label2id[gold]
            pred_idx = label2id[pred]
            if gold == pred:
                is_match = True
                if gold[0] in ['B', 'S']:  # 起始或独立标签
                    for i in range(idx + 1, num_records):
                        next_gold, next_predict, next_file_idx = self.records[i]
                        if next_file_idx != file_idx:
                            # 不属于同一个样本
                            break

                        if next_gold[0] not in self.SKIP_LABEL:  # E, I, M  中间或结束标签
                            idx = i - 1
                            break

                        is_match &= next_gold == next_predict

            self.confusion_matrix[gold_idx, pred_idx] += 1

        # calc the f-measure
        total_num = np.sum(self.confusion_matrix)
        for label in self.labels:
            label_id = label2id[label]
            true_positive = self.confusion_matrix[label_id, label_id]
            false_positive = np.sum(self.confusion_matrix[:, label_id]) - true_positive
            false_negative = np.sum(self.confusion_matrix[label_id, :]) - true_positive
            true_negative = total_num - true_positive - false_positive - false_negative

            if true_positive == 0:
                precision = recall = f1 = accuracy = 0
            else:
                precision, recall, f1, accuracy = F1._calculate_f1_acc(
                    true_positive, false_positive, false_negative, true_negative)
            self.stats[label] = {
                'true_positive': true_positive, 'false_positive': false_positive,
                'true_negative': true_negative, 'false_negative': false_negative,
                'precision': precision, 'recall': recall,
                'f1': f1, 'acc': accuracy}

    @staticmethod
    def _calculate_f1_acc(true_positive, false_positive, false_negative, true_negative):
        if true_positive <= 0:
            return 0.0, 0.0, 0.0, 0.0

        precision = float(true_positive) / (true_positive + false_positive)
        recall = float(true_positive) / (true_positive + false_negative)
        f_1 = 2 * precision * recall / (precision + recall)
        accuracy = float(true_positive + true_negative) / \
            (true_positive + false_positive + false_negative + true_negative)

        return precision, recall, f_1, accuracy

    def print_confusion_matrix(self):
        """ 打印混淆矩阵 confusion matrix """

        num_label = len(self.labels)

        field_width = max(self.max_label_length, int(np.log10(np.max(self.confusion_matrix))))
        field_width = field_width + 5

        message = '\nCONFUSION MATRIX:\n' + (' ' * field_width)
        field_format = "{:" + str(field_width) + "}"

        # 打印表格 title
        for i in range(num_label):
            if self.labels[i][0] in self.SKIP_LABEL:
                continue
            message += field_format.format(self.labels[i])
        message += "\n"

        # 打印各个表格字段
        for pre_id in range(num_label):
            if self.labels[pre_id][0] in self.SKIP_LABEL:
                continue
            message += field_format.format(self.labels[pre_id])
            for gold_id in range(num_label):
                if self.labels[gold_id][0] in self.SKIP_LABEL:
                    continue
                message += ("{:<" + str(field_width) + "}").format(self.confusion_matrix[gold_id, pre_id])
            message += "\n"
        message += "\n"
        message += "sequence length: {}\n".format(len(self.records))
        logging.info(message)

    def print_f1_metric(self):
        """ 打印 F1 统计结果 """
        padding = 5
        title_format = "\n\n{:" + str(self.max_label_length + padding) + "s}{:10s}{:10s}{:10s}\n" + "-" * 50 + "\n"
        message = title_format.format("label", "precision", "recall", "f1")

        field_format = "{:" + str(self.max_label_length + padding) + "s}{p:<10.1%}{r:<10.1%}{f1:<10.1%}\n"
        for label in self.labels:
            if label in self.SKIP_LABEL:
                continue
            result = self.stats[label]
            message += field_format.format(label, **result)

        message += '\n'

        # micro average
        metrics = ['true_positive', 'false_positive', 'false_negative', 'true_negative']
        micro_stat = np.zeros([len(metrics)])
        for label in self.labels:
            if label in self.SKIP_LABEL:
                continue
            for idx, m in enumerate(metrics):
                micro_stat[idx] += self.stats[label][m]
        precision, recall, f1, accuracy = F1._calculate_f1_acc(*micro_stat)
        message += field_format.format(
            "MICRO", **{'p': precision, 'r': recall, 'f1': f1})
        average_f1 = f1

        logging.info(message)

        return precision, recall, average_f1

