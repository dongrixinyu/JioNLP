# -*- coding=utf-8 -*-
# 给定一篇文本，确定其归属地


import os
import pdb
import copy
import collections

import thulac

from location_parser import LocationParser
from split_sentence import SplitSentence
from jionlp.dictionary.dictionary_loader import china_location_loader
from jionlp.dictionary.dictionary_loader import world_location_loader


class LocationRecognizer(object):
    def __init__(self):
        self.location_parser_obj = None
        
    def _prepare(self):
        self.location_parser_obj = LocationParser()
        self.split_sentence_obj = SplitSentence()
        self.thuseg = thulac.thulac()
        #self.municipalities_cities = ['北京', '上海', '天津', '重庆', '香港', '澳门']
        china_loc = china_location_loader()
        self._mapping(china_loc)
        
    def _mapping_china_location(self, china_loc):
        # 整理行政区划码映射表
        self.administrative_map_list = list()  # 地址别称
        
        for prov in china_loc:
            if prov.startswith('_'):
                continue
                
            self.administrative_map_list.append(
                [china_loc[prov]['_admin_code'], 
                 [prov, china_loc[prov]['_alias']],
                 [None, None],
                 [None, None]])
            for city in china_loc[prov]:
                if city.startswith('_'):
                    continue
                    
                self.administrative_map_list.append(
                    [china_loc[prov][city]['_admin_code'], 
                     [prov, china_loc[prov]['_alias']],
                     [city, china_loc[prov][city]['_alias']],
                     [None, None]])
                for county in china_loc[prov][city]:
                    if county.startswith('_'):
                        continue
                        
                    self.administrative_map_list.append(
                        [china_loc[prov][city][county]['_admin_code'], 
                         [prov, china_loc[prov]['_alias']],
                         [city, china_loc[prov][city]['_alias']],
                         [county, china_loc[prov][city][county]['_alias']]])
    
    def _mapping_world_location(self, world_loc):
        # 整理国外行政区划映射表
        
        
        
        
    def get_candidates(self, location):
        ''' 从地址中获取所有可能涉及到的候选地址 '''
        
        if self.administrative_map_list is None:
            self._prepare()
        
        candidate_admin_list = list()  # 候选列表 
        for admin_item in self.administrative_map_list:
            count = 0
            # offset 中的每一个元素，分别指示省、市、县三级
            # 其中每个元素的两个整数，指示在地址中的索引，以及是否全名或别名
            offset_list = [-1, -1, -1]
            for idx, name_item in enumerate(admin_item[1:]):
                match_flag = False
                cur_name = None
                cur_alias = None
                for alias_idx, name in enumerate(name_item):  # 别名与全名任意匹配一个
                    if name is not None and name in location:
                        match_flag = True
                        cur_name = name
                        cur_alias = alias_idx
                        break
                if match_flag:
                    count += 1
                    offset_list[idx] = cur_alias
            
            if count > 0:
                cur_item = copy.deepcopy(admin_item)
                cur_item.extend([count, offset_list])
                candidate_admin_list.append(cur_item)
                
        return candidate_admin_list
    
    def __call__(self, text):
        ''' 地域识别，识别出一篇文本中主要涉及的地址，即返回一篇文本的归属地，
        返回的结果具体到地级市，国外具体到城市 
        具体假设为，每一个句子仅识别一个地址，然后统计所有的结果
        
        计算方法：
        1、按句子的粗粒度分句；
        2、对每一个句子做分词与词性标注（默认使用清华工具 thulac），找出其中地名词汇；
        3、对所有地名词汇进行合并，如“西藏”和“拉萨”，同属于一个地址，则进行合并,成为“{
           '省': '西藏', '市': '拉萨', '县': None}”
        4、
        
        Args:
            text(str): 输入的文本，一般是网络新闻文本
            
        Returns:
            dict: 地名结果，包含若干字段，见如下示例。地名分为国内和国外两部分，其中国内
                按照省、市、县，国外按照国家、市的结构进行返回。每个分别默认返回最佳的结
                果。如两个国家城市具有同样的权重，则同时返回。返回数量可以使用参数调节。
                除此之外，仍有一些地名无法用地名行政区划进行匹配，则在 Addition 字段进
                行返回。
            
        Examples:
            >>> text = '成都市召开了中日韩三国峰会，中国、日本、韩国三国首脑，日本东京和
                尚家村缔结了互帮互助...'
            >>> print(jio.location_recognizer(text))
            {
                'domestic': [
                    {
                        'province': '四川省',
                        'city': '成都市',
                        'county': None
                    }
                ],
                'foreign': [
                    {
                        'country': '日本',
                        'city': '东京'
                    },
                    {
                        'country': '韩国',
                        'city': None
                    }
                ],
                'addition': [
                    '尚家村'
                ]
            }
        
        '''
        if self.location_parser_obj is None:
            self._prepare()
        
        text_pos_seg = self.thuseg.cut(text)
        text_location = [item[0] for item in text_pos_seg if item[1] == 'ns']
        if len(text_location) == 0:
            return
        
        location_count = dict(collections.Counter(text_location).most_common())
        print(location_count)
        
        # 此时，未知 斯里兰卡 和 科伦坡是对应的国家和首都关系，需要进行关联
        for location in location_count:
            
            cur_candidates_list = self.get_candidates(location)
            print(cur_candidates_list)
            
        #if len(candidates_admin_list) == 0:
        #    return

        
        
        
        
        
        
        
        
        pdb.set_trace()
        sen_list = self.split_sentence_obj(text, criterion='coarse')
        

        #count_dict = dict()
        #for location in text_location:
        for sen in sen_list:
            print('# ', sen)
            # 分词、词性标注，获取地名词汇
            sen_pos_seg = self.thuseg.cut(sen)
            sen_location = [item[0] for item in sen_pos_seg if item[1] == 'ns']
            if len(sen_location) == 0:
                continue
            
            
            candidates_admin_list = self.get_candidates(sen_location)
            if len(candidates_admin_list) == 0:
                continue
                
            print(sen_location)
            for i in candidates_admin_list:
                print(i)
            pdb.set_trace()
            
            print('\n')
            #print(sen)
            if len(sen_location) > 1:
                print(sen)
                print(sen_location)

            pdb.set_trace()
        return

        candidates = self.location_parser_obj.get_candidates(sen_location)
        organize_candidates = list()

        for item in candidates:
            not_match_flag = 2  # 指地址的细节，如市、县，哪一个没有在文本中匹配到。
            #print(item[-1])
            for idx, offset in enumerate(reversed(item[-1])):
                if offset[0] == -1:
                    not_match_flag = 2 - idx - 1
                else:
                    break

            organize_item = [it if idx <= not_match_flag else [None, None] 
                             for idx, it in enumerate(item[1:4])]
            #print(organize_item)
            #print(item)
            #pdb.set_trace()
            if organize_item not in organize_candidates:
                organize_candidates.append(organize_item)
        #print(organize_candidates)    
        print(sen)
        print(sen_location)
        for item in organize_candidates:
            key = json.dumps(item, ensure_ascii=False)
            print(key)
            if key in count_dict:
                count_dict[key] += 1
            else:
                count_dict.update({key: 1})


        pdb.set_trace()
            
        count_dict = sorted(count_dict.items(), key=lambda i: i[1], reverse=True)
        for key, val in count_dict:
            print(key, val)
        #pdb.set_trace()
        
        



if __name__ == '__main__':
    import json
    import random
    
    from jionlp.util.file_io import read_file_by_line
    lr = LocationRecognizer()
    texts = read_file_by_line(
        '/data1/ml/cuichengyu/dataset_store/text_dataset_20190731_guoxinyuqing.txt',
        line_num=1000)
    random.shuffle(texts)
    for text in texts:
        #loc = '喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号'
        #print(''.join(json.loads(text)[0]))
        res = lr(text)
        print(json.dumps(res, ensure_ascii=False, 
                         indent=4, separators=(',', ':')))
        #pdb.set_trace()




















