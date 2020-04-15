# -*- coding=utf-8 -*-

import os
import re
import pdb
import copy
import collections

from jionlp.dictionary.dictionary_loader import china_location_loader


class LocationParser(object):
    ''' 将地址解析出来 '''
    def __init__(self):
        self.administrative_map_list = None
        
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
        
    def _prepare(self):
        # 添加中国区划词典
        china_loc = china_location_loader()
        self._mapping(china_loc)
        
        self.loc_level_key_list = ['省', '市', '县']
        self.loc_level_key_dict = dict(
            [(loc_level, None) for loc_level in self.loc_level_key_list])
        self.municipalities_cities = ['北京', '上海', '天津', '重庆', '香港', '澳门']
        
    def get_candidates(self, location_text):
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
                    if name is not None and name in location_text:
                        match_flag = True
                        cur_name = name
                        cur_alias = alias_idx
                        break
                if match_flag:
                    count += 1
                    offset_list[idx][0] = location_text.index(cur_name)
                    offset_list[idx][1] = cur_alias
            
            if count > 0:
                cur_item = copy.deepcopy(admin_item)
                cur_item.extend([count, offset_list])
                candidate_admin_list.append(cur_item)
                
        return candidate_admin_list
        
    def __call__(self, location_text):
        ''' 将地址解析出来，成若干段，其中，省市县的准确度高，而道路等详细字段准确度低 '''
        if self.administrative_map_list is None:
            self._prepare()
        
        # 获取文本中的省、市、县三级行政区划
        # rule: 命中匹配别名或全名，统计命中量，并假设省市县分别位于靠前的位置且依次排开
        candidate_admin_list = self.get_candidates(location_text)
        
        if len(candidate_admin_list) == 0:
            return {'province': None, 
                    'city': None,
                    'county': None,
                    'detail': location_text,
                    'full_location': location_text,
                    'orig_location': location_text}
            
        # 寻找匹配最多的候选地址，然后寻找匹配最靠前的候选地址，作为最终的省市县的判断结果
        candidate_admin_list = sorted(
            candidate_admin_list, key=lambda i:i[-2], reverse=True)
        max_matched_num = candidate_admin_list[0][-2]
        candidate_admin_list = [item for item in candidate_admin_list
                                if item[-2] == max_matched_num]
        candidate_admin_list = sorted(
            candidate_admin_list, key=lambda i:sum([j[0] for j in i[-1]]))
        
        min_matched_offset = sum([j[0] for j in candidate_admin_list[0][-1]])
        candidate_admin_list = [item for item in candidate_admin_list 
                                if sum([j[0] for j in item[-1]]) == min_matched_offset]
        
        # rule: 县级存在重复名称，计算可能重复的县名
        county_dup1_list = [item[3][0] for item in candidate_admin_list]
        county_dup2_list = [item[3][1] for item in candidate_admin_list]
        county_dup_list = county_dup1_list + county_dup2_list
        county_dup_list = collections.Counter(county_dup_list).most_common()
        county_dup_list = [item[0] for item in county_dup_list if item[1] > 1]
        
        final_admin = candidate_admin_list[0]  # 是所求结果
        
        # 确定详细地址部分
        # rule: 根据已有的省市县，确定剩余部分为详细地址
        detail_idx = 0
        
        final_prov = None
        final_city = None
        final_county = None
        for admin_idx, i in enumerate(final_admin[-1]):
            if i[0] != -1:
                detail_idx = i[0] + len(final_admin[admin_idx + 1][i[1]])
                
                # rule: 全国地址省市无重复命名，而县级有，如鼓楼区、高新区等
                if admin_idx >= 0 and final_admin[admin_idx + 1][i[1]] not in county_dup_list:
                    final_prov = final_admin[1][0]
                if admin_idx >= 1 and final_admin[admin_idx + 1][i[1]] not in county_dup_list:
                    final_city = final_admin[2][0]
                if admin_idx >= 2 and final_admin[admin_idx + 1][i[1]] not in county_dup_list:
                    final_county = final_admin[3][0]
                else:
                    final_county = final_admin[3][i[1]]

        # 获取详细地址部分
        detail_part = location_text[detail_idx:]
        
        # 获取省市区行政区划部分
        admin_part = ''
        if final_prov is not None:
            admin_part = final_prov
        if final_city is not None:
            match_muni_flag = False
            for muni_city in self.municipalities_cities:
                if muni_city in final_city:
                    match_muni_flag = True
                    break
            if not match_muni_flag:
                admin_part += final_city
        if final_county is not None:
            admin_part += final_county
        
        return {'province': final_prov, 
                'city': final_city,
                'county': final_county,
                'detail': detail_part,
                'full_location': admin_part + detail_part,
                'orig_location': location_text}
        

if __name__ == '__main__':
    import json
    lp = LocationParser()
    with open('/data1/ml/cuichengyu/hainan_project/address1.txt', 
              'r', encoding='utf-8') as fr:
        addresses = fr.readlines()
        
    for loc in addresses:
        #loc = '喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号'
        res = lp(loc)
        print(json.dumps(res, ensure_ascii=False, 
                         indent=4, separators=(',', ':')))
        pdb.set_trace()


