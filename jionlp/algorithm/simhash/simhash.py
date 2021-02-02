# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import re
import pdb

import ctypes


class SimHash(object):
    def __init__(self, f_topN=500):
        self.f_topN = f_topN
        self.compute = None
        self.compute_extract = None
        self.HammingDist = None
        self.initializer()

    def initializer(self):
        dirname = os.path.dirname(__file__)
        lib = ctypes.cdll.LoadLibrary(os.path.join(dirname, 'c++/simhash_c++.so'))
        lib.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p]
        lib.initializer(os.path.join(dirname, 'c++/jieba.dict.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/hmm_model.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/idf.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/stop_words.utf8').encode(encoding='utf-8', errors='strict'))
        # compute
        compute = lib.compute
        compute.argtypes = [ctypes.c_char_p, ctypes.c_int]
        compute.restype = ctypes.c_ulonglong
        self.compute = compute
        
        # compute extract
        compute_extract = lib.compute_extract
        compute_extract.argtypes = [ctypes.c_char_p, ctypes.c_int]
        compute_extract.restype = ctypes.py_object
        self.compute_extract = compute_extract
        # HammingDist
        HammingDist = lib.HammingDist
        HammingDist.argtypes = [ctypes.c_ulonglong, ctypes.c_ulonglong]
        HammingDist.restype = ctypes.c_int
        self.HammingDist = HammingDist

    def getSimHash(self, text):
        """
        获取text文本hashcode
        :param text:
        :return:
        """
        hashcode = -1
        try:
            text = text.encode(encoding='utf-8', errors='strict')
            hashcode = self.compute(text, self.f_topN)
        except Exception as e:
            print('simhash compute:', e)
        finally:
            return hashcode

    def getSimHashFeatures(self, text):
        """
        获取text文本hashcode，以及计算hashcode使用的文本特征
        :param text:
        :return:
        """
        hashcode = -1
        features = {}
        try:
            text = text.encode(encoding='utf-8', errors='strict')
            res_list = self.compute_extract(text, self.f_topN)
            for i, tmp in enumerate(res_list):
                if i == 0:
                    hashcode = tmp
                else:
                    features.update({tmp[0] + u'': tmp[1]})
        except Exception as e:
            print('simhash compute and features extract:', e)
        finally:
            return hashcode, features

    def hammingDistance(self, value1, value2):
        """
        计算两个hashcode之间的海明距离
        :param value1:
        :param value2:
        :return:
        """
        dist = -1
        try:
            dist = self.HammingDist(value1, value2)
        except Exception as e:
            print('hamming distance compute:', e)
        finally:
            return dist

        
if __name__ == '__main__':
    pass
