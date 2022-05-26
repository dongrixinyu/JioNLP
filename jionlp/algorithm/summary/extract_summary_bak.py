# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import json
import numpy as np
try:
    import spacy_pkuseg as pkuseg
except:
    import pkuseg

from jionlp import logging
from jionlp.rule import clean_text
from jionlp.rule import check_chinese_char
from jionlp.gadget import split_sentence
from jionlp.dictionary import stopwords_loader
from jionlp.dictionary import idf_loader
from jionlp.util import pkuseg_postag_loader


DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class ChineseSummaryExtractor(object):
    """ 从中文文本中抽取关键句子，作为文本摘要。主要针对新闻效果较好。
    但改进空间很大，此功能仅作为 baseline。

    原理简述：为每个文本中的句子分配权重，权重计算包括 tfidf 方法的权重，以及
    LDA 主题权重，以及 lead-3 得到位置权重，并在最后结合 MMR 模型对句子做筛选，
    得到抽取式摘要。（默认使用 pkuseg 的分词工具效果好）

    Args:
        text(str): utf-8 编码中文文本，尤其适用于新闻文本
        summary_length(int): 指定文摘的长度（软指定，有可能超出）
        lead_3_weight(float): 文本的前三句的权重强调，取值必须大于1
        topic_theta(float): 主题权重的权重调节因子，默认0.2，范围（0~无穷）
        allow_topic_weight(bool): 考虑主题突出度，它有助于过滤与主题无关的句子

    Returns:
        str: 文本摘要

    Examples:
        >>> import jionlp as jio
        >>> text = '不交五险一金，老了会怎样？众所周知，五险一金非常重要...'
        >>> summary = jio.summary.extract_summary(text)
        >>> print(summary)

        # '不交五险一金，老了会怎样？'

    """
    def __init__(self):
        self.unk_topic_prominence_value = 0.

    def _prepare(self):
        self.pos_name = set(pkuseg_postag_loader().keys())
        self.strict_pos_name = ['a', 'n', 'j', 'nr', 'ns', 'nt', 'nx', 'nz',
                                'ad', 'an', 'vn', 'vd', 'vx']
        self.seg = pkuseg.pkuseg(postag=True)  # 北大分词器

        # 加载 idf，计算其 oov 均值
        self.idf_dict = idf_loader()
        self.median_idf = sorted(self.idf_dict.values())[len(self.idf_dict) // 2]

        # 读取停用词文件
        self.stop_words = stopwords_loader()

        # 加载 lda 模型参数
        self._lda_prob_matrix()

    def _lda_prob_matrix(self):
        """ 读取 lda 模型有关概率分布文件，并计算 unk 词的概率分布 """
        # 读取 p(topic|word) 概率分布文件，由于 lda 模型过大，不方便加载并计算
        # 概率 p(topic|word)，所以未考虑 p(topic|doc) 概率，可能会导致不准
        # 但是，由于默认的 lda 模型 topic_num == 100，事实上，lda 模型是否在
        # 预测的文档上收敛对结果影响不大（topic_num 越多，越不影响）。

        dict_dir_path = os.path.join(os.path.dirname(os.path.dirname(DIR_PATH)), 'dictionary')

        with open(os.path.join(dict_dir_path, 'topic_word_weight.json'),
                  'r', encoding='utf8') as f:
            self.topic_word_weight = json.load(f)
        self.word_num = len(self.topic_word_weight)

        # 读取 p(word|topic) 概率分布文件
        with open(os.path.join(dict_dir_path, 'word_topic_weight.json'),
                  'r', encoding='utf8') as f:
            self.word_topic_weight = json.load(f)
        self.topic_num = len(self.word_topic_weight)

        self._topic_prominence()  # 预计算主题突出度

    def __call__(self, text, summary_length=200, lead_3_weight=1.2,
                 topic_theta=0.2, allow_topic_weight=True):

        # 输入检查
        if type(text) is not str:
            raise ValueError('type of `text` should only be str')
        try:
            # 初始化加载
            if self.unk_topic_prominence_value == 0.:
                self._prepare()

            if lead_3_weight < 1:
                raise ValueError('the params `lead_3_weight` should not be less than 1.0')
            if len(text) <= summary_length:
                return text

            # step 0: 清洗文本
            text = clean_text(text)

            # step 1: 分句，并逐句清理杂质
            sentences_list = split_sentence(text)

            # step 2: 分词与词性标注
            sentences_segs_dict = dict()
            counter_segs_list = list()
            for idx, sen in enumerate(sentences_list):
                if not check_chinese_char(sen):  # 若无中文字符，则略过
                    continue

                sen_segs = self.seg.cut(sen)
                sentences_segs_dict.update({sen: [idx, sen_segs, list(), 0]})
                counter_segs_list.extend(sen_segs)

            # step 3: 计算词频
            total_length = len(counter_segs_list)
            freq_dict = dict()
            for word_pos in counter_segs_list:
                word, pos = word_pos
                if word in freq_dict:
                    freq_dict[word][1] += 1
                else:
                    freq_dict.update({word: [pos, 1]})

            # step 4: 计算每一个词的权重
            for sen, sen_segs in sentences_segs_dict.items():
                sen_segs_weights = list()
                for word_pos in sen_segs[1]:
                    word, pos = word_pos
                    if pos not in self.pos_name and word in self.stop_words:  # 虚词权重为 0
                        weight = 0.0
                    else:
                        weight = freq_dict[word][1] * self.idf_dict.get(
                            word, self.median_idf) / total_length
                    sen_segs_weights.append(weight)

                sen_segs[2] = sen_segs_weights
                sen_segs[3] = len([w for w in sen_segs_weights if w != 0]) / len(sen_segs_weights) \
                    if len(sen_segs_weights) == 0 else 0

            # step 5: 得到每个句子的权重
            for sen, sen_segs in sentences_segs_dict.items():
                # tfidf 权重
                tfidf_weight = sum(sen_segs[2]) / len(sen_segs[2])

                # 主题模型权重
                if allow_topic_weight:
                    topic_weight = 0.0
                    for item in sen_segs[1]:
                        topic_weight += self.topic_prominence_dict.get(
                            item[0], self.unk_topic_prominence_value)
                    topic_weight = topic_weight / len(sen_segs[1])
                else:
                    topic_weight = 0.0

                sen_weight = topic_weight * topic_theta + tfidf_weight

                # 句子长度超过限制，权重削减
                if len(sen) < 15 or len(sen) > 70:
                    sen_weight = 0.7 * sen_weight

                # LEAD-3 权重
                if sen_segs[0] < 3:
                    sen_weight *= lead_3_weight

                sen_segs[3] = sen_weight

            # step 6: 按照 MMR 算法重新计算权重，并把不想要的过滤掉
            sentences_info_list = sorted(sentences_segs_dict.items(),
                                         key=lambda item: item[1][3], reverse=True)

            mmr_list = list()
            for sentence_info in sentences_info_list:
                # 计算与已有句子的相似度
                sim_ratio = self._mmr_similarity(sentence_info, mmr_list)
                sentence_info[1][3] = (1 - sim_ratio) * sentence_info[1][3]
                mmr_list.append(sentence_info)

            # step 7: 按重要程度进行排序，选取若干个句子作为摘要
            if len(sentences_info_list) == 1:
                return sentences_info_list[0][0]
            total_length = 0
            summary_list = list()
            for idx, item in enumerate(sentences_info_list):
                if len(item[0]) + total_length > summary_length:
                    if idx == 0:
                        return item[0]
                    else:
                        # 按序号排序
                        summary_list = sorted(
                            summary_list, key=lambda item: item[1][0])
                        summary = ''.join([item[0] for item in summary_list])
                        return summary
                else:
                    summary_list.append(item)
                    total_length += len(item[0])
                    if idx == len(sentences_info_list) - 1:
                        summary_list = sorted(
                            summary_list, key=lambda item: item[1][0])
                        summary = ''.join([item[0] for item in summary_list])
                        return summary

            return text[:summary_length]
        except Exception as e:
            logging.error('the text is illegal. \n{}'.format(e))
            return ''

    def _mmr_similarity(self, sentence_info, mmr_list):
        """ 计算出每个句子和之前的句子相似性 """
        sim_ratio = 0.0
        notional_info = set([item[0] for item in sentence_info[1][1]
                             if item[1] in self.strict_pos_name])
        if len(notional_info) == 0:
            return 1.0
        for sen_info in mmr_list:
            no_info = set([item[0] for item in sen_info[1][1]
                           if item[1] in self.strict_pos_name])
            common_part = notional_info & no_info
            if sim_ratio < len(common_part) / len(notional_info):
                sim_ratio = len(common_part) / len(notional_info)
        return sim_ratio

    def _topic_prominence(self):
        """ 计算每个词语的主题突出度 """
        init_prob_distribution = np.array([self.topic_num for i in range(self.topic_num)])

        topic_prominence_dict = dict()
        for word in self.topic_word_weight:
            conditional_prob_list = list()
            for i in range(self.topic_num):
                if str(i) in self.topic_word_weight[word]:
                    conditional_prob_list.append(self.topic_word_weight[word][str(i)])
                else:
                    conditional_prob_list.append(1e-5)
            conditional_prob = np.array(conditional_prob_list)

            tmp_dot_log_res = np.log2(np.multiply(conditional_prob, init_prob_distribution))
            kl_div_sum = np.dot(conditional_prob, tmp_dot_log_res)  # kl divergence
            topic_prominence_dict.update({word: float(kl_div_sum)})

        tmp_list = [i[1] for i in tuple(topic_prominence_dict.items())]
        max_prominence = max(tmp_list)
        min_prominence = min(tmp_list)
        for k, v in topic_prominence_dict.items():
            topic_prominence_dict[k] = (v - min_prominence) / (max_prominence - min_prominence)

        self.topic_prominence_dict = topic_prominence_dict

        # 计算未知词汇的主题突出度，由于停用词已经预先过滤，所以这里不需要再考停用词无突出度
        tmp_prominence_list = [item[1] for item in self.topic_prominence_dict.items()]
        self.unk_topic_prominence_value = sum(tmp_prominence_list) / (2 * len(tmp_prominence_list))


if __name__ == '__main__':
    title = '全面解析拜登外交政策，至关重要的“对华三条”'
    text = '''海外网11月10日电当地时间9日，美国总统特朗普在推特上发文表示，美国国防部长马克·埃斯珀已经被开除。
特朗普的推文写道：“马克·埃斯珀已经被开除。我向他的付出表示感谢。”
他表示，美国国家反恐中心主任克里斯托弗·米勒将担任代理国防部长，决定立即生效。
CNN指出，埃斯珀是特朗普政府的第二位国防部长，其前任为于2018年12月辞职的詹姆斯·马蒂斯。多家美媒指出，特朗普与埃斯珀之间积怨已久。
尤其是在弗洛伊德案引发全美抗议示威后，特朗普曾威胁派出军队应对，但遭到了埃斯珀的公开反对，特朗普对他产生了极大不满。
5日，美国全国广播公司（NBC）曾援引国防部3位现任官员消息，称埃斯珀已准备好辞职信，或将辞职。
当时，国防部发言人乔纳森·霍夫曼在推特上予以否认，“埃斯珀没有辞职计划，也没有被要求提交辞呈”。
NBC报道表示，内阁部长在总统权力过渡期准备未注明日期的辞职信并不罕见，这让总统有机会替换他们。
总统会决定是否接受辞呈，这个过程通常发生在选举结果明确之后。
不过美国防部官员称，埃斯珀准备写辞职信，是因为他是长期以来预计将在选举后被赶出内阁的官员之一。（海外网 赵健行）'''

    cse_obj = ChineseSummaryExtractor()
    summary = cse_obj(text, topic_theta=0.2)
    print('summary_0.2topic: ', summary)
    summary = cse_obj(text, topic_theta=0)
    print('summary_no_topic: ', summary)
    summary = cse_obj(text, topic_theta=0.5)
    print('summary_0.5topic: ', summary)

