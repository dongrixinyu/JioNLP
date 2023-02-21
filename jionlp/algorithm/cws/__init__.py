# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


from .cws_data_converter import tag2word, word2tag
from .cws_data_correction import CWSDCWithStandardWords
from .measure import F1

f1 = F1()
