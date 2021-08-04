# -*- coding=utf-8 -*-
"""
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP
"""

__version__ = '1.3.27'

import os

from jionlp.util.logger import set_logger
from jionlp.util.zip_file import unzip_file, UNZIP_FILE_LIST


logging = set_logger('INFO')

# unzip dictionary files
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
for file_name in UNZIP_FILE_LIST:
    if not os.path.exists(os.path.join(DIR_PATH, 'dictionary', file_name)):
        unzip_file()


guide = """
╭──────────────────────────────────────────────────────────────────────────╮
│ • • • ░░░░░░░░░░░░░░░░░░░░░░  Important Message  ░░░░░░░░░░░░░░░░░░░░░░░ │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│           JioNLP, a python tool for Chinese NLP preprocessing.           │
│               URL: https://github.com/dongrixinyu/JioNLP                 │
│                                                                          │
│   | date       | updated funcs and info                              |   │
│   | ---------- | --------------------------------------------------- |   │
│   | 2020-03-13 | first push                                          |   │
│   | 2020-03-18 | update rules                                        |   │
│   | 2020-03-24 | add traditional and simplified conversion           |   │
│   | 2020-03-26 | add location parser 2019                            |   │
│   | 2020-03-31 | add sentences splitter                              |   │
│   | 2020-04-02 | add id chard parser                                 |   │
│   | 2020-04-03 | add stopwords remover                               |   │
│   | 2020-04-26 | add pinyin and location recognizer                  |   │
│   | 2020-05-26 | add chinese word, char, xiehouyu dict               |   │
│   | 2020-06-01 | add ner tools                                       |   │
│   | 2020-06-10 | add location recognizer                             |   │
│   | 2020-06-30 | add char radical parser                             |   │
│   | 2020-07-07 | add ner acceleration tools and lexicon ner tool     |   │
│   | 2020-07-13 | add sim hash tool                                   |   │
│   | 2020-07-14 | add sentiment analysis                              |   │
│   | 2020-07-27 | add key phrase extraction - ckpe                    |   │
│   | 2020-08-24 | update pinyin                                       |   │
│   | 2020-09-14 | add back translation for data augmentation          |   │
│   | 2020-10-16 | update 2020 china location dictionary               |   │
│   | 2020-10-19 | add zip_file for compressing the size of dict files |   │
│   | 2020-11-10 | add extractive summary func                         |   │
│   | 2020-11-24 | add phone location recognition                      |   │
│   | 2020-12-18 | add idiom solitaire                                 |   │
│   | 2020-12-28 | add help searching tool                             |   │
│   | 2021-01-19 | add money number to character tool                  |   │
│   | 2021-01-22 | update outdated china location conversion           |   │
│   | 2021-02-01 | acquire 400 stars and 58 forks on Github            |   │
│   | 2021-02-02 | add swap char position text augmentation            |   │
│   | 2021-02-09 | add homophone and add & delete text augmentation    |   │
│   | 2021-02-10 | update dictionaries                                 |   │
│   | 2021-03-15 | update chinese char dictionaries                    |   │
│   | 2021-03-18 | add replace entity text augmentation                |   │
│   | 2021-03-24 | update extract money and standardization            |   │
│   | 2021-04-21 | add solar lunar date conversion                     |   │
│   | 2021-06-23 | add time parser                                     |   │
│   | 2021-07-04 | update time parser                                  |   │
│   | 2021-07-18 | update time parser                                  |   │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯
"""


from jionlp.util import *
from jionlp.dictionary import *
from jionlp.rule import *
from jionlp.gadget import *
from jionlp.textaug import *
from jionlp.algorithm import *

# from jionlp.util.fast_loader import FastLoader
# rule = FastLoader('rule', globals(), 'jionlp.rule')
