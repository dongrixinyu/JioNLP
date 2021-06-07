# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP

# --------------------------------------------------------------------------------

import copy
import collections

from jionlp.dictionary.dictionary_loader import china_location_loader,\
    china_location_change_loader


class LocationParser(object):
    """ 将给定中国地址字串进行解析出来，抽取或补全地址对应的省、市、县信息，此外还包
    括详细地址、原地址等。其中，省市县的准确度高，而道路等详细字段准确度低，主要应用
    目标文本示例如下：

    1、中国详细地址字符串
        此类字符串一般用于邮寄、地图等。可以根据国内固有的县、市定位出所在市、省。
        e.g. 喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号
        {
            "province":"辽宁省",
            "city":"朝阳市",
            "county":"喀喇沁左翼蒙古族自治县",
            "detail":"旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号",
            "full_location":"辽宁省朝阳市喀喇沁左翼蒙古族自治县旗覃家岗街道梨树湾
                             村芭蕉沟村民小组临.222号",
            "orig_location":"喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号"
        }

    2、一般文本句子字符串
        此类文本自由度很高，可能包含不止一个地址，默认优先选择最靠前的地址进行返回。
        e.g. 成都和西安是西部大开发先锋城市。
        {
            "province":"四川省",
            "city":"成都市",
            "county":null,
            "detail":"和西安是西部大开发先锋城市。",
            "full_location":"四川省成都市和西安是西部大开发先锋城市。",
            "orig_location":"成都和西安是西部大开发先锋城市。"
        }
        此时，detail 等字段作废，没有意义。

    Args:
        location_text(str): 包含地名的字符串，若字符串中无中国地名，则返回结果是
                            无意义的。
        town_village(bool): 若为 True，则返回 省、市、县区、乡镇街道、村社区 五级信息；
                            若为 False，则返回 省、市、县区 三级信息
        change2new(bool): 若为 True，则遇到旧有地名，自动转为当前最新的地址，如黑龙江伊春市美溪区
                          自动转为黑龙江伊春市伊美区；若为 False，则按旧地名返回

    Returns:
        dict[str,]: 字典格式，如上例所示。

    Examples:
        >>> import jionlp as jio
        >>> text = '喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号'
        >>> res = jio.parse_location(text)
        >>> print(res)

    """
    def __init__(self):
        self.administrative_map_list = None
        self.town_village = False
        self.town_village_dict = dict()
        
    def _mapping(self, china_loc, china_change_loc):
        # 整理行政区划码映射表
        self.administrative_map_list = list()  # 地址别称

        for prov in china_loc:
            if prov.startswith('_'):
                continue
            self.administrative_map_list.append(
                [china_loc[prov]['_admin_code'], 
                 [prov, china_loc[prov]['_alias']],
                 [None, None],
                 [None, None], True])  # True 表示数据为最新地名，反之为旧地名
            for city in china_loc[prov]:
                if city.startswith('_'):
                    continue
                self.administrative_map_list.append(
                    [china_loc[prov][city]['_admin_code'], 
                     [prov, china_loc[prov]['_alias']],
                     [city, china_loc[prov][city]['_alias']],
                     [None, None], True])
                for county in china_loc[prov][city]:
                    if county.startswith('_'):
                        continue
                    self.administrative_map_list.append(
                        [china_loc[prov][city][county]['_admin_code'], 
                         [prov, china_loc[prov]['_alias']],
                         [city, china_loc[prov][city]['_alias']],
                         [county, china_loc[prov][city][county]['_alias']],
                         True])

                    if self.town_village:  # 补充 self.town_village_list

                        key_name = prov + city + county
                        value_dict = china_loc[prov][city][county]
                        self.town_village_dict.update({key_name: value_dict})

        # 将旧有的地名融入 self.administrative_map_list，并建立映射表
        self.old2new_loc_map = dict()

        for item in china_change_loc:
            self.administrative_map_list.append(
                ['000000', item['old_loc'][0], item['old_loc'][1],
                 item['old_loc'][2], False])
            self.old2new_loc_map.update(
                {''.join([i[0] for i in item['old_loc']]): item['new_loc']})

    def _prepare(self):
        # 添加中国区划词典
        china_loc = china_location_loader(detail=self.town_village)
        china_change_loc = china_location_change_loader()
        self._mapping(china_loc, china_change_loc)

        self.loc_level_key_list = ['省', '市', '县']
        if self.town_village:
            self.loc_level_key_list.extend(['乡', '村'])
        self.loc_level_key_dict = dict(
            [(loc_level, None) for loc_level in self.loc_level_key_list])
        self.municipalities_cities = ['北京', '上海', '天津', '重庆', '香港', '澳门']
        
    def get_candidates(self, location_text):
        """ 从地址中获取所有可能涉及到的候选地址 """
        
        if self.administrative_map_list is None:
            self._prepare()

        candidate_admin_list = list()  # 候选列表 
        for admin_item in self.administrative_map_list:
            count = 0  # 匹配个数
            # offset 中的每一个元素，分别指示在地址中的索引，以及全名或别名
            offset_list = [[-1, -1], [-1, -1], [-1, -1]]  
            for idx, name_item in enumerate(admin_item[1: -1]):
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

    def __call__(self, location_text, town_village=False, change2new=True):

        self.town_village = town_village
        if self.administrative_map_list is None:
            self._prepare()
        if self.town_village and self.town_village_dict == dict():
            self._prepare()
        
        # 获取文本中的省、市、县三级行政区划
        # step 1: 命中匹配别名或全名，统计命中量，并假设省市县分别位于靠前的位置且依次排开
        candidate_admin_list = self.get_candidates(location_text)

        if len(candidate_admin_list) == 0:
            result = {'province': None,
                      'city': None,
                      'county': None,
                      'detail': location_text,
                      'full_location': location_text,
                      'orig_location': location_text}
            if self.town_village:
                result.update({'town': None, 'village': None})
            return result
            
        # step 2: 寻找匹配最多的候选地址，然后寻找匹配最靠前的候选地址，作为最终的省市县的判断结果
        candidate_admin_list = sorted(
            candidate_admin_list, key=lambda i: i[-2], reverse=True)
        max_matched_num = candidate_admin_list[0][-2]
        candidate_admin_list = [item for item in candidate_admin_list
                                if item[-2] == max_matched_num]
        candidate_admin_list = sorted(
            candidate_admin_list, key=lambda i: sum([j[0] for j in i[-1]]))
        
        min_matched_offset = sum([j[0] for j in candidate_admin_list[0][-1]])
        candidate_admin_list = [item for item in candidate_admin_list 
                                if sum([j[0] for j in item[-1]]) == min_matched_offset]
        
        # step 3: 县级存在重复名称，计算候选列表中可能重复的县名
        county_dup_list = [item[3][item[-1][-1][1]] for item in candidate_admin_list]
        county_dup_list = collections.Counter(county_dup_list).most_common()
        county_dup_list = [item[0] for item in county_dup_list if item[1] > 1]
        
        final_admin = candidate_admin_list[0]  # 是所求结果

        # step 4: 根据已有的省市县，确定剩余部分为详细地址
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

        # step 5: 将旧地址根据映射转换为新地址
        if change2new:
            tmp_key = ''.join([final_prov if final_prov else '',
                               final_city if final_city else '',
                               final_county if final_county else ''])
            if tmp_key in self.old2new_loc_map:
                final_prov, final_city, final_county = self.old2new_loc_map[tmp_key]

        # step 6: 获取详细地址部分
        detail_part = location_text[detail_idx:]
        if detail_part[0] in '县':
            detail_part = detail_part[1:]

        # step 7: 将地址中的 省直辖、市直辖，去掉
        if final_city is not None and '直辖' in final_city:
            final_city = None
        if final_county is not None and '直辖' in final_county:
            final_county = None

        # step 8: 获取省市区行政区划部分
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

        result = {'province': final_prov,
                  'city': final_city,
                  'county': final_county,
                  'detail': detail_part,
                  'full_location': admin_part + detail_part,
                  'orig_location': location_text}

        # step 9: 获取镇、村两级
        if town_village:
            result = self._get_town_village(result)

        return result

    def _get_town_village(self, result):
        # 从后续地址中，获取乡镇和村、社区信息
        town = None
        village = None

        prov = result['province']
        city = result['city'] if result['city'] is not None else '省直辖行政区划'
        county = result['county'] if result['county'] is not None else '市直辖行政区划'
        key_name = ''.join([prov, city, county])

        if key_name not in self.town_village_dict:
            result.update({'town': town, 'village': village})
            return result

        # 确定乡镇
        town_list = list(self.town_village_dict[key_name].keys())
        for _town in town_list:
            if _town in result['detail']:
                town = _town
                break

        # 确定村、社区
        if town is not None:
            village_list = list(self.town_village_dict[key_name][town].keys())
            for _village in village_list:
                if _village in result['detail']:
                    village = _village
                    break

        result.update({'town': town, 'village': village})
        return result


if __name__ == '__main__':
    import json
    
    lp = LocationParser()
    loc = '成都是西部大开发先锋城市。'
    res = lp(loc)
    print(json.dumps(res, ensure_ascii=False, 
                     indent=4, separators=(',', ':')))

