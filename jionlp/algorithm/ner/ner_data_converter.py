# -*- coding=utf-8 -*-
#

# NER 数据集有两种存储格式
# 默认采用的标注标准为 BIOES 

import json
from typing import Dict, Any, Tuple, Optional, List

from jionlp import logging


__all__ = ['entity2tag', 'tag2entity']


def entity2tag(token_list: List, entities: List[Dict[str, Any]], 
               formater='BIOES'):
    ''' 将实体 entity 格式转为 tag 格式，若标注过程中有重叠标注，则会自动将靠后的
    实体忽略、删除。
    
    Args:
        ner_entities(List[str, Dict[str, Any]]): 文本以及相应的实体。
        formater(str): 选择的标注标准
    return:
        List[List[str], List[str]]: tag 格式的数据
        
    Examples:
        >>> ner_entities = [
                '胡静静在水利局工作。', 
                {'text': '胡静静', 'offset': [0, 3], 'type': 'Person'},
                {'text': '水利局', 'offset': [4, 7], 'type': 'Orgnization'}]]
        >>> print(entity2tag(ner_entities))
            [['胡', '静', '静', '在', '水', '利', '局', '工', '作', '。'],
             ['B-Person', 'I-Person', 'E-Person', 'O', 'B-Orgnization',
             'I-Orgnization', 'E-Orgnization', 'O', 'O', 'O']]
             
    '''
    tags = ['O' for i in range(len(token_list))]
    
    flag = 0  # 判断重叠标注

    for idx, entity in enumerate(entities):
        if entity['offsets'][1] < flag:  # 说明重叠标注，要删除
            if 1 < idx + 1 < len(entities):
                logging.warning(
                    'The entity {} is overlapped with {}.'.format(
                        json.dumps(entity, ensure_ascii=False),
                        json.dumps(entities[idx - 1], ensure_ascii=False)))
            
        else:
            if entity['offsets'][1] - entity['offsets'][0] == 1:
                tags[entity['offsets'][0]] = 'S-' + entity['type']
            else:
                tags[entity['offsets'][0]] = 'B-' + entity['type']
                if entity['offsets'][1] - entity['offsets'][0] > 2:
                    for j in range(entity['offsets'][0] + 1,
                                   entity['offsets'][1] - 1):
                        tags[j] = 'I-' + entity['type']
                tags[entity['offsets'][1] - 1] = 'E-' + entity['type']
            flag = entity['offsets'][1]

    return tags
    
    
    
    
    
def tag2entity():
    ''' 将 tag 格式转为实体 entity 格式 '''
    
    
    
    
    
    


