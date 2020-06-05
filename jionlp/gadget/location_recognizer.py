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
        world_loc = world_location_loader()
        self._mapping_china_location(china_loc)
        self._mapping_world_location(world_loc)
        
    def _mapping_china_location(self, china_loc):
        # 整理行政区划码映射表
        self.china_administrative_map_list = list()  # 地址别称
        
        for prov in china_loc:
            if prov.startswith('_'):
                continue
                
            self.china_administrative_map_list.append(
                [[prov, china_loc[prov]['_alias']],
                 [None, None],
                 [None, None]])
            for city in china_loc[prov]:
                if city.startswith('_'):
                    continue
                    
                self.china_administrative_map_list.append(
                    [[prov, china_loc[prov]['_alias']],
                     [city, china_loc[prov][city]['_alias']],
                     [None, None]])
                for county in china_loc[prov][city]:
                    if county.startswith('_'):
                        continue
                        
                    self.china_administrative_map_list.append(
                        [[prov, china_loc[prov]['_alias']],
                         [city, china_loc[prov][city]['_alias']],
                         [county, china_loc[prov][city][county]['_alias']]])
    
    def _mapping_world_location(self, world_loc):
        # 整理国外行政区划映射表
        world_administrative_map_list = list()
        for continent in world_loc:
            for country in world_loc[continent]:
                #print(country)
                #if country == '中国':
                #    continue
                
                cities = [world_loc[continent][country]['capital']]
                if 'main_city' in world_loc[continent][country]:
                    cities.extend(world_loc[continent][country]['main_city'])
                world_administrative_map_list.append(
                    [[country, world_loc[continent][country]['full_name']],
                     None])
                for city in cities:
                    world_administrative_map_list.append(
                        [[country, world_loc[continent][country]['full_name']],
                         city])
                    
        self.world_administrative_map_list = world_administrative_map_list
        
    def get_china_candidates(self, location):
        ''' 从地址中获取所有可能涉及到的候选地址 '''
        
        if self.china_administrative_map_list is None:
            self._prepare()
        
        candidate_admin_list = list()  # 候选列表 
        for admin_item in self.china_administrative_map_list:
            count = 0
            # offset 中的每一个元素，分别指示省、市、县三级是否被匹配
            offset_list = [-1, -1, -1]
            for idx, name_item in enumerate(admin_item):
                match_flag = False
                for alias_idx, name in enumerate(name_item):  # 别名与全名任意匹配一个
                    if name is not None and name in location:
                        match_flag = True
                        break
                if match_flag:
                    count += 1
                    offset_list[idx] = 1
            
            if count > 0:
                cur_item = copy.deepcopy(admin_item)
                cur_item.extend([offset_list])
                candidate_admin_list.append(cur_item)
                
        return candidate_admin_list
    
    def get_world_candidates(self, location):
        ''' 给定一个地址字符串，找出其中 '''
        if self.world_administrative_map_list is None:
            self._prepare()
            
        candidate_admin_list = list()  # 候选列表 
        for admin_item in self.world_administrative_map_list:
            count = 0
            # offset 中的每一个元素，分别指示国家、城市两级
            offset_list = [-1, -1]
            for idx, name_item in enumerate(admin_item):
                match_flag = False
                if idx == 0:  # 国家名
                    for name in name_item:  # 别名与全名任意匹配一个
                        if name is not None and name in location:
                            match_flag = True
                            break
                elif idx == 1:  # 城市名
                    if name_item is not None and name_item in location:
                        match_flag = True
                else:
                    raise ValueError
                
                if match_flag:
                    count += 1
                    offset_list[idx] = 1
            
            if count > 0:
                cur_item = copy.deepcopy(admin_item)
                cur_item.extend([offset_list])
                candidate_admin_list.append(cur_item)
                
        return candidate_admin_list
        
    def _choose_best_china_location(self, china_candidates):
        ''' 给定针对一个地名字符串的候选地名，选择最优的国内地名 '''
        if len(china_candidates) == 0:
            return {'province': None,
                    'city': None,
                    'county': None}
        if len(china_candidates) == 1:
            
            res = {'province': china_candidates[0][0][0],
                   'city': china_candidates[0][1][0],
                   'county': china_candidates[0][2][0]}
            return res
        else:
            province = list(set([item[0][0] for item in china_candidates if item[-1][0] == 1]))
            city = list(set([item[1][0] for item in china_candidates if item[-1][1] == 1]))
            county = list(set([item[2][0] for item in china_candidates if item[-1][2] == 1]))
            # for item in 
            res = {'province': province[0] if len(province) == 1 else None,
                   'city': city[0] if len(city) == 1 else None,
                   'county': county[0] if len(county) == 1 else None}
            return res
        
    def _choose_best_world_location(self, world_candidates):
        ''' 给定针对一个地名字符串的候选地名，选择最优的国外地名 '''
        if len(world_candidates) == 1:
            res = {'country': world_candidates[0][0][0],
                   'city': world_candidates[0][1]}
            return res
        else:
            country = list(set([item[0][0] for item in world_candidates if item[-1][0] == 1]))
            city = list(set([item[1][0] for item in world_candidates if item[-1][1] == 1]))
             
            res = {'country': country[0] if len(country) == 1 else None,
                   'city': city[0] if len(city) == 1 else None}
            return res

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
        
        final_res = {'domestic': None, 'foreign': None}
        text_pos_seg = self.thuseg.cut(text)
        text_location = [item[0] for item in text_pos_seg if item[1] == 'ns']
        if len(text_location) == 0:
            return final_res
        
        location_count = dict(collections.Counter(text_location).most_common())
        print(location_count)
        
        #china_tmp_dict = dict()
        # 此时，未知 斯里兰卡 和 科伦坡 是对应的国家和首都关系，需要进行关联
        for location, count in location_count.items():
            china_candidates = self.get_china_candidates(location)
            best_loc = self._choose_best_china_location(china_candidates)
            if len(china_candidates) > 0:
                #print(china_candidates)
                print(best_loc)
                pdb.set_trace()
            
        
        
        #world_tmp_dict = dict()
        # 此时，未知 斯里兰卡 和 科伦坡是对应的国家和首都关系，需要进行关联
        for location, count in location_count.items():
            world_candidates = self.get_world_candidates(location)
            best_loc = self._choose_best_world_location(world_candidates)
            if len(world_candidates) > 0:
                #print(world_candidates)
                print(best_loc)
                pdb.set_trace()
            
            
        # 汇总所有的地址，合并 
                    
        #if len(candidates_admin_list) == 0:
        #    return

        
        
        
        
        
        
        
        
        
        pdb.set_trace()
        return
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




















