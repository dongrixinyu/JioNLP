# -*- coding=utf-8 -*-


__version__ = '1.3.8'

import os

from jionlp.util.logger import set_logger
from jionlp.util.zip_file import unzip_file


logging = set_logger('INFO')

# unzip dictionary files
DIR_PATH = os.path.dirname(os.path.abspath(__file__))
if not os.path.exists(os.path.join(DIR_PATH, 'dictionary', 'china_location.txt')):
    unzip_file()


guide = """
╭─────────────────────────────────────────────────────────────────────────╮
│ ◎ ○ ○ ░░░░░░░░░░░░░░░░░░░░░  Important Message  ░░░░░░░░░░░░░░░░░░░░░░░░│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│              JioNLP, a python tool for Chinese NLP coding.              │
│               URL: https://github.com/dongrixinyu/JioNLP                │
│                                                                         │
│   | date       | updated funcs and infos                            |   │
│   | ---------- | -------------------------------------------------- |   │
│   | 2020-09-14 | add back translation for data augmentation         |   │
│   | 2020-10-16 | update 2020 china location dictionary              |   │
│   | 2020-10-19 | add zip_file for compressing the size of dict files|   │
│   | 2020-11-10 | add extractive summary func                        |   │
│   | 2020-11-24 | add phone location recognization                   |   │
│   | 2020-12-18 | add idiom solitairing                              |   │
│                                                                         │
╰─────────────────────────────────────────────────────────────────────────╯
"""


from jionlp.util import *
from jionlp.dictionary import *
from jionlp.rule import *
from jionlp.gadget import *
from jionlp.algorithm import *

from jionlp.util.fast_loader import FastLoader


# rule = FastLoader('rule', globals(), 'jionlp.rule')
