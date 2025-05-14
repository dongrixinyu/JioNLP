# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP


import os
import re
import json
import math

from jionlp import logging
from jionlp.util.file_io import read_file_by_line


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
GRAND_DIR_PATH = os.path.dirname(DIR_PATH)


__all__ = ['char_distribution_loader', 'char_radical_loader',
           'china_location_change_loader', 'china_location_loader',
           'chinese_char_dictionary_loader',
           'chinese_idiom_loader', 'chinese_word_dictionary_loader',
           'html_entities_dictionary_loader',
           'idf_loader', 'llm_test_dataset_loader', 'negative_words_loader',
           'phone_location_loader',
           'pinyin_char_loader', 'pinyin_phrase_loader',
           'pornography_loader',
           'quantifiers_loader',
           'sentiment_expand_words_loader',
           'sentiment_words_loader', 'stopwords_loader',
           'telecom_operator_loader',
           'traditional_simplified_loader',
           'word_distribution_loader',
           'world_location_loader', 'xiehouyu_loader', 'STRUCTURE_DICT']

STRUCTURE_DICT = {
    0: '一体结构', 1: '左右结构', 2: '上下结构', 3: '左中右结构',
    4: '上中下结构', 5: '右上包围结构', 6: '左上包围结构', 7: '左下包围结构',
    8: '全包围结构', 9: '半包围结构'}


def quantifiers_loader():
    """ 加载常见量词词典。返回每个量词在语料中的出现总次数、该词出现时作为量词出现的概率。
    词典说明：
        1、此量词词典并不是语料中的全量量词，做了一部分删减。
            - 若量词的出现频次过低，很难称之为一个完整量词，如 “些些”，则删除；
            - 若量词的出现频次偏低，且该词作为量词的概率很低，如 “拨”，频次 1860，概率 0.1533。则删除。
        2、该量词词典根据词性标注语料获取。

    Returns:
        dict(list): 例如：
            {'岁': {'total_num': 297368,
                    'prob': 0.9964}
            ... }
    """
    quantifiers_info = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary', 'quantifiers_stat.txt'), auto_loads_json=False)

    quantifiers_info_dict = {}
    for item in quantifiers_info:
        quantifier, num, prob = item.strip().split('\t')
        quantifiers_info_dict.update(
            {quantifier: {'total_num': num, 'prob': prob}})

    return quantifiers_info_dict


def char_distribution_loader():
    """ 加载 utf-8 编码字符在中文文本中的分布，返回每个字在语料中的出现总次数、概率、
    概率的 -log10 值。

    Returns:
        dict(list): 例如
            {'中': {'total_num': 61980430,
                    'prob': 0.0054539722,
                    'log_prob': 2.2632870},
             ...}

    """
    char_info = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary', 'char_distribution.json'))

    char_info_dict = dict()
    total_num = sum([item[1] for item in char_info])
    for item in char_info:
        char_info_dict.update(
            {item[0]: {'total_num': item[1],
                       'prob': item[1] / total_num,
                       'log_prob': - math.log10(item[1] / total_num)}})

    return char_info_dict


def china_location_loader(detail=False):
    """ 加载中国地名词典 china_location.txt

    Args:
        detail(bool): 若为 True，则返回 省、市、县区、乡镇街道、村社区 五级信息；
            若为 False，则返回 省、市、县区 三级信息

    """
    with open(os.path.join(GRAND_DIR_PATH, 'dictionary/china_location.txt'),
              'r', encoding='utf-8') as f:
        location_jio = f.readlines()
    
    cur_province = None
    cur_city = None
    cur_county = None
    cur_town = None
    cur_village = None
    location_dict = {}

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

        elif item.startswith('\t\t\t\t'):  # 村、社区
            if not detail:
                continue
            cur_village = item.strip()
            location_dict[cur_province][cur_city][cur_county][cur_town].update(
                {cur_village: None})

        elif item.startswith('\t\t\t'):  # 乡镇、街道
            if not detail:
                continue
            cur_town = item.strip()
            location_dict[cur_province][cur_city][cur_county].update(
                {cur_town: dict()})

        elif item.startswith('\t\t'):  # 县、区
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
            if '/' in alias_name:
                alias_name_list = alias_name.split('/')
                location_dict[cur_province].update(
                    {cur_city: {'_full_name': city,
                                '_alias': alias_name_list,
                                '_admin_code': admin_code}})
            else:
                location_dict[cur_province].update(
                    {cur_city: {'_full_name': city,
                                '_alias': [alias_name],
                                '_admin_code': admin_code}})

    return location_dict


def china_location_change_loader():
    """ 加载中国地名变更词典 china_location_change.txt
    整理了 2018 年至今国内政府批复修改的县级以上的地名变化。仅添加了地名的撤销变更，
    而对未撤销地名的新增地名，如深圳市光明区，不做记录，因为不影响工具的使用。

    Args:
        None

    Returns:
        dict: 返回 省、市、县区 三级的变更地址，以及变更日期和批准部门；
            '国批' 表示国务院批准，'民批' 表示国务院民政部批准，
            '省批'表示省级政府或民政部批准。

    """
    location_change_jio = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/china_location_change.txt'),
        auto_loads_json=False)

    location_change_list = []
    for line in location_change_jio:
        location_change_dict = dict()
        line_seg = line.split('=>')
        orig_line_seg = line_seg[0].split('\t')
        new_line_seg = line_seg[1].split('\t')

        if len(orig_line_seg) == 8:  # 县一级
            location_change_dict.update(
                {'date': orig_line_seg[0], 'department': orig_line_seg[1],
                 'old_loc': [orig_line_seg[2: 4], orig_line_seg[4: 6], orig_line_seg[6: 8]],
                 'new_loc': new_line_seg})

        elif len(orig_line_seg) == 6:  # 市一级，主要是 襄樊市 => 襄阳市
            assert len(new_line_seg) == 2, 'error with line `{}`'.format(line)

            location_change_dict.update(
                {'date': orig_line_seg[0], 'department': orig_line_seg[1],
                 'old_loc': [orig_line_seg[2: 4], orig_line_seg[4: 6], [None, None]],
                 'new_loc': [new_line_seg[0], new_line_seg[1], None]})

        location_change_list.append(location_change_dict)

    return location_change_list


def world_location_loader():
    """ 加载世界地名词典 world_location.txt """
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/world_location.txt'),
        auto_loads_json=False)
    
    result = {}
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
    """ 加载停用词典 stopwords.txt """
    res = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/stopwords.txt'),
        auto_loads_json=False)
    # 一般漏掉了若干转换符号
    res.extend(['', ' ', '\t'])
    res = list(set(res))
    return res


def negative_words_loader():
    """ 加载否定词典 negative_words.txt """
    res = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/negative_words.txt'),
        auto_loads_json=False)
    
    return res


def chinese_char_dictionary_loader():
    """ 加载百度汉语字典，字典与新华字典大同小异，分别包括：
    汉字，偏旁，字形结构，四角编码，笔画顺序，繁体字，五笔输入编码，拼音，释义

    本词典囊括了 utf-8 编码中，“一~龥”的所有汉字，但有所删减
    考虑到百度汉语字典无法与时俱进，其中有相当多的老旧内容，故增删说明如下：
        1、删除了所有的日本和字 -> 释义中包含 “日本汉字/日本地名用字” 内容，如 “桛 ā 1.日本和字。”；
        2、删除了释义未详的字 -> 释义中包含 “义未详” 内容，或某个字的某个读音义未详，如 “穝zuō## ⒈义未详。”
        3、删除了低频汉字 -> 释义中字频低于亿分之一的，且不在 char_distribution.json 中的字。
            如 “葨wēi 1.见"葨芝"。”
        4、删除了所有的韩国、朝鲜创字、用字、用意 -> 櫷guī槐木的一种（韩国汉字）
        5、删除了古代用字、用意 -> 释义中包含  “古同~/古代~/古通~/古书~/古地名/古人名” 内容，
            但如有多个释义，且其中有非古代释义，则保留该汉字；如 “鼃 wā 古同蛙”。但常见古字，如“巙kuí”

        共计删减 3402 字。

    """
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary',
                     'chinese_char_dictionary.txt'),
        strip=False, auto_loads_json=False)

    pinyin_ptn = re.compile(r'\[[a-zàáāǎòóōǒèéēěìíīǐùúūǔǜǘǖǚǹńňüḿ]{1,8}\]')
    explanation_ptn = re.compile(r'\d{1,2}\.')

    char_dict = {}
    for idx, line in enumerate(content):
        segs = line.split('\t')

        assert len(segs) == 8

        # 拆解每个读音的各个含义
        pinyin_list = [item[1:-1] for item in pinyin_ptn.findall(segs[-1])]
        explanation_list = [item for item in pinyin_ptn.split(segs[-1].replace('~', segs[0]).strip())
                            if item != '']
        assert len(pinyin_list) == len(explanation_list)

        pinyin_explanation_dict = {}
        for pinyin, explanations in zip(pinyin_list, explanation_list):
            explanations = [ex for ex in explanation_ptn.split(explanations) if ex != '']
            pinyin_explanation_dict.update({pinyin: explanations})

        char_dict.update({
            segs[0]: {'radical': segs[1],
                      'structure': STRUCTURE_DICT[int(segs[2])],
                      'corner_coding': segs[3],
                      'stroke_order': segs[4],
                      'traditional_version': segs[5],
                      'wubi_coding': segs[6],
                      'pinyin': pinyin_explanation_dict}})
        
    return char_dict


def chinese_idiom_loader():
    """ 加载成语词典 chinese_idiom.txt """
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary/chinese_idiom.txt'),
        auto_loads_json=False)
    
    result = {}

    for line in content:
        item_tup = line.split('\t')

        assert len(item_tup) == 2
        cur_item = {'freq': int(item_tup[1])}

        # 旧函数遭删减
        # assert len(item_tup) == 5
        # example = item_tup[3] if item_tup[3] != '' else None
        # cur_item = {'explanation': item_tup[1],
        #             'derivation': item_tup[2],
        #             'example': example,
        #             'freq': int(item_tup[4])}
        result.update({item_tup[0]: cur_item})
    
    return result


def chinese_word_dictionary_loader():
    """ 加载新华词典，词典中有 20 万余个多音字，分别包括：
    词语及其释义

    考虑到新华词典无法与时俱进，其中有相当多的老旧内容，故增删说明如下：
        1、删除了所有未出现在 word_distribution.json 中的词汇；
            可发现，词典由原先 26万条锐减至 3.3万条，即新华词典中大量的词条都已被淘汰，且有很多新词未加入词典。

    """
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary',
                     'chinese_word_dictionary.txt'),
        auto_loads_json=False)

    word_dict = {}
    for idx, line in enumerate(content):
        segs = line.split('\t')
        assert len(segs) == 2
        word_dict.update({segs[0]: segs[1]})

    return word_dict
    

def pornography_loader():
    """ 加载淫秽色情词典 pornography.txt """
    return read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary/pornography.txt'))
    
    
def char_radical_loader():
    """ 加载汉字字形词典 chinese_char_dictionary.txt ，字形内容包括
    偏旁部首、字形结构、四角编码、字形笔画与偏旁组成。"""

    char_dict = chinese_char_dictionary_loader()
    char_radical_dict = {}
    for char, item in char_dict.items():

        radical = item['radical']
        structure = item['structure']
        corner_coding = item['corner_coding']  # 四角编码
        stroke_order = item['stroke_order']  # 笔画顺序
        wubi_coding = item['wubi_coding']  # 五笔打字编码

        char_radical_dict.update(
            {char: {'radical': radical, 'structure': structure,
                    'corner_coding': corner_coding,
                    'stroke_order': stroke_order,
                    'wubi_coding': wubi_coding}})
        
    return char_radical_dict
    
    
def idf_loader():
    """ 加载 idf 文件，属于 tfidf 算法的一部分 """
    content = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary', 'idf.txt'),
        auto_loads_json=False)
    
    idf_dict = {}
    for item in content:
        word, idf_value = item.split('\t')
        idf_dict.update({word: float(idf_value)})
    
    return idf_dict
    
    
def traditional_simplified_loader(file_name):
    """ 加载繁简体转换词典 """
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', file_name), auto_loads_json=False)
    
    map_dict = {}
    for item in content:
        key, value = item.split('\t')
        map_dict.update({key: value})

    return map_dict


def phone_location_loader():
    """ 加载电话号码地址与运营商解析词典 """
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'phone_location.txt'),
        strip=False, auto_loads_json=False)

    def return_all_num(line):
        """ 返回所有的手机号码中间四位字符串 """
        front, info = line.strip().split('\t')
        num_string_list = info.split(',')
        result_list = []

        for num_string in num_string_list:
            if '-' in num_string:
                start_num, end_num = num_string.split('-')
                for i in range(int(start_num), int(end_num) + 1):
                    result_list.append('{:0>4d}'.format(i))
            else:
                result_list.append(num_string)

        result_list = [front + res for res in result_list]

        return result_list

    phone_location_dict = {}
    cur_location = ''
    zip_code_location_dict = {}
    area_code_location_dict = {}
    for line in content:
        if line.startswith('\t'):
            res = return_all_num(line)
            for i in res:
                phone_location_dict.update({i: cur_location})

        else:
            cur_location, area_code, zip_code = line.strip().split('\t')
            zip_code_location_dict.update({zip_code: cur_location})
            area_code_location_dict.update({area_code: cur_location})

    return phone_location_dict, zip_code_location_dict, area_code_location_dict

    
def pinyin_phrase_loader():
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'pinyin_phrase.txt'), auto_loads_json=False)
    
    map_dict = {}
    for item in content:
        key, value = item.split('\t')
        value = value.split('/')
        map_dict.update({key: value})
        
    return map_dict


def pinyin_char_loader():
    """加载拼音词典 chinese_char_dictionary.txt，以 list 返回，多音字也标出。"""

    char_dict = chinese_char_dictionary_loader()
    pinyin_char_dict = dict()
    for char, item in char_dict.items():
        pinyin_list = list(item['pinyin'].keys())
        pinyin_char_dict.update({char: pinyin_list})

    return pinyin_char_dict


def sentiment_expand_words_loader():
    """ 加载情感词典，并附带其对应的情感权重

    """
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'sentiment_expand_words.txt'))
    
    sentiment_expand_words_dict = dict()
    for item in content:
        key, value = item.split('\t')
        assert len(item.split('\t')) == 2
        
        # multi_pinyin = value.split('/')
        sentiment_expand_words_dict.update({key: float(value)})

    return sentiment_expand_words_dict


def sentiment_words_loader():
    """ 加载情感词典，并附带其对应的情感权重

    """
    content = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'sentiment_words.txt'), auto_loads_json=False)
    
    sentiment_words_dict = {}
    for item in content:
        key, value = item.split('\t')
        assert len(item.split('\t')) == 2
        
        # multi_pinyin = value.split('/')
        sentiment_words_dict.update({key: float(value)})

    return sentiment_words_dict


def telecom_operator_loader():
    """ 加载通信运营商手机号码的匹配词典
    """
    telecom_operator = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'telecom_operator.txt'))

    telecom_operator_dict = dict()
    for line in telecom_operator:
        num, operator = line.strip().split(' ')
        telecom_operator_dict.update({num: operator})

    return telecom_operator_dict


def word_distribution_loader():
    """ 加载 jiojio 分词后的词汇结果在中文文本中的词频分布，返回每个词在语料中的出现总次数、概率、
    概率的 -log10 值。

    Returns:
        dict(list): 例如
            {'国家': {'total_num': 101930,
                    'prob': 0.0014539722,
                    'log_prob': 3.2632870},
             ...}

    """
    word_info = read_file_by_line(
        os.path.join(GRAND_DIR_PATH, 'dictionary', 'word_distribution.json'))

    word_info_dict = {}
    total_num = sum([item[1] for item in word_info])
    for item in word_info:
        word_info_dict.update(
            {item[0]: {'total_num': item[1],
                       'prob': item[1] / total_num,
                       'log_prob': - math.log10(item[1] / total_num)}})

    return word_info_dict

    
def xiehouyu_loader():
    """ 加载歇后语词典，共计 17000 余条，其中有相似的歇后语，如：
    一个模子出来的  一个样
    一个模子出来的  一模一样
    对于此类歇后语，均按不同的表达分为不同的歇后语，方便检索查询
    """
    xiehouyu = read_file_by_line(os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'xiehouyu.txt'), auto_loads_json=False)
    
    xiehouyu = list(set(xiehouyu))
    xiehouyu = [item.split('\t') for item in xiehouyu]

    return xiehouyu


def llm_test_dataset_loader(version=None, field=None):
    """ 加载 llm 评测数据集，满分 100 分，每一条为一条评测题目
    客观题均为选择题，有正确答案，每一道 1 分
    主观题仅有问题，无标准答案。除机器翻译外，每一道 5 分，机器翻译每道 4 分。
    数据集说明参考：https://github.com/dongrixinyu/JioNLP/wiki/LLM%E8%AF%84%E6%B5%8B%E6%95%B0%E6%8D%AE%E9%9B%86

    Args:
        version: 测试题集的版本号，1.0，1.1 等，默认为 None，即最高版本测试题集。
        field: 指定是哪一方面的测试题，默认为 None，即全量测试题。
            目前包括 逻辑推理，field='logic', 社会伦理，field='ethics',
            数学问题，field='math'，

    Examples:
        >>> import jionlp as jio
        >>> llm_test = jio.llm_test_dataset_loader()
        >>> print(llm_test[15])

    """
    if version is None:
        version = '1.1'

    if field is None:

        version_list = ['1.0', '1.1', '1.2']
        if version not in version_list:
            raise ValueError('The given `version` parameter is wrong.')
        logging.info('LLM test dataset version: {}'.format(version))

        llm_test = read_file_by_line(
            os.path.join(GRAND_DIR_PATH,
                         'dictionary',
                         'jionlp_LLM_test',
                         'jionlp_LLM_test_{}.json'.format(version)))

        return llm_test

    elif type(field) is str and len(field) > 0:
        llm_test = read_file_by_line(
            os.path.join(GRAND_DIR_PATH, 'dictionary',
                         'jionlp_LLM_test',
                         'jionlp_{}_question.json'.format(field)))
        return llm_test
    elif field == 'coding':
        llm_test = read_file_by_line(
            os.path.join(GRAND_DIR_PATH, 'dictionary',
                         'jionlp_LLM_test', 'jionlp_coding_question.json'))
        return llm_test

def html_entities_dictionary_loader():
    """ load html entities dictionary.

    Returns: dict map

    """
    html_entities_file_path = os.path.join(
        GRAND_DIR_PATH, 'dictionary', 'html_entities.json')

    with open(html_entities_file_path, 'r', encoding='utf-8') as fw:
        html_entities_dict = json.load(fw)

    return html_entities_dict
