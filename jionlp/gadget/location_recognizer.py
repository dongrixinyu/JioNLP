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
        
    def _mapping(self, china_loc):
        # 整理行政区划码映射表
        self.administrative_map_list = list()  # 地址别称
        
        for prov in china_loc:
            if not prov.startswith('_'):
                self.administrative_map_list.append(
                    [china_loc[prov]['_admin_code'], 
                     [prov, china_loc[prov]['_alias']],
                     [None, None],
                     [None, None]])
                for city in china_loc[prov]:
                    if not city.startswith('_'):
                        self.administrative_map_list.append(
                            [china_loc[prov][city]['_admin_code'], 
                             [prov, china_loc[prov]['_alias']],
                             [city, china_loc[prov][city]['_alias']],
                             [None, None]])
                        for county in china_loc[prov][city]:
                            if not county.startswith('_'):
                                self.administrative_map_list.append(
                                    [china_loc[prov][city][county]['_admin_code'], 
                                     [prov, china_loc[prov]['_alias']],
                                     [city, china_loc[prov][city]['_alias']],
                                     [county, china_loc[prov][city][county]['_alias']]])
                                
    def get_candidates(self, location_list):
        ''' 从地址中获取所有可能涉及到的候选地址 '''
        
        if self.administrative_map_list is None:
            self._prepare()
        
        candidate_admin_list = list()  # 候选列表 
        for admin_item in self.administrative_map_list:
            count = 0
            # offset 中的每一个元素，分别指示在地址中的索引，以及全名或别名
            offset_list = [[-1, -1], [-1, -1], [-1, -1]]  
            for idx, name_item in enumerate(admin_item[1:]):
                match_flag = False
                cur_name = None
                cur_alias = None
                for alias_idx, name in enumerate(name_item):  # 别名与全名任意匹配一个
                    if name is not None and name in location_list:
                        match_flag = True
                        cur_name = name
                        cur_alias = alias_idx
                        break
                if match_flag:
                    count += 1
                    offset_list[idx][0] = location_list.index(cur_name)
                    offset_list[idx][1] = cur_alias
            
            if count > 0:
                cur_item = copy.deepcopy(admin_item)
                cur_item.extend([count, offset_list])
                candidate_admin_list.append(cur_item)
                
        return candidate_admin_list
    
    def __call__(self, text):
        ''' 地域识别，识别出一篇文本中主要涉及的地址，即返回一篇文本的归属地，
        返回的结果具体到地级市，国外具体到城市 
        具体假设为，每一个句子仅识别一个地址，然后统计所有的结果
        '''
        if self.location_parser_obj is None:
            self._prepare()
        
        sen_list = self.split_sentence_obj(text)
        

        #count_dict = dict()
        #for location in text_location:
        for sen in sen_list:
            
            # 仅获取地名
            sen_pos_seg = self.thuseg.cut(sen)
            sen_location = [item[0] for item in sen_pos_seg if item[1] == 'ns']
            if len(sen_location) == 0:
                continue
                
            candidates_admin_list = self.get_candidates(sen_location)
            if len(candidates_admin_list) == 0:
                continue
                
            #for i in candidates_admin_list:
            #    print(i)
            
            #print('\n')
            #print(sen)
            if len(sen_location) > 1:
                print(sen)
                print(sen_location)

            #pdb.set_trace()
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
    lr = LocationRecognizer()
    with open('/data1/ml/cuichengyu/new_ner/ner_data/boson_20200331.txt', 
              'r', encoding='utf-8') as fr:
        texts = fr.readlines()
        
    for text in texts:
        #loc = '喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号'
        #print(''.join(json.loads(text)[0]))
        res = lr(''.join(json.loads(text)[0]))
        #print(json.dumps(res, ensure_ascii=False, 
        #                 indent=4, separators=(',', ':')))
        #pdb.set_trace()




















