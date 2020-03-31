# -*- coding=utf-8 -*-

import os
import re
import pdb


class SplitSentence(object):
    def __init__(self):
        self.puncs_fine = None
        
    def _prepare(self):
        self.puncs_fine = ['……', '\r\n', '，', '。', ';', '；', '…', '！',
                           '!', '?', '？', '\r', '\n', '“', '”', '‘', '’',
                           '：']
        self.puncs_coarse = ['。', '！', '？', '\n', '“', '”', '‘', '’']
        self.front_quote_list = ['“', '‘']
        
        self.puncs_coarse_ptn = re.compile('([。“”！？\n])')
        self.puncs_fine_ptn = re.compile('([，：。;“”；…！!?？\r\n])')
        
    def __call__(self, text, criterion='coarse'):
        '''将文本切分为若干句子

        Args:
            text(str): 字符串文本
            criterion(coarse/fine): 句子切分粒度，粗细两种 `coarse` 或 `fine`，
                `coarse` 指的是按句号级别切分，`fine` 指按所有标点符合切分，
                默认按照粗粒度进行切分
            pattern(str): 用户可指定正则模式进行切分，该字符串必须正则编译正确

        Returns:
            list(str): 句子列表

        Examples:
            >>> text = '中华古汉语，泱泱大国，历史传承的瑰宝。'
            >>> print(bbd.split_sentences(text, criterion='fine'))
            ['中华古汉语，', '泱泱大国，', '历史传承的瑰宝。']
        
        '''
        if self.puncs_fine is None:
            self._prepare()

        if criterion == 'coarse':
            tmp_list = self.puncs_coarse_ptn.split(text)
        elif criterion == 'fine':
            tmp_list = self.puncs_fine_ptn.split(text)
        else:
            raise ValueError('The parameter `criterion` must be '
                             '`coarse` or `fine`.')
        
        final_sentences = list()
        cur_flag = 0
        quote_flag = False
        for idx, sen in enumerate(tmp_list):
            if sen == '':
                continue
            if criterion == 'coarse':
                if sen in self.puncs_coarse:
                    # 前引号较为特殊，其后的一句需要与前引号合并，而不与其前一句合并
                    if sen in self.front_quote_list:
                        quote_flag = True
                        final_sentences.append(sen)
                        continue
                    if len(final_sentences) == 0:
                        final_sentences.append(sen)
                    else:
                        final_sentences[-1] = ''.join(
                            [final_sentences[-1], sen])
                    continue
            elif criterion == 'fine':
                if sen in self.puncs_fine:
                    # 前引号较为特殊，其后的一句需要与前引号合并，而不与其前一句合并
                    if sen in self.front_quote_list:
                        quote_flag = True
                        final_sentences.append(sen)
                        continue
                    if len(final_sentences) == 0:
                        final_sentences.append(sen)
                    else:
                        final_sentences[-1] = ''.join(
                            [final_sentences[-1], sen])
                    continue
            if quote_flag:
                final_sentences[-1] = ''.join([final_sentences[-1], sen])
                quote_flag = False
            else:
                final_sentences.append(sen)
                
        return final_sentences

    
if __name__ == '__main__':
    split_sentence = SplitSentence()
    text = '中华古汉语，泱泱大国，历史传承的瑰宝。。'
    res = split_sentence(text, criterion='fine')
    print(res)
    
    
    
    
    