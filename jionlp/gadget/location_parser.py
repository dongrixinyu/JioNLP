# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re
# import copy
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
        self.town_village_dict = {}
        
    def _mapping(self, china_loc, china_change_loc):
        # 整理行政区划码映射表
        # TODO:
        # 整个功能最耗时部分是 get_candidate 中的三重循环，因此，为加速，应当将
        # self.administrative_map_list 这里的 list 改为 dict，其中，又涉及到诸多信息，这里暂留坑。
        self.administrative_map_list = []  # 地址别称

        for prov in china_loc:
            if prov.startswith('_'):
                continue
            if china_loc[prov]['_alias'] in self.municipalities_cities:
                pass
                # 去除直辖市仅包含省级的信息，因为直辖市一定将匹配至市一级。
            else:
                self.administrative_map_list.append(
                    [china_loc[prov]['_admin_code'],
                     [prov, china_loc[prov]['_alias']],
                     [None, None],
                     [None, None], True])  # True 表示数据为最新地名，反之为旧地名

            for city in china_loc[prov]:
                if city.startswith('_'):
                    continue

                for alias_name in china_loc[prov][city]['_alias']:

                    self.administrative_map_list.append(
                        [china_loc[prov][city]['_admin_code'],
                         [prov, china_loc[prov]['_alias']],
                         [city, alias_name],
                         [None, None], True])

                    for county in china_loc[prov][city]:
                        if county.startswith('_'):
                            continue
                        self.administrative_map_list.append(
                            [china_loc[prov][city][county]['_admin_code'],
                             [prov, china_loc[prov]['_alias']],
                             [city, alias_name],
                             ['经济技术开发区' if county.endswith('经济技术开发区') else county,
                              china_loc[prov][city][county]['_alias']],
                             True])
                        # 这里 “经济技术开发区”，例如 “秦皇岛市经济技术开发区”，
                        # 容易将市、县级的地址匹配在相同的 offset 上，造成错误

                        if self.town_village:  # 补充 self.town_village_list

                            key_name = prov + city + county
                            value_dict = china_loc[prov][city][county]
                            self.town_village_dict.update({key_name: value_dict})

        # 将旧有的地名融入 self.administrative_map_list，并建立映射表
        self.old2new_loc_map = {}

        for item in china_change_loc:
            self.administrative_map_list.append(
                ['000000', item['old_loc'][0], item['old_loc'][1],
                 item['old_loc'][2], False])

            self.old2new_loc_map.update(
                {''.join([i[0] for i in item['old_loc'] if i[0] is not None]): item['new_loc']})

    def _prepare(self):
        self.municipalities_cities = {'北京', '上海', '天津', '重庆', '香港', '澳门'}
        # '北京市', '上海市', '天津市', '重庆市', '香港特别行政区', '澳门特别行政区'])

        # 处理异常的别名
        self.loc_alias_string = '【loc_alias】'
        self.exception_suffix_pattern = re.compile('(【loc_alias】(路|大街|街))')

        # 添加中国区划词典
        china_loc = china_location_loader(detail=self.town_village)
        china_change_loc = china_location_change_loader()
        self._mapping(china_loc, china_change_loc)

        self.loc_level_key_list = ['省', '市', '县']
        if self.town_village:
            self.loc_level_key_list.extend(['乡', '村'])
        self.loc_level_key_dict = dict(
            [(loc_level, None) for loc_level in self.loc_level_key_list])

    def get_candidates(self, location_text):
        """ 从地址中获取所有可能涉及到的候选地址 """

        candidate_admin_list = []  # 候选列表
        for admin_item in self.administrative_map_list:
            count = 0  # 匹配个数
            # offset 中的每一个元素，分别指示在地址中的 “索引”，以及指示 “全名或别名”
            # 索引指在地址中的那个位置出现，优先处理靠左靠前的
            # offset 匹配全名用 0 表示，匹配别名用 1 表示。
            offset_list = [[-1, -1], [-1, -1], [-1, -1]]

            for idx, name_item in enumerate(admin_item[1: 4]):
                match_flag = False
                cur_name = None
                cur_alias = None
                for alias_idx, name in enumerate(name_item):  # 别名与全名任意匹配一个
                    if name is not None and name in location_text:
                        # 此时需添加逻辑，若 name 为别名，且之后立即跟了 “路、街” 等字，则需跳过处理。
                        # 例如：“北海市重庆路其仓11号”，这样的城市名会受到干扰，应当将 “重庆路” 进行过滤
                        if alias_idx == 1:
                            exception_alias_flag = self._process_exception_alias(name, location_text)
                            if not exception_alias_flag:
                                continue

                        match_flag = True
                        cur_name = name
                        cur_alias = alias_idx
                        break

                if match_flag:
                    count += 1
                    offset_list[idx][0] = location_text.index(cur_name)
                    offset_list[idx][1] = cur_alias

                    # 两条匹配，相差一个字符位置，说明匹配错误，
                    # 如 “青海西宁”，容易匹配“海西”，是错误的。
                    if idx == 1 and (offset_list[idx-1][0] >= 0):
                        if offset_list[idx][0] - offset_list[idx-1][0] == 1:
                            count = 0
                            break
                    if idx == 2:
                        if offset_list[idx-1][0] >= 0:
                            if offset_list[idx][0] - offset_list[idx-1][0] == 1:
                                count = 0
                                break
                        if offset_list[idx-2][0] >= 0:
                            if offset_list[idx][0] - offset_list[idx-2][0] == 1:
                                count = 0
                                break

            if count > 0:
                # cur_item = copy.deepcopy(admin_item)
                # cur_item.extend([count, offset_list])
                # candidate_admin_list.append(cur_item)
                if admin_item[1][1] in self.municipalities_cities and admin_item[1][1] in location_text:
                    count -= 1
                if len(admin_item) == 5:
                    admin_item.extend([count, offset_list])
                    candidate_admin_list.append(admin_item)
                elif len(admin_item) == 7:
                    admin_item[-2] = count
                    admin_item[-1] = offset_list
                    candidate_admin_list.append(admin_item)
                else:
                    raise ValueError('length of admin_item is wrong!')

        return candidate_admin_list

    def _process_exception_alias(self, name, location_text):
        # 处理一些异常的简称，如 “上海市嘉定区太原路99号” 中的 太原 这个简称
        location_text = location_text.replace(name, self.loc_alias_string)
        matched_res = self.exception_suffix_pattern.search(location_text)

        if matched_res is None:
            # 说明没有 “太原路” 这样的异常别名，可以正常返回
            return True
        else:
            # 有异常别名，需跳过
            return False

    def __call__(self, location_text, town_village=False, change2new=True):

        self.town_village = town_village
        if self.administrative_map_list is None:
            self._prepare()
        if self.town_village and self.town_village_dict == {}:
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

        # 2.0 去除那些同一个 offset 匹配了多个别名的内容
        # 如 “湖南省长沙市”，此时将匹配到 “湖南省长沙市长沙县”，这是错误的，应当按全名匹配
        # 条件是，当同一个 offset 值匹配了两个级别的地名，其中一个是全名，另一个是别名时。按全名操作，删除别名
        non_same_offset_list = []
        for item in candidate_admin_list:
            offset_list = [i[0] for i in item[-1] if i[0] > -1]
            if len(offset_list) != len(set(offset_list)):  # 说明有重复匹配项
                the_same_offset = collections.Counter(offset_list).most_common()[0][0]
                the_same_offset_loc = [i for i in item[-1] if i[0] == the_same_offset]  # 长度必然为 2
                if the_same_offset_loc[0][1] == 0 and the_same_offset_loc[1][1] == 1:
                    # 此时说明地址同一个位置的词汇匹配到了不同的全名和别名，
                    # 其中第一个为高级别的 地名，为省、市，第二个为低级别的，市、县。
                    # 若匹配到高级别的全名和低级别的别名，则将该 item 丢弃，否则保留
                    pass
                else:
                    non_same_offset_list.append(item)
            else:
                non_same_offset_list.append(item)

        candidate_admin_list = non_same_offset_list
        # 2.1 找出文本中匹配数量最多的
        max_matched_num = max([item[-2] for item in candidate_admin_list])
        candidate_admin_list = [item for item in candidate_admin_list
                                if item[-2] == max_matched_num]

        # 对于有些新旧地名简称相同，且省市县不按靠前的位置依次排开的，删除旧地名
        if len(candidate_admin_list) == 2:
            # 1. 这种情况下，candidate_admin_list包含2个行政区划且offset中地址的 “索引”相同
            # 索引名完全相同
            if [i[0] for i in candidate_admin_list[0][-1]] == [i[0] for i in candidate_admin_list[1][-1]]:
                # 删除旧地名
                candidate_admin_list = [item for item in candidate_admin_list if item[4] is True]
            # 2. 别名完全相同。
            elif [i[1] for i in candidate_admin_list[0][1:4]] == [i[1] for i in candidate_admin_list[1][1:4]]:
                candidate_admin_list = [item for item in candidate_admin_list if item[4] is True]

        # 此时，若仅有一个地址被匹配，则应当直接返回正确的结果
        if len(candidate_admin_list) == 1:
            result = self._get_final_res(
                candidate_admin_list[0], location_text, [],
                town_village=town_village, change2new=change2new)

            return result

        # 2.2 找出匹配位置最靠前的
        candidate_admin_list = sorted(
            candidate_admin_list, key=lambda i: sum([j[0] for j in i[-1]]))

        # 对于有些 地市名 和 县级名简称相同的，需要进行过滤，根据被匹配的 offset 进行确定。
        # 直辖市除外
        new_candidate_admin_list = []
        for item in candidate_admin_list:
            if item[1][1] in self.municipalities_cities:
                new_candidate_admin_list.append(item)
            else:
                if -1 not in [item[-1][0][0], item[-1][1][0], item[-1][2][0]]:
                    # 省、市、县全都匹配到
                    if (item[-1][0][0] < item[-1][1][0]) and (item[-1][1][0] < item[-1][2][0]):
                        # 必须按照 省、市、县的顺序进行匹配
                        new_candidate_admin_list.append(item)
                else:
                    new_candidate_admin_list.append(item)

        candidate_admin_list = new_candidate_admin_list
        if len(candidate_admin_list) == 0:
            result = {'province': None,
                      'city': None,
                      'county': None,
                      'detail': location_text,
                      'full_location': location_text,
                      'orig_location': location_text}
            return result

        min_matched_offset = sum([j[0] for j in candidate_admin_list[0][-1]])
        candidate_admin_list = [item for item in candidate_admin_list 
                                if sum([j[0] for j in item[-1]]) == min_matched_offset]

        # 2.3 优先匹配包含全名的，其次匹配别名，此处将别名的过滤掉，仅保留全名的
        # 分两种情况
        # case 1: 如 “海南藏族自治州”，不可匹配到 “海南省”
        full_alias_list = [min([j[1] for j in item[-1] if j[1] > -1]) for item in candidate_admin_list]
        full_alias_min = min(full_alias_list)
        candidate_admin_list = [item for val, item in zip(full_alias_list, candidate_admin_list) if val == full_alias_min]
        # case 2: 如 “科尔沁左翼后旗”，不可匹配到 “科尔沁区”
        full_alias_list = [sum([j[1] for j in item[-1] if j[1] > -1]) for item in candidate_admin_list]
        full_alias_min = min(full_alias_list)
        candidate_admin_list = [item for val, item in zip(full_alias_list, candidate_admin_list)
                                if val == full_alias_min]

        # 2.4 若全部都匹配别名，则别名获取级别应当越高越好
        # 如“海南大学”，应当匹配“海南省”，而非“海南藏族自治州”，
        # 如“西安交通大学”，应当匹配 “西安市”，而非“吉林省通辽市西安区”
        # 受 2.3 中 变量 full_alias_min 控制，该变量为 0 时，表示有 item 匹配了全名
        alias_matched_num_list = [
            len([i[0] for i in item[-1] if i[0] > -1]) for item in candidate_admin_list]
        # 该变量指示了所有 item 都仅匹配了一个别名
        max_alias_matched_num = max(alias_matched_num_list)
        if full_alias_min == 1 and max_alias_matched_num == 1:
            # 说明全部都是别名，无全名匹配，且只匹配了一个别名
            # 例如，“西安交通大学”，此时应当尽量匹配省、市，而避免比配市、县
            candidate_admin_list = sorted(
                candidate_admin_list,
                key=lambda item: [idx for idx, i in enumerate(item[-1]) if i[0] != -1][0])

        # step 3: 去除重复地名
        # step 3.1: 某些地名会同时匹配到老地名和新地名，此时需要保留新地名，去除旧地名
        # 该情况下，不需要考虑 change2new 参数，直接合入新地址
        new_candidate_admin_list = []
        for item in candidate_admin_list:
            if item[0] == '000000':
                # 找到老地址映射的新地址
                if item[1][0] is None or item[2][0] is None or item[3][0] is None:
                    new_candidate_admin_list.append(item)
                    continue

                loc_key = item[1][0] + item[2][0] + item[3][0]
                if loc_key in self.old2new_loc_map:
                    new_loc = self.old2new_loc_map[loc_key]

                    has_new_loc_flag = False
                    for _item in candidate_admin_list:
                        if _item[0] != '000000':
                            if new_loc[0] == _item[1][0] and new_loc[1] == _item[2][0] and new_loc[2] == _item[3][0]:
                                # 说明候选地址集里已有新地址，删除旧地址
                                has_new_loc_flag = True
                                break
                    if not has_new_loc_flag:
                        new_candidate_admin_list.append(item)

                else:
                    new_candidate_admin_list.append(item)
            else:
                new_candidate_admin_list.append(item)

        candidate_admin_list = new_candidate_admin_list

        # step 3.2: 县级存在重复名称，计算候选列表中可能重复的县名，如 “鼓楼区”、“高新区” 等
        county_dup_list = [item[3][item[-1][-1][1]] for item in candidate_admin_list]
        county_dup_list = collections.Counter(county_dup_list).most_common()
        county_dup_list = [item[0] for item in county_dup_list if item[1] > 1]
        
        final_admin = candidate_admin_list[0]  # 是所求结果

        result = self._get_final_res(
            final_admin, location_text, county_dup_list,
            town_village=town_village, change2new=change2new)

        return result

    def _get_final_res(self, final_admin, location_text, county_dup_list,
                       town_village=True, change2new=True):
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
        if len(detail_part) == 0:
            pass
        elif detail_part[0] in '县':
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

        prov = result['province'] if result['province'] is not None else ''
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
    lp = LocationParser()
    loc = '成都是西部大开发先锋城市。'
    res = lp(loc)
    print(res)

