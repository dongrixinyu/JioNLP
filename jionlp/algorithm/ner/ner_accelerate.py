# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

"""
DESCRIPTION:
    该文件包含了若干种对 NER 模型进行预测(predict/inference)加速的方法。主要包括：
    1、将短句进行拼接，至接近最大序列长度。
        一般 NER 模型在输入模型前，须首先进行分句处理。但一般较短的句子，其上下文依赖
        少，不利于挖掘上下文信息；另一方面，需要大量的 pad 操作，限制了模型效率。因此
        须将较短的句子逐一拼接，至接近模型允许的序列最大长度。该方法主要由
        TokenSplitSentence 实现。
    2、将超长句子进行重叠拆解，并使用规则对其进行合并。
        输入的文本有一部分，长度超过模型允许序列最大长度，且无标点符号。这类句子一旦
        直接应用模型，一方面造成模型并行性能急剧下降，另一方面其模型效果也会下降。因此
        须将超长句子进行重叠拆分，然后再次利用规则合并，达到高速并行的效果。该方法已申
        请专利。由 TokenBreakLongSentence 实现。
    3、将相近长度的句子拼接入一个 batch，提升模型的并行能力。
        在 tensorflow 等框架中，动态处理 LSTM 等 RNN 序列，会以最长的序列为基准进行
        计算。因此，若句子长度均相近，长句和长句放入一个 batch，短句和短句放入一个
        batch，则会减少 pad 数量，提升模型的并行能力。由 TokenBatchBucket 实现。
    4、上述三种方法可以并用，也可以单独使用，并用样例如下：

        1、并用样例：
            >>> import jionlp as jio
            >>> text_list = [list(line) for line in text_list]

            >>> def func(token_lists, para=1):
            >>> ... token_lists = [['S-' + chr(ord(token) + para) for token in token_list]
            >>> ...                for token_list in token_lists]
            >>> ... return token_lists

            >>> max_sen_len = 70
            >>> token_batch_obj = jio.ner.TokenBatchBucket(func, max_sen_len=max_sen_len, batch_size=30)
            >>> token_break_obj = jio.ner.TokenBreakLongSentence(token_batch_obj, max_sen_len=max_sen_len)
            >>> token_split_obj= jio.ner.TokenSplitSentence(token_break_obj, max_sen_len=max_sen_len, combine_sentences=True)

            >>> res = token_split_obj(text_list, para=1)  # 补充 func 函数的参数
            其中，三个工具的 max_sen_len 必须保持一致。

        2、分用样例：
            允许 TokenSplitSentence, TokenBreakLongSentence 两者结合

            >>> token_break_obj = jio.ner.TokenBreakLongSentence(token_batch_obj, max_sen_len=max_sen_len)
            >>> token_split_obj= jio.ner.TokenSplitSentence(token_break_obj, max_sen_len=max_sen_len, combine_sentences=True)

            >>> res = token_break_obj(text_list, para=1)  # 补充 func 函数的参数

"""

import pdb
import re
import copy
import math


__all__ = ['TokenSplitSentence', 'TokenBreakLongSentence', 'TokenBatchBucket']


class TokenSplitSentence(object):
    """ 将句子按照标点符号拆解开，同时提供将若干短句拼接的功能。
    1、给定待并行处理的序列 token 列表。
    2、对每个句子进行分句。
    3、当前，超长序列被按序排列为子序列。
    4、输入给模型进行预测，并将结果子序列，拼接为原超长序列，其中拼接过程使用规则完成。

    Args:
        func: 按照 max_sen_len 处理数据的函数，如按照 max_sen_len
            训练得到的模型进行预测的函数。
        criterion: 分句的粒度粗细。
        max_sen_len: 用以契合 func 函数需要的模型最大长度。
        combine_sentences: 是否将最终合并结果不超过 max_sen_len 的短句进行合并。

    Return:
        tag_list: 结果列表

    Examples:
        >>> # func: [['张', '川'], ['不', '在']] => [['B-Person', 'E-Person'], ['O', 'O']]
        >>> import jionlp as jio
        >>> token_split_sentence = jio.ner.TokenSplitSentence(
                func, criterion='fine', max_sen_len=10, combine_sentences=True)

        >>> token_lists = [['张', '川'], ['不', '在']]
        >>> res = token_split_sentence(token_lists, **kwargs)
        >>> print(res)
            [['B-Person', 'E-Person'], ['O', 'O']]

    """
    def __init__(self, func, criterion='fine', max_sen_len=100, 
                 combine_sentences=False):
        self.func = func
        self.max_sen_len = max_sen_len
        self.combine_sentences = combine_sentences
        
        if criterion == 'fine':
            self.puncs = ['……', '\r\n', '，', '。', ';', '；', '…', '！',
                          '!', '?', '？', '\r', '\n', '：']
        elif criterion == 'coarse':
            self.puncs = ['。', '！', '？', '?', '!', '\n']  # 粗略划分
        else:
            raise ValueError('argument `criterion` should be either `fine` or `coarse`.')

    def __call__(self, token_lists, **kwargs):
        recover_info, punc_sen = self.__split_sentences(token_lists)
        tags = self.func(punc_sen, **kwargs)

        return self.__recover_tags(punc_sen, recover_info, tags)

    def __split_sentences(self, token_lists):
        """ 拆分一个 batch 的句子，根据标点符号拆分句子，子句之间没有重叠。标点符号保留在句子的末尾。
        eg. "今天，我去公园" => ["今天，", "我去公园"]

        :param token_lists: 字符串
        :return: sentences, starts
                 sentences: ["sentence 1", "sentence 2", ...]
                 starts: [0, 20, 40, ...]
        """
        recover_info = list()  # 恢复标点句子所需要的信息
        punc_sen = list()  # 标点切分后的子句放在这里
        for token_list in token_lists:  # token_lists 本身就是个 batch, 要事先保证其中没有空字符串
            valid_sub_sen, valid_sub_starts, complete_sen_starts, \
                complete_sen_len = self.__split_one_sentence(token_list)  # 每句信息
            recover_info.append((token_list, complete_sen_len, valid_sub_sen,
                                 valid_sub_starts, complete_sen_starts,
                                 len(valid_sub_sen)))
            punc_sen.extend(valid_sub_sen)  # 全部的子句信息进入分句 batch 中
        
        tmp_sen = list()
        for line in punc_sen:
            tmp_sen.extend(line)
            
        return recover_info, punc_sen

    def __split_one_sentence(self, token_list):
        """ 拆分一个句子为若干短句，根据标点符号拆分句子，子句之间没有重叠。标点符号保留在句子的末尾。
        eg. "今天，我去公园" => ["今天，", "我去公园"]

        :param token_list: 字符串
        :return: valid_sentences, valid_starts, sentence_starts, len(sentences)
                 valid_sentences: ["sentence 1", "sentence 2", ...] 真实可处理的子句，而非仅仅一个逗号
                 valid_starts: [0, 20, 40, ...]  真实可处理的子句 在整句中的起始位置
                 sentence_starts: 整个句子切分成的子句的起始位置，可能包含仅仅一个逗号等等
                 len(sentences): 整个句子切分后的结果，不包含标点，可能有空字符串存在
        """
        
        sentences = list()
        start_idx = -1
        for idx, word in enumerate(token_list):
            if word in self.puncs:  # 遇见标点
                if start_idx + 1 < idx:  # 说明是正常的句子末尾的一个标点
                    if self.combine_sentences and self.max_sen_len:  # 需要将短句合并
                        if len(sentences) > 0:  # 说明前面已经有了句子
                            if idx - start_idx - 1 + len(sentences[-1]) <= self.max_sen_len:
                                # 且和前一句相加长度小于等于最大长度，和前一句合并
                                sentences[-1].extend(token_list[start_idx + 1: idx + 1])
                            else:  # 和前一句长度大于最大规定长度，则不合并
                                sentences.append(token_list[start_idx + 1: idx + 1])
                        else:  # 说明这就是该字符串文章的第一个句子
                            sentences.append(token_list[start_idx + 1: idx + 1])
                    else:  # 并不将短句合并，直接按句子拆分
                        sentences.append(token_list[start_idx + 1: idx + 1])
                else:  # 说明是两个标点相连的情况，需要将该标点添加在前一句的后面
                    if len(sentences) > 0:  # 说明之前已经有了标点，将两标点拼接
                        sentences[-1].append(word)
                    else:  # 说明该句子的起始就是标点，直接插入第一个标点
                        sentences.append([word])
                start_idx = idx  # 遇到标点，调整 start_idx
                
            elif idx == len(token_list) - 1:  # 已经抵达序列的末尾
                sentences.append(token_list[start_idx + 1:])
        
        # 计算 starts 起始位置
        sentence_starts = list()
        if token_list != list():
            sentence_starts.append(0)
        for s in sentences[: -1]:
            if sentence_starts[-1] + len(s) < len(token_list):
                sentence_starts.append(sentence_starts[-1] + len(s))
        # 若 len(sentences) != len(sentence_starts),
        # 即 the last char in the sentence 是标点.
        
        # 过滤 empty sentence
        valid_sentences = list()
        valid_starts = list()

        for s, start in zip(sentences, sentence_starts):
            # 句子开头出现 '' 要加入，句子中出现则不加入。
            if s:
                valid_sentences.append(
                    token_list[start: start + len(s)])  # retain separator
                valid_starts.append(start)
        
        return valid_sentences, valid_starts, sentence_starts, len(sentences)

    def __recover_tags(self, punc_sen, recover_info, tags):
        """
            根据信息恢复 punc 切分前的样子
            punc_sen: 被 punc 切分之后的句子结果，且其中都只有valid子句，没有只包含标点的错误子句
            recover_info: 恢复信息，一个句子对应一个 tuple
            tags: 与 punc_sen 对应的预测出来的 tags

        """
        num = 0  # 从该数值之后的若干子句串成一个没被 punc 切过的大长句
        whole_non_punc_tags = []  # 没有被 punc 切分过的句子对应的标签

        for recover in recover_info:
            token_list, complete_sen_len, valid_sub_sen, valid_sub_starts, \
            complete_sen_starts, valid_sub_sen_len = recover
            
            # 被拆分的子句的所有 tags，不被拆分的不在此列
            sen_tags = tags[num: num + valid_sub_sen_len]
            non_punc_tags = self.__recover_one_tags(
                token_list, complete_sen_len, valid_sub_sen, valid_sub_starts,
                complete_sen_starts, sen_tags)
            
            whole_non_punc_tags.append(non_punc_tags)
            num += valid_sub_sen_len

        return whole_non_punc_tags

    @staticmethod
    def __recover_one_tags(sentence, sentence_length, sub_sentences,
                           valid_starts, sentence_starts, tags):
        """
        根据信息把碎片句子恢复成原句子
        :param sentence: 完整的句子
        :param sentence_length:
        :param sub_sentences: 真实有效的子句
        :param valid_starts: 真实非空子句的起始值
        :param sentence_starts: 所有的子句的起始值
        :param tags: 每个真实子句的标签列表
        :return:
        """
        # concat the sub tags
        whole_tags = []
        for start_num in sentence_starts:
            if start_num in valid_starts:
                whole_tags.extend(tags[valid_starts.index(start_num)])
            else:
                whole_tags.extend('O')
        
        return whole_tags
    
    
class TokenBreakLongSentence(object):
    """ 将超长句重叠切分为若干部分。
    1、前提，句子经过了分句，得到了分句后的结果。
    2、给定 max_sen_len 模型指定的最大序列长度，对超过的句子，进行拆解，其中相邻两
        片子序列需要有重叠值 overlap，用于后续恢复。
    3、当前，超长序列被按序排列为子序列。
    4、输入给模型进行预测，并将结果子序列，拼接为原超长序列，其中拼接过程使用规则完成。

    Args:
        func: 按照 max_sen_len 处理数据的函数，如按照 max_sen_len
            训练得到的模型进行预测的函数。
        max_sen_len: 用以契合 func 函数需要的模型最大长度。
        batch_size: 用以契合 func 函数需要的模型 batch 大小。

    Return:
        tag_list: 结果列表

    Examples:
        >>> # func: [['张', '川'], ['不', '在']] => [['B-Person', 'E-Person'], ['O', 'O']]
        >>> import jionlp as jio
        >>> token_break_long_sentence = jio.ner.TokenBreakLongSentence(
                func, max_sen_len=10, overlap=3)

        >>> token_lists = [['张', '川'], ['不', '在']]
        >>> res = token_break_long_sentence(token_lists, **kwargs)
        >>> print(res)
            [['B-Person', 'E-Person'], ['O', 'O']]

    """
    def __init__(self, func, max_sen_len=50, overlap=20):
        self.func = func
        self.max_sen_len = max_sen_len
        self.overlap = overlap

    def __call__(self, sentences, **kwargs):
        sub_sentences, starts = self.__break_long_sentence(sentences)
        tags = self.func(sub_sentences, **kwargs)
        
        return self.__recover_tags(sub_sentences, starts, tags)

    def __break_long_sentence(self, sentences):
        """ 将长的句子强制拆分成短句，最大句子长度为50，子句之间重叠
            e.g. "我爱北京天安门" => ["我爱北京", "北京天安", "天安门"]
            上例中，max_length=4, overlap=2

        Args:
            max_length: 最大子句长度，默认50
            overlap: 相邻子句之间的重叠长度，默认10

        Return:
            sentences, starts
            sentences: ["sentence 1", "sentence 2", ...]
            starts: [0, 20, 40, ...]

        """
        starts = list()
        broken_sentences = list()

        for sentence in sentences:
            valid_broken_sentences, valid_broken_starts = self._break_one_sentence(
                sentence)
            starts.append(valid_broken_starts)
            broken_sentences.extend(valid_broken_sentences)
        return broken_sentences, starts

    def _break_one_sentence(self, sentence):
        valid_broken_starts = [0]
        valid_broken_sentences = list()
        
        if len(sentence) <= self.max_sen_len:
            return [sentence], [0]
        else:
            while len(sentence) > self.max_sen_len:
                valid_broken_sentences.append(
                    sentence[:self.max_sen_len])  # 添加最大长度的句子
                valid_broken_starts.append(
                    valid_broken_starts[-1] + self.max_sen_len - self.overlap)
                sentence = sentence[self.max_sen_len - self.overlap:]  # 不断被截短
            valid_broken_sentences.append(sentence)
        return valid_broken_sentences, valid_broken_starts

    def __recover_tags(self, sub_sentences, starts, tags):
        whole_tags = list()
        count = 0
        for idx, start in enumerate(starts):
            if len(start) == 1:
                whole_tags.append(tags[count])
                count += 1
            else:
                complete_tags = list()
                flag = 0  # 用于累加 tag
                for _ in start:
                    if flag == 0:
                        complete_tags.extend(
                            tags[count][:self.max_sen_len - self.overlap])
                    else:
                        complete_tags.extend(
                            tags[count][
                                self.overlap: self.max_sen_len - self.overlap])

                    overlap_1 = tags[count][self.max_sen_len - self.overlap:]
                    overlap_2 = tags[count + 1][:self.overlap]
                    # old_overlap_1 = copy.deepcopy(overlap_1)
                    # old_overlap_2 = copy.deepcopy(overlap_2)
                    
                    if overlap_1[-1][0] != 'O' and overlap_2[0][0] != 'O':
                        pass  # 两个实体都在边界上，则略过
                    elif overlap_1[-1][0] != 'O':  # 只有 overlap 1 的末尾有实体在边界上
                        for i in range(len(overlap_1)):
                            if overlap_1[-i - 1] != 'O':
                                overlap_1[-i - 1] = 'O'
                            else:
                                break
                    elif overlap_2[0][0] != 'O':  # 只有 overlap 2 的起始有实体在边界上
                        for i in range(len(overlap_2)):
                            if overlap_2[i] != 'O':
                                overlap_2[i] = 'O'
                            else:
                                break
                    else:  # 两个 overlap 都没有实体在边界上，则不需考虑
                        pass
                        
                    overlap = list()
                    for indexing, (lap_1, lap_2) in enumerate(zip(overlap_1, overlap_2)):
                        if lap_1[0] == 'I' and lap_2[0] == 'I':
                            if indexing + 1 < self.overlap and overlap_1[indexing + 1][0] == 'O':
                                # I 后面接了 O
                                overlap.append(lap_2)
                            else:
                                # 如果类型不一致，全部按照 lap_2 来处理
                                overlap.append(lap_2)
                        elif lap_1[0] == 'I' and lap_2[0] == 'E':
                            if indexing + 1 < self.overlap and overlap_1[indexing + 1][0] == 'O':
                                overlap.append(lap_2)
                            else:
                                # 如果类型不一致，全部按照 lap_1 处理
                                overlap.append(lap_1)
                        elif lap_1[0] == 'I' and lap_2[0] == 'B':
                            overlap.append(lap_1)
                        elif lap_1[0] in 'BE' and lap_2[0] == 'I':
                            overlap.append(lap_2)
                        elif lap_1[0] == 'O' and lap_2[0] in 'BIOES':
                            overlap.append(lap_2)
                        elif lap_1[0] == 'B' and lap_2[0] == 'E':
                            overlap.append('I' + lap_2[2:])
                        elif lap_1[0] in 'BIES' and lap_2[0] == 'O':
                            overlap.append(lap_1)
                        elif lap_1[0] == 'B' and lap_2[0] == 'B':
                            overlap.append(lap_2)
                        elif lap_1[0] == 'E' and lap_2[0] == 'E':
                            overlap.append(lap_2)
                        elif lap_1[0] == 'E' and lap_2[0] == 'B':
                            overlap.append('I' + lap_2[2:])
                        elif lap_1[0] in 'EIBS' and lap_2[0] == 'S':
                            overlap.append(lap_1)
                        elif lap_1[0] == 'S' and lap_2[0] in 'BIE':
                            overlap.append(lap_2)
                        else:
                            raise ValueError(
                                'a tag unknown! `{}` or `{}`'.format(
                                    lap_1, lap_2))
                    flag += 1
                    count += 1

                    complete_tags.extend(overlap)
                    if flag == len(start) - 1:
                        complete_tags.extend(tags[count][self.overlap:])
                        break

                # 类型合并. 在结合的时候可能会出现不同类别的实体结合在一起类型穿插
                entity_type = ''  # 优化 tags，把一个实体中的类别调整一致，初始为空
                optimized_tags = list()
                for tag in reversed(complete_tags):
                    if 'E' in tag[:2]:
                        entity_type = tag[2:]
                        optimized_tags.append(tag)
                    elif 'I' in tag[:2]:
                        tag = 'I-' + entity_type
                        optimized_tags.append(tag)
                    elif 'O' in tag[:2]:
                        optimized_tags.append(tag)
                    elif 'B' in tag[:2]:
                        tag = 'B-' + entity_type
                        optimized_tags.append(tag)
                    elif 'S' in tag[:2]:
                        tag = 'S-' + entity_type
                        optimized_tags.append(tag)
                    else:
                        raise ValueError('a tag unknown! `{}`'.format(tag))
                optimized_tags.reverse()

                whole_tags.append(optimized_tags)
                count += 1
                
        return whole_tags

    
class TokenBatchBucket(object):
    """ 对待输入给模型的序列，进行桶排序。
    1、确定所有的序列长度均在 max_sen_len 之内，不允许有超出，否则桶的个数不受限制。
    2、按桶分配所有序列，长度一致的分在一组，并将其按照 batch_size 进行拼装。
    3、当前，所有序列的顺序均打乱，按长度排序。
    4、输入给模型进行预测，并将结果按照原序进行排列。

    Args:
        func: 按照 max_sen_len 和 batch_size 处理数据的函数，如按照 max_sen_len
            训练得到的模型，以 batch_size 大小进行预测的函数。
        max_sen_len: 用以契合 func 函数需要的模型最大长度。
        batch_size: 用以契合 func 函数需要的模型 batch 大小。

    Return:
        tag_list: 结果列表

    Examples:
        >>> # func: [['张', '川'], ['不', '在']] => [['B-Person', 'E-Person'], ['O', 'O']]
        >>> import jionlp as jio
        >>> token_batch_bucket = jio.ner.TokenBatchBucket(
                func, max_sen_len=10, batch_size=2)

        >>> token_lists = [['张', '川'], ['不', '在']]
        >>> res = token_batch_bucket(token_lists, **kwargs)
        >>> print(res)
            [['B-Person', 'E-Person'], ['O', 'O']]

    """
    def __init__(self, func, max_sen_len=100, batch_size=1000):
        """ 默认最大的长度指定已经 """
        self.func = func
        self.max_sen_len = max_sen_len
        self.batch_size = batch_size
        
    def __call__(self, token_lists, **kwargs):
        batch_bucket, idx_bucket = self.make_bucket(token_lists)
        
        batch_tags = list()
        for batch in batch_bucket:
            tmp_batch_tags = self.func(batch, **kwargs)
            batch_tags.append(tmp_batch_tags)
        
        batch_tags = self.resolve_bucket(batch_tags, idx_bucket)
        return batch_tags
        
    @staticmethod
    def list_concat(bucket_list):
        concat_list = list()
        for bucket in bucket_list:
            concat_list.extend(bucket)
        return concat_list

    def make_batch(self, bucket_list, batch_size):
        length = len(bucket_list)
        batch_num = math.ceil(length / self.batch_size)
        batch_list = list()
        for i in range(batch_num):
            batch_list.append(
                bucket_list[i * self.batch_size: (i + 1) * self.batch_size])
        return batch_list
    
    def make_bucket(self, token_lists):
        """ 制作桶排序 """
        token_list_bucket_list = list()
        index_bucket_list = list()

        for _ in range(self.max_sen_len + 1):
            token_list_bucket_list.append(list())
            index_bucket_list.append(list())

        for i in range(len(token_lists)):
            token_list = token_lists[i]
            token_list_len = len(token_list)
            token_list_bucket_list[token_list_len].append(token_list)
            index_bucket_list[token_list_len].append(i)
        
        token_list_cat = self.list_concat(token_list_bucket_list)
        index_cat = self.list_concat(index_bucket_list)
        
        batch_bucket = self.make_batch(token_list_cat, self.batch_size)
        idx_bucket = self.make_batch(index_cat, self.batch_size)

        return batch_bucket, idx_bucket

    def resolve_bucket(self, batch_bucket, idx_bucket):
        """ 还原桶排序 """
        batch_cat = self.list_concat(batch_bucket)
        idx_cat = self.list_concat(idx_bucket)
        length = len(idx_cat)
        token_list = [''] * length

        for i in range(len(idx_cat)):
            token_list[idx_cat[i]] = batch_cat[i]
            
        return token_list

    
if __name__ == '__main__':
    text_list = [
        '任务型对话模型包括两种方法：Pipeline和End2End，前面介绍了问题定义和建模（任务型对话系统公式建模&&实例说明）、Pipeline方法中的SLU（总结|对话系统中的口语理解技术(SLU)（一）、总结|对话系统中的口语理解技术(SLU)（二）、总结|对话系统中的口语理解技术(SLU)（三））、DST（一文看懂任务型对话系统中的状态追踪（DST））、DPL（一文看懂任务型对话中的对话策略学习（DPL））、NLG（总结|对话系统中的自然语言生成技术（NLG））。今天简单介绍下部分End2End的方法（End2End的方法也有多种，比如：有的方法虽然是End2End的方法，但是还是单独设计模型的部件，不同部件解决Pipeline方法中的某个或多个模块；有的方法则是完全忽略Pipeline方法划分的多个模块，完全的End2End），后续抽时间会继续介绍。',
        '以搜索引擎和搜索广告为例，最重要的也最难解决的问题是语义相似度，这里主要体现在两个方面：召回和排序。在召回时，传统的文本相似性如 BM25，无法有效发现语义类 query-Doc 结果对，如"从北京到上海的机票"与"携程网"的相似性、"快递软件"与"菜鸟裹裹"的相似性。在排序时，一些细微的语言变化往往带来巨大的语义变化，如"小宝宝生病怎么办"和"狗宝宝生病怎么办"、"深度学习"和"学习深度"。',
        '',
        '',
        '新华社广州3月30日电（记者吴涛）广铁集团证实，30日11时40分，济南至广州的T179次列车运行至湖南郴州境内时发生脱轨。初步排查，脱轨原因为列车撞上受连日降雨引发的塌方山体。广铁集团表示，T179次列车隶属于广铁集团，受连日降雨影响，京广线马田墟至栖凤渡站下行区间发生线路塌方，火车司机发现后采取紧急制动措施，列车撞上塌方山体，导致机后第一节发电车起火，第二至六节车厢脱线倾覆。据广铁集团介绍，抢险救援工作已经展开，受伤的铁路员工和旅客已送医治疗，具体原因正在调查。',
        '今天天气挺好的哈！是',
        '你说呢？小伙子张少飞今天还挺好的哈！',
        '",\"upload_status\":900000}],\"file_name\":null,\"cpv\":null,\"attachment_url\":null,\"agents\":null,\"bbd_table\":\"other_prospectus\",\"company_name\":\"广州农村商业银行股份有限公司\",\"location\":\"深交所中小板\",\"_id\":\"f002d724-35ce-4981-aca1-2d8636ef041d\",\"law_office_sponsor\":null,\"representatives\":null,\"bbd_dotime\":\"2020-04-14\",\"upload_status\":null}"}',
        '........',
        '抓紧组织落实相关工作。省级政府对组合使用专项债券和市场化融资的项目建立事前评审和批准机制,对允许专项债券作为资本金的项目要重点评估论证,加强督促检查。地方各级政府负责组织制定本级专项债券项目预期收益与融资平衡方案,客观评估项目预期收益和资产价值。金融机构按照商业化原则自主决策,在不新增隐性债务前提下给予融资支持。加强部门监管合作。在地方党委和政府领导下,建立财政、金融管理、发展改革等部门协同配合机制,健全专项债券项目安排协调机制,加强地方财政、发展改革等部门与金融单位之间的沟通衔接,支持做好专项债券发行及项目配套融资工作。财政部门及时向当地发展改革、金融管理部门及金融机构提供有关专项债券项目安排信息、存量隐性债务中的必要在建项目信息等。发展改革部门按职责分工做好建设项目审批或核准工作。金融管理部门指导金融机构做好补短板重大项目和有关专项债券项目配套融资工作。推进债券项目公开。地方各级政府按照有关规定,加大地方政府债券信息公开力度,依托全国统一的集中信息公开平台,加快推进专项债券项目库公开,全面详细公开专项债券项目信息,对组合使用专项债券和市场化融资的项目以及将专项债券作为资本金的项目要单独公开,支持金融机构开展授信风险评估,让信息“多跑路”、金融机构“少跑腿”。进一步发挥主承销商作用,不断加强专项债券信息公开和持续监管工作。出现更换项目单位等重大事项的,应当第一时间告知债权人。金融机构加强专项债券项目信息应用,按照商业化原则自主决策,及时遴选符合条件的项目予以支持;需要补充信息的,地方政府及其相关部门要给予配合。建立正向激励机制。研究建立正向激励机制,将做好专项债券发行及项目配套融资工作、加快专项债券发行使用进度与全年专项债券额度分配挂钩,对专项债券发行使用进度较快的地区予以适当倾斜支持。适当提高地方政府债券作为信贷政策支持再贷款担保品的质押率,进一步提高金融机构持有地方政府债券的积极性。依法合规予以免责。既要强化责任意识,谁举债谁负责、谁融资谁负责,从严整治举债乱象,也要明确政策界限,允许合法合规融资行为,避免各方因担心被问责而不作为。对金融机构依法合规支持专项债券项目配套融资,以及依法合规支持已纳入国家和省市县级政府及收益和资产价值。金融机构按照商业化原则自主决策,在不新增隐性债务前提下给予融资支持。加强部门监管合作。在地方党委和政府领导下,建立财政、金融管理、发展改革等部门协同配合机制,健全专项债券项目安排协调机制,加强地方财政、发展改革等部门与金融单位之间的沟通衔接,支持做好专项债券发行及项目配套融资工作。财政部门及时向当地发展改革、金融管理部门及金融机构提供有关专项债券项目安排信息、存量隐性债务中的必要在建项目信息等。发展改革部门按职责分工做好建设项目审批或核准工作。金融管理部门指导金融机构做好补短板重大项目和有关专项债券项目配套融资工作。推进债券项目公开。地方各级政府按照有关规定,加大地方政府债券信息公开力度,依托全国统一的集中信息公开平台,加快推进专项债券项目库公开,全面详细公开专项债券项目信息,对组合使用专项债券和市场化融资的项目以及将专项债券作为资本金的项目要单独公开,支持金融机构开展授信风险评估,让信息“多跑路”、金融机构“少跑腿”。进一步发挥主承销商作用,不断加强专项债券信息公开和持续监管工作。出现更换项目单位等重大事项的,应当第一时间告知债权人。金融机构加强专项债券项目信息应用,按照商业化原则自主决策,及时遴选符合条件的项目予以支持;需要补充信息的,地方政府及其相关部门要给予配合。建立正向激励机制。研究建立正向激励机制,将做好专项债券发行及项目配套融资工作、加快专项债券发行使用进度与全年专项债券额度分配挂钩,对专项债券发行使用进度较快的地区予以适当倾斜支持。适当提高地方政府债券作为信贷政策支持再贷款担保品的质押率,进一步提高金融机构持有地方政府债券的积极性。依法合规予以免责。既要强化责任意识,谁举债谁部门印发的“十三五”规划并按规定权限完成审批或核准程序的项目,发展改革部门牵头提出的其他补短板重大项目,凡偿债资金来源为经营性收入、不新增隐性债务的,不认定为隐性债务问责情形。对金融机构支持存量隐性债务中的必要在建项目后续融资且不新增隐性债务的,也不认定为隐性债务问责情形。强化跟踪评估监督。地方各级政府、地方金融监管部门、金融机构动态跟踪政策执行情况,总结经验做法,梳理存在问题,及时研究提出政策建议。',
        '。',
        '''{"事件类型": "环境污染", "标题": "河北整治矿山环境 铁腕关停“散乱小”。", "正文": "作为大气污染治理的重要内容，河北2014年起启动露天矿山治理行动。记者走访太行山沿线一些矿业大市了解到 ||| ，这些地区对废弃矿山实施生态修复的同时，近年来铁腕关停“散乱小”、规范矿业开采，治理工作初显成效。同时，这项工作也面临资金缺口大、技术需完善、工作推进慢等问题。偿还旧账不欠新账2014年起，河北以632个露天矿山为重点，开展矿山环境治理。2016年，提出利用3年时间，对全省1881个露天矿山污染深度整治，对624处责任主体灭\n失矿山修复绿化。2018年，提出三年攻坚行动，实现无主矿山迹地损毁土地复垦"}''',
        '其中是移动平均值是移动的未中心方差β1是平均值的插值常数β2是未中心方差的插值常数∇L是损失的梯度指数中的括号表示它实际上不是指数而是时间步长这看起来有些可怕但需要注意的重要一点是和都只是梯度的线性插值（β* x0 +（1 - β）* x1）及其方差这为我们提供了移动平均线每个β越高我们更新每个新样本的移动平均值越少从而平滑我们对批次间梯度的均值和方差的估计这里是我们在不同测试数据集的噪声数据集上获得多少平滑的可移动平均值是移动的未中心方差β1是平均值的插值常数β2是未中心方差的插值常数∇L是损失的梯度指数中的括号表示它实际上不是指数而是时间步长这看起来有些可怕但需要注意的重要一点是和都只是梯度的线性插值（β* x0 +（1 - β）* x1）及其方差这为我们提供了移动平均线每个β越高我们更新每个新样本的移动平均值越少从而平滑我们对批次间梯度的均值和方差的估计这里是我们在不同测试数据集的噪声数据集上获得多少平滑视化']

    text_list = [list(line) for line in text_list]

    def func(token_lists, para=1):
        token_lists = [['S-' + chr(ord(token) + para) for token in token_list]
                       for token_list in token_lists]
        return token_lists
    
    max_sen_len = 70
    token_batch_obj = TokenBatchBucket(func, max_sen_len=max_sen_len, batch_size=30)
    token_break_obj = TokenBreakLongSentence(token_batch_obj, max_sen_len=max_sen_len)
    token_split_obj= TokenSplitSentence(
        token_break_obj, max_sen_len=max_sen_len, combine_sentences=True)
    
    res = token_split_obj(text_list, para=1)
    
    # 确保序列前后长度一致
    print([len(i) for i in res])
    print([len(i) for i in text_list])
    print([len(i) for i in text_list] == [len(i) for i in res])
