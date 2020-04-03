# -*- coding=utf-8 -*-

import os
import pdb

from jionlp.dictionary.dictionary_loader import stopwords_loader


class RemoveStopwords(object):
    def __init__(self):
        self.stopwords_list = None

    def _prepare(self):
        self.stopwords_list = stopwords_loader()
        
    def __call__(self, text_segs):
        ''' 给出分词之后的结果，做判定，其中分词器使用用户自定义的 '''
        if self.stopwords_list is None:
            self._prepare()
        
        res_text_segs = list()
        for word in text_segs:
            if word not in self.stopwords_list:
                res_text_segs.append(word)
        return res_text_segs
        


