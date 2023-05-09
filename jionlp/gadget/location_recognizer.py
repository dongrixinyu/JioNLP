# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


"""
给定一篇中文文本，确定其归属地。主要应用在新闻领域，确定新闻的发生地
注意事项：
    1、该方法主要应用于舆情分析与统计
    2、该方法采用了分词器 jiojio，采用词性标注得到的地名 ns 进行统计计算
       因此，方法的计算效果和性能 90% 程度上受到分词器影响。
    3、该方法抽取结果中，排序靠后的地址可能存在错误，如，原文中出现“北京朝阳”，
       而结果中返回了
           {'province': '辽宁省', 'city': '朝阳市', 'county': '朝阳县'}
       因此，当有多个地址返回时，排序靠后的地址往往可靠性低。
    4、在新闻领域，其归属地往往由 1~3 个国内城市或国家构成，这是分析大量新闻
       得出的结论，极少有某篇新闻涉及到诸多国家或城市。因此，返回的地址中，可
       靠性较高的是前三个地址，在应用时也可仅考虑前三个重要的地址。
    5、国内地名未考虑乡镇级，国外地名未考虑洲、州、邦、县级；地名未考虑海洋、
       山形、河流、楼宇等，此类地址全部存入 others 字段，方便后续的处理。
    6、文本中，存在“中国”二字，而不存在具体的城市、省份的情况，往往为外交新闻，
       因此，在 foreign 字段中，也可能出现“中国”，而 domestic 为空。
    7、地名词典仍有扩充和改进的空间。
    8、仍需增加一些规则，如“北京时间”不能计入地名计算，往往分词器无法判断；
       “日美同盟”中需要分别考虑日本、美国，此类简称也无法考虑。
    9、返回结果中，第一个地址属于文本的归属地的正确率为 93%。

"""


import copy
import collections

import jiojio
from jionlp.dictionary.dictionary_loader import china_location_loader
from jionlp.dictionary.dictionary_loader import world_location_loader


class LocationRecognizer(object):
    """ 地域识别，识别出一篇文本中主要涉及的地址，即返回一篇文本的归属地，
    返回的结果具体到地级市，国外具体到城市
    具体假设为，每一个句子仅识别一个地址，然后统计所有的结果

    计算方法：
    1、对文本做分词与词性标注（默认使用分词工具 jiojio），找出其中地名词汇，统计词频；
    2、对所有地名词汇进行扩充，如，将 “广州” 扩展成
       {'province': '广东省', 'city': '广州市', 'county': None}；
    3、将存在上下级关系的地名进行合并，如“西藏”和“拉萨”，同属于一个地址，则进行合并，
       {'province': '西藏', 'city': '拉萨', 'county': None}；
    4、统计国内、国外、以及无法归纳的地址，按频次排序返回。

    Args:
        text(str): 输入的文本，一般是网络新闻文本

    Returns:
        dict: 地名结果，包含若干字段，见如下示例。地名分为国内和国外两部分，其中国内
            按照省、市、县，国外按照国家、市的结构进行返回。每个分别默认返回最佳的结
            果。如两个国家城市具有同样的权重，则同时返回。返回数量可以使用参数调节。
            除此之外，仍有一些地名无法用地名行政区划进行匹配，则在 Addition 字段进
            行返回。

    Examples:
        >>> text = '成都市召开了中日韩三国峰会，中国、日本、韩国三国首脑，'
                   '日本东京和尚家村缔结了互帮互助...'
        >>> print(jio.recognize_location(text))
        {
            'domestic': [
                [
                    {
                        'province': '四川省',
                        'city': '成都市',
                        'county': None
                    },
                    1
                ]
            ],
            'foreign': [
                [
                    {
                        'country': '日本',
                        'city': '东京'
                    },
                    3
                ],
                [
                    {
                        'country': '韩国',
                        'city': None
                    },
                    1
                ]
            ],
            'others': [
                '尚家村',
                '印度洋',
                '羽田机场',
                '直布罗陀海峡'
            ]
        }

    """
    def __init__(self):
        self.load_flag = None
        
    def _prepare(self):
        jiojio.init(pos_rule=True, pos=True)
        self.load_flag = True

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
        """ 从地址中获取所有可能涉及到的候选地址，
        如给定，朝阳，匹配得到
            [
                {'province': '北京市', 'city': '北京市', 'county': '朝阳区'},
                {'province': '辽宁省', 'city': '朝阳市', 'county': None},
                {'province': '辽宁省', 'city': '朝阳市', 'county': '朝阳县'},
                {'province': '吉林省', 'city': '长春市', 'county': '朝阳区'}
            ]

        存在一个地址对应多个详细地址的情况，如 朝阳，匹配得到 北京朝阳，辽宁朝阳，吉林长春朝阳
        此种情况下需要全部返回。

        """
        if self.china_administrative_map_list is None:
            self._prepare()
        
        level_list = ['province', 'city', 'county']
        candidate_admin_list = []  # 候选列表
        for admin_item in self.china_administrative_map_list:
            count = 0
            for idx, name_item in enumerate(admin_item):
                match_flag = False
                for name in name_item:  # 别名与全名任意匹配一个
                    if name is not None and name == location:
                        match_flag = True
                        break
                if match_flag:
                    count += 1
                    # offset 中的每一个元素，分别指示省、市、县三级是否被匹配
                    offset_list = [1 if i <= idx else 0 for i in range(3)]
                    
            if count > 0:
                cur_item = dict()
                for level, offset, name in zip(level_list, offset_list, admin_item):
                    if offset == 1:
                        cur_item.update({level: name[0]})
                    else:
                        cur_item.update({level: None})
                if cur_item not in candidate_admin_list:
                    candidate_admin_list.append(cur_item)
            # TODO
            # 当这里已有结果后，若不是有歧义的地名，如辽宁朝阳，北京朝阳等之外，可以直接跳出循环
            # 返回结果即可，可以大大加快计算速度，待总结
            
        return candidate_admin_list
    
    def get_world_candidates(self, location):
        """ 给定一个地址字符串，找出其中的候选地址，
        如给定 科伦坡，匹配得到
            [{'country': '斯里兰卡', 'city': '科伦坡'}]
        """
        if self.world_administrative_map_list is None:
            self._prepare()
            
        level_list = ['country', 'city']
        candidate_admin_list = []  # 候选列表
        for admin_item in self.world_administrative_map_list:
            count = 0
            for idx, name_item in enumerate(admin_item):
                match_flag = False
                if idx == 0:  # 国家名
                    for name in name_item:  # 别名与全名任意匹配一个
                        if name is not None and name == location:
                            match_flag = True
                            break
                elif idx == 1:  # 城市名
                    if name_item is not None:
                        if name_item in [location, location.replace('市', '')]:
                            # 兼顾到国外地名未提各类别名的情况
                            match_flag = True
                else:
                    raise ValueError
                
                if match_flag:
                    count += 1
                    # offset 中的每一个元素，分别指示国家、城市是否被匹配
                    offset_list = [1 if i <= idx else 0 for i in range(2)]
            
            if count > 0:
                cur_item = dict()
                for level, offset, name in zip(level_list, offset_list, admin_item):
                    if offset == 1:
                        if type(name) is list:
                            
                            cur_item.update({level: name[0]})
                        elif type(name) is str:
                            cur_item.update({level: name})
                    else:
                        cur_item.update({level: None})
                if cur_item not in candidate_admin_list:
                    candidate_admin_list.append(cur_item)
            # TODO:
            # 世界地名较少有重复的城市名称，因此可以考虑当匹配后，直接跳出循环
        return candidate_admin_list

    @staticmethod
    def _combine_china_locations(china_combine_list, cur_location):
        """ 给定一个匹配的地名列表，以及一个当前的待合并地址，
        将当前的地址放入地名列表，须注意与该合并的地址进行合并。
        china_combine_list: 结构如下
            [[{'province': '江苏省', 'city': '南京市', 'county': '鼓楼区'}, 2, True],
             [{'province': '河南省', 'city': '开封市', 'county': '鼓楼区'}, 1, True],
             [{'province': '河南省', 'city': None, 'county': '鼓楼区'}, 6, False]]

             其中 数字代表出现的频次，True 代表可以作为地址结果进行返回，
             False 表示不可以作为最终结果返回

        cur_location: 结构如下：
            [{'province': '河南省', 'city': '开封市', 'county': None}, 8]

        """
        if len(china_combine_list) == 0:
            cur_location.append(True)
            china_combine_list.append(cur_location)
            return china_combine_list
            
        combine_flag = False
        for item in china_combine_list:
            
            cur_combine_flag = True
            if item[0]['province'] is not None and cur_location[0]['province'] is not None:
                if item[0]['province'] != cur_location[0]['province']:
                    cur_combine_flag = False
            if item[0]['city'] is not None and cur_location[0]['city'] is not None:
                if item[0]['city'] != cur_location[0]['city']:
                    cur_combine_flag = False
            if item[0]['county'] is not None and cur_location[0]['county'] is not None:
                if item[0]['county'] != cur_location[0]['county']:
                    cur_combine_flag = False

            if cur_combine_flag:
                # 可以合并了，因为都一样的公共部分
                # 将较短的一个地名设置为 False，频次取两者最大值
                none_num = len([i for i in list(item[0].values()) if i is None])
                cur_none_num = len([i for i in list(cur_location[0].values()) if i is None])
                
                if none_num < cur_none_num:  # 当前进入的地址较短，不作为最终结果
                    item[1] = item[1] + cur_location[1]
                    cur_location.append(False)
                    combine_flag = True  # 在计算最末将该地址添加进去
                    
                else:  # 替换掉该条较短的地址，作为最终结果
                    item[2] = False
                    cur_location[1] = item[1] + cur_location[1]
                    cur_location.append(True)
                    combine_flag = True
                    
        if combine_flag:
            china_combine_list.append(cur_location)
        else:  # 并无合并，但是仍需加在所有结果的末尾
            cur_location.append(True)
            china_combine_list.append(cur_location)
            
        return china_combine_list

    @staticmethod
    def _combine_world_locations(world_combine_list, cur_location):
        """ 给定一个匹配的地名列表，以及一个当前的待合并地址，
        将当前的地址放入地名列表，须注意与该合并的地址进行合并。
        world_combine_list: 结构如下
            [[{'country': '美国', 'city': '华盛顿'}, 2, True],
             [{'country': '斯里兰卡', 'city': '科伦坡'}, 1, True],
             [{'country': '斯里兰卡', 'city': None}, 6, False]]

             其中 数字代表出现的频次，True 代表可以作为地址结果进行返回，
             False 表示不可以作为最终结果返回

        cur_location: 结构如下：
            [{'country': '日本', 'city': None}, 8]

        """
        if len(world_combine_list) == 0:
            cur_location.append(True)
            world_combine_list.append(cur_location)
            return world_combine_list

        combine_flag = False
        for item in world_combine_list:

            cur_combine_flag = True
            if item[0]['country'] is not None and cur_location[0]['country'] is not None:
                if item[0]['country'] != cur_location[0]['country']:
                    cur_combine_flag = False
            if item[0]['city'] is not None and cur_location[0]['city'] is not None:
                if item[0]['city'] != cur_location[0]['city']:
                    cur_combine_flag = False

            if cur_combine_flag:
                # 可以合并了，因为都一样的公共部分
                # 将较短的一个地名设置为 False，频次取两者最大值
                none_num = len([i for i in list(item[0].values()) if i is None])
                cur_none_num = len([i for i in list(cur_location[0].values()) if i is None])
                if none_num < cur_none_num:  # 当前进入的地址较短，不作为最终结果
                    item[1] = item[1] + cur_location[1]
                    cur_location.append(False)
                    combine_flag = True  # 在计算最末将该地址添加进去

                else:  # 替换掉该条较短的地址，作为最终结果
                    item[2] = False
                    cur_location[1] = item[1] + cur_location[1]
                    cur_location.append(True)

                    combine_flag = True

        if combine_flag:
            world_combine_list.append(cur_location)
        else:  # 并无合并，但是仍需加在所有结果的末尾
            cur_location.append(True)
            world_combine_list.append(cur_location)

        return world_combine_list

    def __call__(self, text, top_k='default'):

        if self.load_flag is None:
            self._prepare()
        
        final_res = {'domestic': None, 'foreign': None, 'others': None}
        
        text_pos_seg = jiojio.cut(text)
        text_location = [item[0] for item in text_pos_seg if item[1] == 'ns']
        if len(text_location) == 0:
            return {'domestic': None, 'foreign': None, 'others': None}
        
        location_count = dict(collections.Counter(text_location).most_common())
        
        not_matched_list = copy.deepcopy(location_count)  # 统计未匹配地址
        
        # 中国国内部分
        china_combine_list = []  # 将若干中国地名合并
        for location, count in location_count.items():
            china_candidates = self.get_china_candidates(location)
            if len(china_candidates) > 0:  # 匹配到地址
                not_matched_list.pop(location)  # 从未匹配词典中删除
                # 此时，未知 郑州 和 金水区 是对应的上下级映射关系，需要进行关联
                for china_candidate in china_candidates:
                    china_combine_list = self._combine_china_locations(
                        china_combine_list, [china_candidate, count])
        
        domestic_locations = sorted(
            [item[:2] for item in china_combine_list if item[-1]],
            key=lambda i: i[1], reverse=True)
        
        # 世界部分
        world_combine_list = list()  # 将若干世界地名合并
        for location, count in location_count.items():
            world_candidates = self.get_world_candidates(location)
            if len(world_candidates) > 0:  # 匹配到地址
                if location in not_matched_list:
                    not_matched_list.pop(location)  # 从未匹配词典中删除
                
                # 此时，未知 斯里兰卡 和 科伦坡 是对应的上下级映射关系，需要进行关联
                for world_candidate in world_candidates:
                    world_combine_list = self._combine_world_locations(
                        world_combine_list, [world_candidate, count])

        foreign_locations = sorted(
            [item[:2] for item in world_combine_list if item[-1]],
            key=lambda i: i[1], reverse=True)
        
        if len(domestic_locations) > 0:
            if top_k == 'default':
                final_res['domestic'] = domestic_locations[:3]
            else:
                final_res['domestic'] = domestic_locations[:top_k]
                
        if len(foreign_locations) > 0:
            if top_k == 'default':
                final_res['foreign'] = foreign_locations[:3]
            else:
                final_res['foreign'] = foreign_locations[:top_k]
        if len(not_matched_list) > 0:
            final_res['others'] = not_matched_list
        
        return final_res
            

if __name__ == '__main__':
    import json
    lr = LocationRecognizer()
    text = '中国海军和平方舟医院船首访多米尼加。新华社圣多明各11月1日电（记者吴昊 江山）执行“和谐使命－2018”任务的中国海军和平方舟医院船11月1日抵达圣多明各港，开始对多米尼加进行为期8天的友好访问。多米尼加地处加勒比海，今年5月1日，与中国正式建交。这是两国建交以来，中国海军舰艇首次访多。当地时间1日上午7时30分许，和平方舟缓缓驶进圣多明各港。停泊在港内的多海军舰艇悬挂满旗，舰员在甲板分区列队，随着一长声鸣笛，整齐敬礼，表达热烈欢迎。和平方舟悬挂满旗致谢，鸣笛一长声还礼，海军官兵行举手礼致敬。8时许，和平方舟停靠圣多明各港码头，多方举行热烈欢迎仪式，多海军军乐队分别演奏两国国歌，官兵代表向“和谐使命－2018”任务指挥员敬献鲜花。多军政官员，中国驻多使馆临时代办张步新 率使馆工作人员、华侨华人、中资机构代表等在码头迎接。仪式结束后，多军政官员、华侨华人等登船参观。当天下午，和平方舟主平台全面展开，进行诊疗活动。多米尼加是和平方舟 入列以来访问的第41个国家，也是此次任务的第九站。访问期间，“和谐使命－2018”任务指挥员将拜会多军政要员，和平方舟将开展联合诊疗、文化联谊、设备维修等系列活动。'
    res = lr(text)
    print(json.dumps(res, ensure_ascii=False, 
                     indent=4, separators=(',', ':')))
