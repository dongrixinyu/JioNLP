# -*- coding=utf-8 -*-

import os
import pdb

from jionlp import logging
from jionlp.util.file_io import read_file_by_line


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
GRAND_DIR_PATH = os.path.dirname(DIR_PATH)


__all__ = ['china_location_loader', 'world_location_loader',
           'stopwords_loader', 'chinese_idiom_loader', 
           'pinyin_phrase_loader', 'pinyin_char_loader',
           'xiehouyu_loader', 'chinese_char_dictionary_loader',
           'chinese_word_dictionary_loader',
           'pornography_loader', 'traditional_simplified_loader']


def china_location_loader():
    ''' 加载中国地名词典 china_location.txt '''
    location_jio = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/china_location.txt'), 
        strip=False)
    
    cur_province = None
    cur_city = None
    cur_county = None
    location_dict = dict()

    for item in location_jio:
        if not item.startswith('\t'):  # 省
            if len(item.strip().split('\t')) != 3:
                continue
            province, admin_code, alias_name = item.strip().split('\t')
            cur_province = province
            location_dict.update(
                {cur_province: {'_full_name': province,
                                '_alias': alias_name,
                                '_admin_code': admin_code}})

        elif item.startswith('\t\t'):  # 县
            if len(item.strip().split('\t')) != 3:
                continue
            county, admin_code, alias_name = item.strip().split('\t')
            cur_county = county
            location_dict[cur_province][cur_city].update(
                {cur_county: {'_full_name': county,
                              '_alias': alias_name,
                              '_admin_code': admin_code}})

        else:  # 市
            if len(item.strip().split('\t')) != 3:
                continue
            city, admin_code, alias_name = item.strip().split('\t')
            cur_city = city
            location_dict[cur_province].update(
                {cur_city: {'_full_name': city,
                            '_alias': alias_name,
                            '_admin_code': admin_code}})

    return location_dict


def world_location_loader():
    ''' 加载世界地名词典 world_location.txt '''
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/world_location.txt'))
    
    result = dict()
    cur_continent = None
    
    for line in content:
        if '洲:' in line:
            cur_continent = line.replace(':', '')
            result.update({cur_continent: dict()})
            continue
        
        item_tup = line.split('\t')
        item_length = len(item_tup)
        if item_length == 3:
            result[cur_continent].update(
                {item_tup[0]: {'full_name': item_tup[1], 
                               'capital': item_tup[2]}})
        
        if item_length == 4:
            result[cur_continent].update(
                {item_tup[0]: {'full_name': item_tup[1], 
                               'capital': item_tup[2], 
                               'main_city': item_tup[3].split('/')}})
        else:
            pass
        
    return result
    
    
def stopwords_loader():
    ''' 加载停用词典 stopwords.txt '''
    res = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary/stopwords.txt'))
    # 一般漏掉了若干转换符号
    res.extend(['', ' ', '\t'])
    return res


def negative_words_loader():
    ''' 加载否定词典 negative_words.txt '''
    res = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary/negative_words.txt'))
    
    return res


def chinese_char_dictionary_loader():
    ''' 加载新华字典，分别包括：
    汉字，释义，详细释义 3 部分
    '''
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary',
                     'chinese_char_dictionary.txt'), strip=False)
    
    char_dict = dict()
    for line in content:
        segs = line.split('\t')
        
        assert len(segs) == 3
        char_dict.update({
            segs[0]: {'explanation': segs[1],
                      'more_details': segs[2].replace('\n', '')
                      if segs[2] != '\n' else None}})
        
    return char_dict
    
    
def chinese_idiom_loader():
    ''' 加载成语词典 chinese_idiom.txt '''
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/chinese_idiom.txt'))
    
    result = dict()
    cur_item = dict()
    import json
    for line in content:
        item_tup = line.split('\t')
        
        assert len(item_tup) == 5
        example = item_tup[3] if item_tup[3] != '' else None
        cur_item = {'explanation': item_tup[1],
                    'derivation': item_tup[2],
                    'example': example,
                    'freq': int(item_tup[4])}
        result.update({item_tup[0]: cur_item})
    
    return result
    
    
def chinese_word_dictionary_loader():
    ''' 加载新华词典，词典中有 20 万余个多音字，分别包括：
    词语及其释义
    '''
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary',
                     'chinese_word_dictionary.txt'))
    
    word_dict = dict()
    for idx, line in enumerate(content):
        segs = line.split('\t')
        assert len(segs) == 2
        word_dict.update({segs[0]: segs[1]})
        
    return word_dict
    

def pornography_loader():
    ''' 加载淫秽色情词典 pornography.txt '''
    return read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary/pornography.txt'))
    
    
def char_radical_loader():
    ''' 加载汉字字形词典 char_radical.txt '''
    structure_dict = {
        0: '一体结构', 1: '左右结构', 2: '上下结构', 3: '左中右结构',
        4: '上中下结构', 5: '右上包围结构', 6: '左上包围结构', 7: '左下包围结构',
        8: '全包围结构', 9: '半包围结构'}
    
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'char_radical.txt'))
    
    map_dict = dict()
    for item in content:
        assert len(item.split('\t')) == 5
        char, radical, structure, four_corner, components = item.split('\t')
        map_dict.update({char: [radical, int(structure),
                                four_corner, components]})
        
    return map_dict, structure_dict
    
    
    
    
def traditional_simplified_loader(file_name):
    ''' 加载繁简体转换词典 '''
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', file_name))
    
    map_dict = dict()
    for item in content:
        key, value = item.split('\t')
        map_dict.update({key: value})
    return map_dict
    
    
def pinyin_phrase_loader():
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'pinyin_phrase.txt'))
    
    map_dict = dict()
    for item in content:
        key, value = item.split('\t')
        value = value.split('/')
        map_dict.update({key: value})
        
    return map_dict


def pinyin_char_loader():
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'pinyin_char.txt'))
    
    map_dict = dict()
    for item in content:
        key, value = item.split('\t')
        assert len(item.split('\t')) == 2
        
        multi_pinyin = value.split('/')
        map_dict.update({key: multi_pinyin})

    return map_dict
    

def xiehouyu_loader():
    ''' 加载歇后语词典，共计 17000 余条，其中有相似的歇后语，如：
    一个模子出来的  一个样
    一个模子出来的  一模一样
    对于此类歇后语，均按不同的表达分为不同的歇后语，方便检索查询
    '''
    xiehouyu = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'xiehouyu.txt'))
    
    xiehouyu = list(set(xiehouyu))
    xiehouyu = [item.split('\t') for item in xiehouyu]

    return xiehouyu




















