# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from .dictionary_loader import char_distribution_loader
from .dictionary_loader import char_radical_loader
from .dictionary_loader import china_location_loader
from .dictionary_loader import china_location_change_loader
from .dictionary_loader import chinese_char_dictionary_loader
from .dictionary_loader import chinese_word_dictionary_loader
from .dictionary_loader import chinese_idiom_loader
from .dictionary_loader import idf_loader
from .dictionary_loader import negative_words_loader
from .dictionary_loader import phone_location_loader
from .dictionary_loader import pinyin_phrase_loader
from .dictionary_loader import pinyin_char_loader
from .dictionary_loader import pornography_loader
from .dictionary_loader import sentiment_expand_words_loader
from .dictionary_loader import sentiment_words_loader
from .dictionary_loader import stopwords_loader
from .dictionary_loader import STRUCTURE_DICT
from .dictionary_loader import telecom_operator_loader
from .dictionary_loader import traditional_simplified_loader
from .dictionary_loader import word_distribution_loader
from .dictionary_loader import world_location_loader
from .dictionary_loader import xiehouyu_loader


DICTIONARY_DESCRIPTION = {
    'char_distribution.json': '统计中文文本全量语料中有效 utf-8 字符的频次与分布',
    'china_location.txt': '中国地名词典，包括省、地市、县三级。且涵盖了该地名的简称、俗称、行政区划码。',
    'china_location_change.txt': '中国地名变更词典，包括省、地市、县三级。且涵盖了该地名的变更时间、批准部门。',
    'chinese_char_dictionary.txt': '百度汉语新华字典，字典中有两千余个多音字，每个字分别包括汉字，释义，详细释义 7 部分',
    'chinese_idiom.txt': '中国成语词典，包含成语词条、释义、出处来源、汉语拼音、例句（多数成语无）、在 100 万文本中的出现次数，默认平滑次数为 1。',
    'chinese_word_dictionary.txt': '新华词典，词典中包含 20 万余词汇，分别包括词汇和释义',
    'landline_phone_area_code.txt': '固定电话区号对照表，用于定位区号的归属地',
    'negative_words.txt': '常用否定词汇词典',
    'phone_location.txt': '电话号码归属地词典',
    'phrase_pinyin.txt': '包含多音字的词汇和短语的注音词典',
    'pornography.txt': '色情词典',
    'sentiment_expand_words.txt': '情感词分析中，情感扩张性副词',
    'sentiment_words.txt': '情感分析中，情感词及其权重',
    'sim2tra_word.txt': '简体转繁体字的港台和大陆用语转换词典',
    'sim2tra_char.txt': '简体转繁体字映射词典',
    'stopwords.txt': '停用词词典',
    'telecom_operator.txt': '手机电信运营商归属地词典',
    'tra2sim_word.txt': '繁体转简体字的港台和大陆用语转换词典',
    'tra2sim_char.txt': '繁体转简体映射词典',
    'word_distribution.json': '统计中文文本全量语料中，jieba 分词后的词频统计，删除了概率低于1e-6的中文分词结果，与低于1e-5的非中文内容',
    'world_location.txt': '世界地名词典，包括洲、国家两级，国家名下包括国家全名、首都（首府）、主要城市（不完全）等信息。',
    'xiehouyu.txt': '对网络上搜集的歇后语做汇总，质量较高，几乎无错漏；共计 17000 多条。其中',
}

