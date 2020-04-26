# -*- coding=utf-8 -*-

import os


DICTIONARY = {
    'stopwords.txt': '停用词词典',
    'china_location.txt': '中国地名词典，包括省、地市、县三级',
    'world_location.txt': '世界地名词典，包括洲、国家两级，国家名下包括国家全名、首都（首府）、主要城市等属性',
    'pornography.txt': '色情词典',
    'chinese_idiom.txt': '中国成语词典',
    'phrase_pinyin.txt': '包含多音字的词汇和短语的注音词典',
    'pinyin_char.txt': '所有汉字的注音词典',
    'sim2tra_word.txt': '简体转繁体字的港台和大陆用语转换词典',
    'sim2tra_char.txt': '简体转繁体字映射词典',
    'tra2sim_word.txt': '繁体转简体字的港台和大陆用语转换词典',
    'tra2sim_char.txt': '繁体转简体映射词典',
}


from .dictionary_loader import china_location_loader
from .dictionary_loader import world_location_loader
from .dictionary_loader import stopwords_loader
from .dictionary_loader import chinese_idiom_loader
from .dictionary_loader import pornography_loader
from .dictionary_loader import traditional_simplified_loader
from .dictionary_loader import pinyin_phrase_loader
from .dictionary_loader import pinyin_char_loader















