# -*- coding=utf-8 -*-
'''
TODO:
    1、常用的分词器有 jieba、清华 thuseg、北大 pkuseg 等。
    2、在时间的过滤中，主要使用规则过滤，jieba 常常将 “2017年” 拆分开，
       而北大分词器则作为整体返回，因此，需要在后续中，增加对“2017”, “年” 
       类时间的过滤。
    3、地名使用词典过滤，主要是中国省市县三级以及国外主要国家首都城市，因此
       大量的地名无法被过滤，主要包括国内乡镇、村、山川、省市简称、道路、
       新区、桥梁、地标、楼房小区、海洋（海峡、海沟）、区域（华北、南疆）、
       地形（盆地、沙漠）。这些均有待使用地名词典过滤。
       
'''
import os
import re
import pdb
import typing

from jionlp.dictionary.dictionary_loader import stopwords_loader, world_location_loader, china_location_loader
from jionlp.rule.rule_pattern import TIME_PATTERN


class RemoveStopwords(object):
    def __init__(self):
        self.stopwords_list = None

    def _prepare(self):
        self.stopwords_list = stopwords_loader()
        self.world_list = self._prepare_china_locations()
        self.china_list = self._prepare_world_locations()
        self.location_list = list(set(self.world_list + self.china_list))
        #pdb.set_trace()
        self.time_pattern = re.compile(TIME_PATTERN)
        
    def _prepare_world_locations(self):
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
        #pdb.set_trace()
        return world_list
        
    def _prepare_china_locations(self):
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
                 remove_location=False):
        ''' 给出分词之后的结果，做判定，其中分词器使用用户自定义的，推荐的有
        jieba 分词器、清华分词器 thuseg、北大分词器 pkuseg。
        
        Args:
            list(str): 分词之后的列表
            remove_time: 是否去除时间词汇
            remove_location: 是否去除地名词汇
        
        Return:
            list(str)
        
        '''
        if self.stopwords_list is None:
            self._prepare()
        
        res_text_segs = list()
        for word in text_segs:
            # rule0: 空字符串过滤
            if word == '':
                continue
                
            # rule1: 采用停用词典过滤
            if word in self.stopwords_list:
                continue
                
            # rule2: 采用时间正则过滤
            if remove_time:
                res = self.time_pattern.search(word)
                if res is not None:
                    continue
            
            # rule3: 采用地名词典过滤
            if remove_location:
                if word in self.location_list:
                    continue
            res_text_segs.append(word)
            
        return res_text_segs
        


