# -*- coding=utf-8 -*-

import os

from bbd_nlp_apis.gadget.file_io import read_file_by_line


DIR_PATH = os.path.dirname(os.path.abspath(__file__))


def china_location_loader():
    ''' 加载中国地名词典 china_location.txt '''
    
    


def world_location_loader():
    ''' 加载世界地名词典 world_location.txt '''
    content = read_file_by_line(
        os.path.join(DIR_PATH, 'world_location.txt'))
    
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
    return read_file_by_line(os.path.join(DIR_PATH, 'stopwords.txt'))
    
    
def chinese_idiom_loader():
    ''' 加载成语词典 chinese_idiom.txt '''
    content = read_file_by_line(
        os.path.join(DIR_PATH, 'chinese_idiom.txt'))
    
    result = dict()
    for line in content:
        item_tup = line.split('\t')
        result.update({item_tup[0]: int(item_tup[1])})
    return result
    

def pornography_loader():
    ''' 加载淫秽色情词典 pornography.txt '''
    return read_file_by_line(os.path.join(DIR_PATH, 'pornography.txt'))
    
    
    
    
    
    
    
    
    






















