# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: https://www.jionlp.com


__version__ = '1.5.23'


import os

from jionlp.util.logger import set_logger
from jionlp.util.zip_file import unzip_file, UNZIP_FILE_LIST

import logging
# logging = set_logger(level='INFO', log_dir_name='.cache/jionlp_logs')

# unzip dictionary files
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
for file_name in UNZIP_FILE_LIST:
    if not os.path.exists(os.path.join(DIR_PATH, 'dictionary', file_name)):
        zip_file = '.'.join(file_name.split('.')[:-1]) + '.zip'
        unzip_file(zip_file)


history = """
╭──────────────────────────────────────────────────────────────────────────╮
│ • • • ░░░░░░░░░░░░░░░░░░░░░  History Messages  ░░░░░░░░░░░░░░░░░░░░░░░░░ │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│       JioNLP, a python tool for Chinese NLP preprocessing & parsing.     │
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
│   | 2021-09-01 | add jionlp online version                           |   │
│   | 2021-10-25 | update extract money and parse money                |   │
│   | 2021-11-10 | add logger tuner                                    |   │
│   | 2021-12-04 | add chinese word segmentor tools                    |   │
│   | 2022-03-02 | update email & tel rules                            |   │
│   | 2022-03-07 | update time period parser                           |   │
│   | 2022-03-24 | add cws labeled sample correction                   |   │
│   | 2022-04-10 | update money extractor                              |   │
│   | 2022-05-26 | transfer from pkuseg to jiojio                      |   │
│   | 2022-06-13 | add new_word_discovery                              |   │
│   | 2022-06-15 | expose and update redundant char remover            |   │
│   | 2022-07-03 | add replace_xxx functions                           |   │
│   | 2022-07-30 | add extract_wechat_id functions                     |   │
│   | 2022-09-06 | fix extract_money bug                               |   │
│   | 2022-10-15 | add extract & parse motor vehicle licence plate     |   │
│   | 2022-11-27 | fix parse_location bug                              |   │
│   | 2022-11-28 | add check_xxx functions                             |   │
│   | 2023-01-05 | fix parse_money bug & dict loader bug               |   │
│   | 2023-05-01 | add llm test dataset                                |   │
│   | 2023-07-05 | add clean html & update to 1.5.*                    |   │
│   | 2023-12-12 | add MELLM algorithm to evaluate LLMs                |   │
│   | 2024-01-12 | fix set_logger bug                                  |   │
│   | 2024-06-12 | add llm_test_1.2 & fix clean_text bug               |   │
│                                                                          │
╰──────────────────────────────────────────────────────────────────────────╯
"""


from jionlp.util import *
from jionlp.dictionary import *
from jionlp.rule import *
from jionlp.gadget import *
from jionlp.textaug import *
from jionlp.algorithm import *

