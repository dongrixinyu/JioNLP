# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    1、首先基于 pkuseg 工具做分词和词性标注，再使用 tfidf 计算文本的关键词权重，
    2、关键词提取算法找出碎片化的关键词，然后再根据相邻关键碎片词进行融合，重新计算权重，去除相似词汇。得到的融合的多个关键碎片即为关键短语。
        1、短语的 token 长度不超过 12
        2、短语中不可出现超过1个虚词
        3、短语的两端 token 不可是虚词和停用词
        4、短语中停用词数量不可以超过规定个数
        5、短语重复度计算 MMR 添加其中
        6、提供仅抽取名词短语功能
    3、使用预训练好的 LDA 模型，计算文本的主题概率分布，以及每一个候选短语的主题概率分布，得到最终权重

"""

import os
import re
import json
import numpy as np
import pkuseg

from jionlp import logging
from jionlp.rule import clean_text
from jionlp.gadget import split_sentence
from jionlp.dictionary import stopwords_loader
from jionlp.dictionary import idf_loader
from jionlp.util import pkuseg_postag_loader


DIR_PATH = os.path.dirname(os.path.abspath(__file__))


class Chunking(object):
    """ 根据词性和规则，从文本中找出名词类短语
    """
    def __init__(self):
        pass

    def __call__(self, text):
        pass


class ChineseKeyPhrasesExtractor(object):
    """ 关键短语提取在生成词云、提供摘要阅读、关键信息检索等任务中有重要作用，
    来作为文本的关键词。

    原理简述：在 tfidf 方法提取的碎片化的关键词（默认使用 pkuseg 的分词工具）基础上，
    将在文本中相邻的关键词合并，并根据权重进行调整，同时合并较为相似的短语，并结合
    LDA 模型，寻找突出主题的词汇，增加权重，组合成结果进行返回。

    Args:
        text: utf-8 编码中文文本
        top_k: (int) 选取多少个关键短语返回，默认为 5，若为 -1 返回所有短语
        with_weight: 指定返回关键短语是否需要短语权重
        func_word_num: 允许短语中出现的虚词个数，strict_pos 为 True 时无效
        stop_word_num: 允许短语中出现的停用词个数，strict_pos 为 True 时无效
        max_phrase_len: 允许短语的最长长度，默认为 25 个字符
        topic_theta: 主题权重的权重调节因子，默认0.5，范围（0~无穷）
        strict_pos: (bool) 为 True 时仅允许名词短语出现
        allow_pos_weight: (bool) 考虑词性权重，即某些词性组合的短语首尾更倾向成为关键短语
        allow_length_weight: (bool) 考虑词性权重，即 token 长度为 2~5 的短语倾向成为关键短语
        allow_topic_weight: (bool) 考虑主题突出度，它有助于过滤与主题无关的短语（如日期等）
        without_person_name: (bool) 决定是否剔除短语中的人名
        without_location_name: (bool) 决定是否剔除短语中的地名
        remove_phrases_list: (list) 将某些不想要的短语剔除，使其不出现在最终结果中
        remove_words_list: (list) 将某些不想要的词剔除，使包含该词的短语不出现在最终结果中
        specified_words: (dict) 行业名词:词频，若不为空，则仅返回包含该词的短语
        bias: (int|float) 若指定 specified_words，则可选择定义权重增加值

    Examples:
        >>> import jionlp as jio
        >>> text = '朝鲜确认金正恩出访俄罗斯 将与普京举行会谈...'
        >>> key_phrases = jio.keyphrase.extract_keyphrase(text)
        >>> print(key_phrases)

        # ['俄罗斯克里姆林宫', '邀请金正恩访俄', '举行会谈',
        #  '朝方转交普京', '最高司令官金正恩']

    """
    def __init__(self, ):
        self.unk_topic_prominence_value = 0.
        
    def _prepare(self):
        # 词性预处理
        # 词性参考 https://github.com/lancopku/pkuseg-python/blob/master/tags.txt
        # jio.util.pkuseg_postag_loader()
        self.pos_name = set(pkuseg_postag_loader().keys())
        self.pos_exception = set(['u', 'p', 'c', 'y', 'e', 'o', 'w'])
        self.loose_pos_name = self.pos_name - self.pos_exception
        self.strict_pos_name = ['a', 'n', 'j', 'nr', 'ns', 'nt', 'nx', 'nz', 
                                'ad', 'an', 'vn', 'vd', 'vx']

        # 去除冗余短语的规则
        self.redundant_strict_pattern = re.compile('[\*\|`\;:丨－\<\>]')  # 有一个字符即抛弃
        self.redundant_loose_pattern = re.compile('[/\d\.\-:=a-z+,%]+')  # 全部是该字符即抛弃
        self.extra_date_ptn = re.compile('\d{1,2}[月|日]')
        
        # 加载 idf，计算其 oov 均值
        self.idf_dict = idf_loader()
        self.median_idf = sorted(self.idf_dict.values())[len(self.idf_dict) // 2]
        self.seg = pkuseg.pkuseg(postag=True)  # 北大分词器
        
        # 短语长度权重字典，调整绝大多数的短语要位于 2~6 个词之间
        # 根据人工抽取的关键短语结果，短语词长有一个泊松分布，而根据 idf 和 lda 概率的结果，也有一个
        # 分布，两者之间存在偏差，因此，直接对短语长度分布采用权重进行调节，使抽取分布逼近人工的分布。
        self.phrases_length_control_dict = {
            1: 1, 2: 5.6, 3: 1.1, 4: 2.0, 5: 0.7, 6: 0.9, 7: 0.48,
            8: 0.43, 9: 0.24, 10: 0.15, 11: 0.07, 12: 0.05}
        self.phrases_length_control_none = 0.01  # 在大于 7 时选取
        
        # 短语词性组合权重字典
        with open(os.path.join(DIR_PATH, 'pos_combine_weights.json'), 
                  'r', encoding='utf8') as f:
            self.pos_combine_weights_dict = json.load(f)
        
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
    
    def __call__(self, text, top_k=5, with_weight=False,
                 func_word_num=1, stop_word_num=0, 
                 max_phrase_len=25,
                 topic_theta=0.5, allow_pos_weight=True,
                 strict_pos=True, allow_length_weight=True,
                 allow_topic_weight=True,
                 without_person_name=False,
                 without_location_name=False,
                 remove_phrases_list=None,
                 remove_words_list=None,
                 specified_words=dict(), bias=None):
        try:
            # 初始化加载
            if self.unk_topic_prominence_value == 0.:
                self._prepare()
                
            # 配置参数
            if without_location_name:
                if 'ns' in self.strict_pos_name:
                    self.strict_pos_name.remove('ns')
                if 'ns' in self.pos_name:
                    self.pos_name.remove('ns')
            else:
                if 'ns' not in self.strict_pos_name:
                    self.strict_pos_name.append('ns')
                if 'ns' not in self.pos_name:
                    self.pos_name.append('ns')

            if without_person_name:
                if 'nr' in self.strict_pos_name:
                    self.strict_pos_name.remove('nr')
                if 'nr' in self.pos_name:
                    self.pos_name.remove('nr')
            else:
                if 'nr' not in self.strict_pos_name:
                    self.strict_pos_name.append('nr')
                if 'nr' not in self.pos_name:
                    self.pos_name.append('nr')

            # step0: 清洗文本，去除杂质
            text = clean_text(text)

            # step1: 分句，使用北大的分词器 pkuseg 做分词和词性标注
            sentences_list = split_sentence(text, criterion='fine')
            
            sentences_segs_list = list()
            counter_segs_list = list()
            for sen in sentences_list:
                sen_segs = self.seg.cut(sen)
                sentences_segs_list.append(sen_segs)
                counter_segs_list.extend(sen_segs)

            # step2: 计算词频
            total_length = len(counter_segs_list)
            freq_dict = dict()
            for word_pos in counter_segs_list:
                word, pos = word_pos
                if word in freq_dict:
                    freq_dict[word][1] += 1
                else:
                    freq_dict.update({word: [pos, 1]})

            # step3: 计算每一个词的权重，tfidf 方式
            sentences_segs_weights_list = list()
            for sen, sen_segs in zip(sentences_list, sentences_segs_list):
                sen_segs_weights = list()
                for word_pos in sen_segs:
                    word, pos = word_pos
                    if pos in self.pos_name:  # 虚词权重为 0
                        if word in self.stop_words:  # 停用词权重为 0
                            weight = 0.0
                        else:
                            if word in specified_words:  # 为词计算权重
                                if bias is None:
                                    weight = freq_dict[word][1] * self.idf_dict.get(
                                        word, self.median_idf) / total_length + 1 / specified_words[word]
                                else:
                                    weight = freq_dict[word][1] * self.idf_dict.get(
                                        word, self.median_idf) / total_length + bias
                            else:
                                weight = freq_dict[word][1] * self.idf_dict.get(
                                    word, self.median_idf) / total_length
                    else:
                        weight = 0.0
                    sen_segs_weights.append(weight)
                sentences_segs_weights_list.append(sen_segs_weights)


            # pdb.set_trace()
            # step4: 通过一定规则，找到候选短语集合，以及其权重
            candidate_phrases_dict = dict()
            for sen_segs, sen_segs_weights in zip(
                sentences_segs_list, sentences_segs_weights_list):
                sen_length = len(sen_segs)

                for n in range(1, sen_length + 1):  # n-grams
                    for i in range(0, sen_length - n + 1):
                        candidate_phrase = sen_segs[i: i + n]
                        # print(candidate_phrase)
                        # pdb.set_trace()

                        # 由于 pkuseg 的缺陷，日期被识别为 n 而非 t，故删除日期
                        res = self.extra_date_ptn.match(candidate_phrase[-1][0])
                        if res is not None:
                            continue

                        # 找短语过程中需要进行过滤，分为严格、宽松规则
                        if not strict_pos:  
                            rule_flag = self._loose_candidate_phrases_rules(
                                candidate_phrase, func_word_num=func_word_num,
                                max_phrase_len=max_phrase_len,  
                                stop_word_num=stop_word_num)
                        else:
                            rule_flag = self._strict_candidate_phrases_rules(
                                candidate_phrase, max_phrase_len=max_phrase_len)
                        if not rule_flag:
                            continue

                        # 由于 pkuseg 的缺陷，会把一些杂质符号识别为 n、v、adj，故须删除
                        redundant_flag = False
                        for item in candidate_phrase:
                            matched = self.redundant_strict_pattern.search(item[0])
                            if matched is not None:
                                redundant_flag = True
                                break
                            matched = self.redundant_loose_pattern.search(item[0])

                            if matched is not None and matched.group() == item[0]:
                                redundant_flag = True
                                break
                        if redundant_flag:
                            continue
                            
                        # 如果短语中包含了某些不想要的词，则跳过
                        if remove_words_list is not None:
                            unwanted_phrase_flag = False
                            for item in candidate_phrase:
                                if item[0] in remove_words_list:
                                    unwanted_phrase_flag = True
                                    break
                            if unwanted_phrase_flag:
                                continue

                        # 如果短语中没有一个 token 存在于指定词汇中，则跳过
                        if specified_words != dict():
                            with_specified_words_flag = False
                            for item in candidate_phrase:
                                if item[0] in specified_words:
                                    with_specified_words_flag = True
                                    break
                            if not with_specified_words_flag:
                                continue

                        # 条件六：短语的权重需要乘上'词性权重'
                        if allow_pos_weight:
                            start_end_pos = None
                            if len(candidate_phrase) == 1:
                                start_end_pos = candidate_phrase[0][1]
                            elif len(candidate_phrase) >= 2:
                                start_end_pos = candidate_phrase[0][1] + '|' + candidate_phrase[-1][1]
                            pos_weight = self.pos_combine_weights_dict.get(start_end_pos, 1.0)
                        else:
                            pos_weight = 1.0

                        # 条件七：短语的权重需要乘上 '长度权重'
                        if allow_length_weight:
                            length_weight = self.phrases_length_control_dict.get(
                                len(sen_segs_weights[i: i + n]), 
                                self.phrases_length_control_none)
                        else:
                            length_weight = 1.0

                        # 条件八：短语的权重需要加上`主题突出度权重`
                        if allow_topic_weight:
                            topic_weight = 0.0
                            for item in candidate_phrase:
                                topic_weight += self.topic_prominence_dict.get(
                                    item[0], self.unk_topic_prominence_value)
                            topic_weight = topic_weight / len(candidate_phrase)
                        else:
                            topic_weight = 0.0

                        candidate_phrase_weight = sum(sen_segs_weights[i: i + n])
                        candidate_phrase_weight *= length_weight * pos_weight
                        candidate_phrase_weight += topic_weight * topic_theta

                        candidate_phrase_string = ''.join([tup[0] for tup in candidate_phrase])
                        if remove_phrases_list is not None:
                            if candidate_phrase_string in remove_phrases_list:
                                continue
                        if candidate_phrase_string not in candidate_phrases_dict:
                            candidate_phrases_dict.update(
                                {candidate_phrase_string: [candidate_phrase, 
                                                           candidate_phrase_weight]})

            # step5: 将 overlapping 过量的短语进行去重过滤
            # 尝试了依据权重高低，将较短的短语替代重复了的较长的短语，但效果不好，故删去
            candidate_phrases_list = sorted(
                candidate_phrases_dict.items(), 
                key=lambda item: len(item[1][0]), reverse=True)

            de_duplication_candidate_phrases_list = list()
            for item in candidate_phrases_list:
                sim_ratio = self._mmr_similarity(
                    item, de_duplication_candidate_phrases_list)
                if sim_ratio != 1:
                    item[1][1] = (1 - sim_ratio) * item[1][1]
                    de_duplication_candidate_phrases_list.append(item)

            # step6: 按重要程度进行排序，选取 top_k 个
            candidate_phrases_list = sorted(
                de_duplication_candidate_phrases_list, 
                key=lambda item: item[1][1], reverse=True)

            if with_weight:
                if top_k != -1:
                    final_res = [(item[0], item[1][1]) for item in candidate_phrases_list[:top_k]
                                 if item[1][1] > 0]
                else:
                    final_res = [(item[0], item[1][1]) for item in candidate_phrases_list
                                 if item[1][1] > 0]
            else:
                if top_k != -1:
                    final_res = [item[0] for item in candidate_phrases_list[:top_k]
                                 if item[1][1] > 0]
                else:
                    final_res = [item[0] for item in candidate_phrases_list
                                 if item[1][1] > 0]
            return final_res

        except Exception as e:
            logging.error('the text is illegal. \n{}'.format(e))
            return list()

    @staticmethod
    def _mmr_similarity(candidate_item,
                        de_duplication_candidate_phrases_list):
        """ 计算 mmr 相似度，用于考察信息量 """
        sim_ratio = 0.0
        candidate_info = set([item[0] for item in candidate_item[1][0]])
        
        for de_du_item in de_duplication_candidate_phrases_list:
            no_info = set([item[0] for item in de_du_item[1][0]])
            common_part = candidate_info & no_info
            if sim_ratio < len(common_part) / len(candidate_info):
                sim_ratio = len(common_part) / len(candidate_info)
        return sim_ratio
        
    def _loose_candidate_phrases_rules(self, candidate_phrase,
                                       max_phrase_len=25, 
                                       func_word_num=1, stop_word_num=0):
        """ 按照宽松规则筛选候选短语，对词性和停用词宽松 """
        # 条件一：一个短语不能超过 12个 token
        if len(candidate_phrase) > 12:
            return False

        # 条件二：一个短语不能超过 25 个 char
        if len(''.join([item[0] for item in candidate_phrase])) > max_phrase_len:
            return False

        # 条件三：一个短语中不能出现超过一个虚词
        more_than_one_func_word_count = 0
        for item in candidate_phrase:
            if item[1] in self.pos_exception:
                more_than_one_func_word_count += 1
        if more_than_one_func_word_count > func_word_num:
            return False

        # 条件四：短语的前后不可以是虚词、停用词，短语末尾不可是动词
        if candidate_phrase[0][1] in self.pos_exception:
            return False
        if candidate_phrase[len(candidate_phrase)-1][1] in self.pos_exception:
            return False
        if candidate_phrase[len(candidate_phrase)-1][1] in ['v', 'd']:
            return False
        if candidate_phrase[0][0] in self.stop_words:
            return False 
        if candidate_phrase[len(candidate_phrase)-1][0] in self.stop_words:
            return False

        # 条件五：短语中不可以超过规定个数的停用词
        has_stop_words_count = 0
        for item in candidate_phrase:
            if item[0] in self.stop_words:
                has_stop_words_count += 1
        if has_stop_words_count > stop_word_num:
            return False
        return True
    
    def _strict_candidate_phrases_rules(self, candidate_phrase, 
                                        max_phrase_len=25):
        """ 按照严格规则筛选候选短语，严格限制在名词短语 """
        # 条件一：一个短语不能超过 12个 token
        if len(candidate_phrase) > 12:
            return False

        # 条件二：一个短语不能超过 25 个 char
        if len(''.join([item[0] for item in candidate_phrase])) > max_phrase_len:
            return False

        # 条件三：短语必须是名词短语，不能有停用词
        for idx, item in enumerate(candidate_phrase):
            if item[1] not in self.strict_pos_name:
                return False
            if idx == 0:  # 初始词汇不可以是动词
                if item[1] in ['v', 'vd', 'vx']:  # 动名词不算在内
                    return False
            if idx == len(candidate_phrase) - 1:  # 结束词必须是名词
                if item[1] in ['a', 'ad', 'vd', 'vx', 'v']:
                    return False

        # 条件四：短语中不可以有停用词
        # for item in candidate_phrase:
        #    if item[0] in self.stop_words and item[1] not in self.strict_pos_name:
        #        return False
        return True
        
    def _topic_prominence(self):
        """ 计算每个词语的主题突出度，并保存在内存 """
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
    title = '巴黎圣母院大火：保安查验火警失误 现场找到7根烟头'
    text = '法国媒体最新披露，巴黎圣母院火灾当晚，第一次消防警报响起时，负责查验的保安找错了位置，因而可能贻误了救火的最佳时机。' \
           '据法国BFMTV电视台报道，4月15日晚，巴黎圣母院起火之初，教堂内的烟雾报警器两次示警。' \
           '当晚18时20分，值班人员响应警报前往电脑指示地点查看，但没有发现火情。20分钟后，警报再次响起，保安赶到教堂顶部确认起火。' \
           '然而为时已晚，火势已迅速蔓延开来。报道援引火因调查知情者的话说，18时20分首次报警时，监控系统侦测到的失火位置准确无误。' \
           '当时没有发生电脑故障，而是负责现场查验的工作人员走错了地方，因而属于人为失误。' \
           '报道称，究竟是人机沟通出错，还是电脑系统指示有误，亦或是工作人员对机器提示理解不当？' \
           '事发当时的具体情形尚待调查确认，以厘清责任归属。' \
           '该台还证实了此前法媒的另一项爆料：调查人员在巴黎圣母院顶部施工工地上找到了7个烟头，但并未得出乱扔烟头引发火灾的结论。' \
           '截至目前，警方尚未排除其它可能性。大火发生当天（15日）晚上，巴黎检察机关便以“因火灾导致过失损毁”为由展开司法调查。' \
           '目前，巴黎司法警察共抽调50名警力参与调查工作。参与圣母院顶部翻修施工的工人、施工方企业负责人以及圣母院保安等30余人相继接受警方问话。' \
           '此前，巴黎市共和国检察官海伊茨曾表示，目前情况下，并无任何针对故意纵火行为的调查，因此优先考虑的调查方向是意外失火。' \
           '调查将是一个“漫长而复杂”的过程。现阶段，调查人员尚未排除任何追溯火源的线索。' \
           '因此，烟头、短路、喷焊等一切可能引发火灾的因素都有待核实，尤其是圣母院顶部的电路布线情况将成为调查的对象。' \
           '负责巴黎圣母院顶部翻修工程的施工企业负责人在接受法国电视一台新闻频道采访时表示，该公司部分员工向警方承认曾在脚手架上抽烟，' \
           '此举违反了工地禁烟的规定。他对此感到遗憾，但同时否认工人吸烟与火灾存在任何直接关联。' \
           '该企业负责人此前还曾在新闻发布会上否认检方关于起火时尚有工人在场的说法。他声称，火灾发生前所有在现场施工的工人都已经按点下班，' \
           '因此事发时无人在场。《鸭鸣报》在其报道中称，警方还将调查教堂电梯、电子钟或霓虹灯短路的可能性。' \
           '但由于教堂内的供电系统在大火中遭严重破坏，有些电路配件已成灰烬，几乎丧失了分析价值。' \
           '此外，目前尚难以判定究竟是短路引发大火还是火灾造成短路。25日，即巴黎圣母院发生震惊全球的严重火灾10天后，' \
           '法国司法警察刑事鉴定专家进入失火现场展开勘查取证工作，标志着火因调查的技术程序正式启动。' \
           '此前，由于灾后建筑结构仍不稳定和现场积水过多，调查人员一直没有真正开始采集取样。'
    
    ckpe_obj = ChineseKeyPhrasesExtractor()
    key_phrases = ckpe_obj(text, topic_theta=1)
    print('key_phrases_1topic: ', key_phrases)
    key_phrases = ckpe_obj(text, topic_theta=0)
    print('key_phrases_notopic: ', key_phrases)
    key_phrases = ckpe_obj(text, allow_length_weight=False, topic_theta=0.5, max_phrase_len=8)
    print('key_phrases_05topic: ', key_phrases)

