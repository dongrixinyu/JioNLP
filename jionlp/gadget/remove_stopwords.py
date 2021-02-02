# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
TODO:
    1、常用的分词器有 jieba、清华 thuseg、北大 pkuseg 等。
    2、在时间的过滤中，主要使用规则过滤，jieba 常常将 “2017年” 拆分开，
       而北大分词器则作为整体返回，因此，需要在后续中，增加对“2017”, “年”
       类时间的过滤。

       rule:
       1. 时间格式仅用于滤除具体确切的时间点和时间段，如“2019年6月30日”，
          “第一季度”，“18:30:51”，“3~4月份”，“清晨”，“年前” 等等，此类词
          汇描述了具体的时间，在语言中一般作为时间状语存在，因此在停用词滤
          除中，需要将该部分词汇滤除。
       2. 但不滤除模糊的时间范围，如“三十年”，“六七个月”，“十周”，“四日”
          等等，这些时间描述了一个模糊的时间段，并没有确切的指代，在语言中
          一般做宾语，补语，主语，因此在停用词滤除中，一般不将此类词汇滤除。
       3. 有些词汇含义指代不明，如“三十一日”，具体指某月 31日，还是31天的
          时间，并不确切，此时不予滤除。
       4. 节日名称不予滤除，如“圣诞节”、“除夕夜”，尽管其指示具体的时间点，
          但是一般做名词性成分，因此不予滤除。

    3、地名使用词典过滤，主要是中国省市县三级以及国外主要国家首都城市，因此
       大量的地名无法被过滤，主要包括国内乡镇、村、山川、省市简称、道路、
       新区、桥梁、地标、楼房小区、海洋（海峡、海沟）、区域（华北、南疆）、
       地形（盆地、沙漠）。这些均有待使用地名词典过滤。

       rule:
       1. 地名既可以做位置状语，也可以做名词性成分，因此其过滤需要大而全。
          首先根据工具内词典将匹配的地名识别出来，并做过滤。
       2. 然后，使用正则对剩余不在词典中的地名做匹配过滤。存在误差，如“窗
          含西岭”，“锦荣家园城”，“万国”由于尾字匹配而导致错误。

    4、数字滤除使用正则匹配。数字主要以 “数词 + 量词” 的形式出现，但该工具
       目前并未考虑量词的情况。

       rule:
       1. 融合了百分比，千分比，万分比，十分比格式、序数词，形容词如 “数千
          万、三千余”，负数，数字范围如 “2000~5000”等，还差分数表示未添加，
          如 “三十分之一”。

"""
import os
import re
import pdb
import typing

from jionlp.dictionary.dictionary_loader import stopwords_loader, world_location_loader, china_location_loader, negative_words_loader
from jionlp.rule.rule_pattern import TIME_PATTERN, NUMBER_PATTERN, CHINESE_CHAR_PATTERN, LOCATION_PATTERN


class RemoveStopwords(object):
    """ 给出分词之后的结果，做判定，其中分词器使用用户自定义的，推荐的有
    jieba 分词器、清华分词器 thuseg、北大分词器 pkuseg。
    该方法处理速度较快，但由于大量的中文词汇包含多义，如“本”字包含名词、
    代词、连词等词性，因此准确性较差。是词性标注的简易替代品。

    Args:
        text_segs: 分词之后的列表
        remove_time: 是否去除时间词汇
        remove_location: 是否去除地名词汇
        remove_number: 是否去除纯数字词汇
        remove_non_chinese: 是否去除非中文词汇
        save_negative_words: 保留否定词，如“未”、“没有”、“不”等

    Return:
        list(str)

    """
    def __init__(self):
        self.stopwords_list = None

    def _prepare(self):
        self.stopwords_list = stopwords_loader()
        self.world_list = self._prepare_china_locations()
        self.china_list = self._prepare_world_locations()
        self.location_list = list(set(self.world_list + self.china_list))
        self.negative_words_list = negative_words_loader()
        
        self.time_pattern = re.compile(TIME_PATTERN)
        self.location_pattern = re.compile(LOCATION_PATTERN)
        self.number_pattern = re.compile(NUMBER_PATTERN)
        self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)

    @staticmethod
    def _prepare_world_locations():
        world_location = world_location_loader()
        world_list = list()
        world_list.extend(list(world_location.keys()))
        for continent, countries in world_location.items():
            world_list.extend(list(countries.keys()))
            for country, info in countries.items():
                if 'main_city' in info:
                    world_list.extend(info['main_city'])
                world_list.append(info['full_name'])
                world_list.append(info['capital'])

        return world_list

    @staticmethod
    def _prepare_china_locations():
        china_location = china_location_loader()
        china_list = list()
        china_list.extend(list(china_location.keys()))
        for prov, cities in china_location.items():
            china_list.append(prov)
            china_list.append(cities['_full_name'])
            china_list.append(cities['_alias'])
            for city, counties in cities.items():
                if city.startswith('_'):
                    continue
                china_list.append(city)
                china_list.append(counties['_full_name'])
                china_list.append(counties['_alias'])
                for county, info in counties.items():
                    if county.startswith('_'):
                        continue
                    china_list.append(county)
                    china_list.append(info['_full_name'])
                    china_list.append(info['_alias'])
                    
        return china_list
        
    def __call__(self, text_segs, remove_time=False, 
                 remove_location=False, remove_number=False,
                 remove_non_chinese=False,
                 save_negative_words=False):

        if self.stopwords_list is None:
            self._prepare()
        
        res_text_segs = list()
        for word in text_segs:
            # rule0: 空字符串过滤
            if word == '':
                continue
                
            # rule1: 采用停用词典过滤
            if word in self.stopwords_list:
                # rule6: 保留停用词词典里的否定词
                if save_negative_words:
                    if word in self.negative_words_list:
                        pass
                    else:
                        continue
                else:
                    continue
            
            word_length = len(word)
            # rule2: 采用时间正则过滤
            if remove_time:
                res = self.time_pattern.search(word)
                if res is not None:
                    if res.span()[1] - res.span()[0] == word_length:
                        continue
            
            # rule3: 采用地名词典与正则过滤
            if remove_location:
                if word in self.location_list:
                    continue
                    
                res = self.location_pattern.search(word)
                if res is not None:
                    if res.span()[1] - res.span()[0] == word_length:
                        continue
            
            # rule4: 采用数字正则过滤纯数字
            if remove_number:
                res = self.number_pattern.search(word)
                if res is not None:
                    if res.span()[1] - res.span()[0] == word_length:
                        continue
            
            # rule5: 采用中文正则过滤非中文词汇
            if remove_non_chinese:
                res = self.chinese_char_pattern.search(word)
                if res is None:
                    continue
            
            res_text_segs.append(word)
            
        return res_text_segs
