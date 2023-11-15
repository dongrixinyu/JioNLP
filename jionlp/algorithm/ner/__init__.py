# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

from .ner_data_converter import entity2tag, tag2entity, char2word, word2char
from .lexicon_ner import LexiconNER
from .ner_accelerate import TokenSplitSentence, TokenBreakLongSentence, TokenBatchBucket
from .ner_entity_compare import entity_compare
from .analyse_dataset import analyse_dataset, collect_dataset_entities
from .time_extractor import TimeExtractor
from .money_extractor import MoneyExtractor
from .measure import F1
from .check_person_name import CheckPersonName

f1 = F1()
extract_time = TimeExtractor()
extract_money = MoneyExtractor()
check_person_name = CheckPersonName()

