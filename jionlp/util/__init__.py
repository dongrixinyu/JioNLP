# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from .funcs import bracket_absence, bracket, absence
from .file_io import *
from .time_it import TimeIt
from .util_doc import pkuseg_postag_loader
from .zip_file import zip_file, unzip_file
from .help_search import HelpSearch


help = HelpSearch()

