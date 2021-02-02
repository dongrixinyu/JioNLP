# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import pdb


def _check_entity(entity):
    """ 检查实体的 text 和 offset 是否对应一致 """
    if len(entity['text']) == entity['offset'][1] - entity['offset'][0]:
        return True
    else:
        return False


def entity_compare(text, labeled_entities, predicted_entities, context_pad=10):
    """ 针对标注语料的实体，以及模型训练后预测得到的实体，往往存在不一致，找出这些标注不一
    致的数据，能够有效分析模型的预测能力。

    输入数据须为字 token 文本和实体，对应的标注实体，模型预测的实体，返回不一致的实体对。
    存在以下几种情况：
    1、标注实体存在，而模型预测实体无
    2、标注实体无，而模型预测实体存在
    3、标注实体存在，模型预测实体存在，但两者之间存在一侧或两侧偏差
        1、标注实体和多个模型预测实体存在交叠偏差
        2、模型预测实体和多个标注实体存在交叠偏差
        3、两者不存在多个偏差实体
    4、两者不存在交叠偏差，但类型不一致

    Args:
        text(str): 文本字符串或字 token 的列表
        labeled_entities: 标注语料中，标注的实体，以 entity 格式存储
        predicted_entities: 针对 text 的文本，使用模型预测得到的实体结果，以 entity 格式
            存储。
        context_pad: 需要返回有差异实体对的上下文，需指定其上下文指定长度，默认为 10

    Return:
        list: 有差异的实体对。

    Examples:
        >>> import jionlp as jio
        >>> text = '张三在西藏拉萨游玩！之后去新疆。'
        >>> labeled_entities = [
                {'text': '张三', 'offset': [0, 2], 'type': 'Person'},
                {'text': '西藏拉萨', 'offset': [3, 7], 'type': 'Location'}]
        >>> predicted_entities = [
                {'text': '张三在', 'offset': [0, 3], 'type': 'Person'},
                {'text': '西藏拉萨', 'offset': [3, 7], 'type': 'Location'},
                {'text': '新疆', 'offset': [13, 15], 'type': 'Location'}]
        >>> res = jio.ner.entity_compare(
                text, labeled_entities, predicted_entities, context_pad=1)
        >>> print(res)
            [{'context': '张三在西',
              'labeled_entity': {'text': '张三', 'offset': [0, 2], 'type': 'Person'},
              'predicted_entity': {'text': '张三在', 'offset': [0, 3], 'type': 'Person'}},
             {'context': '去新疆。',
              'labeled_entity': None,
              'predicted_entity':
                  {'text': '新疆', 'offset': [13, 15], 'type': 'Location'}}]

    """
    different_entity_pairs = list()  # 标注数据和模型预测数据里，有差异的实体对
    text_length = len(text)
    
    labeled_entities = [entity for entity in labeled_entities if _check_entity(entity)]
    predicted_entities = [entity for entity in predicted_entities if _check_entity(entity)]
    
    labeled_entities = sorted(labeled_entities, key=lambda item: item['offset'][0])
    predicted_entities = sorted(predicted_entities, key=lambda item: item['offset'][0])
    
    if labeled_entities == list():
        if predicted_entities == list():
            # 无任何标注实体
            return list()
        
        else:
            # 模型预测有实体，而标注数据无实体
            for predicted_entity in predicted_entities:
                
                context_info = text[
                    max(int(predicted_entity['offset'][0]) - context_pad, 0):
                    min(int(predicted_entity['offset'][1]) + context_pad, text_length)]
                diff_item = {'context': context_info,
                             'labeled_entity': None,
                             'predicted_entity': predicted_entity}
                different_entity_pairs.append(diff_item)
                
    else:
        if predicted_entities == list():
            # 模型预测无实体，标注数据有实体
            for labeled_entity in labeled_entities:
                
                context_info = text[
                    max(int(labeled_entity['offset'][0]) - context_pad, 0):
                    min(int(labeled_entity['offset'][1]) + context_pad, text_length)]
                diff_item = {'context': context_info,
                             'labeled_entity': labeled_entity,
                             'predicted_entity': None}
                different_entity_pairs.append(diff_item)

        else:  
            # 模型预测和标注数据均存在实体
            for labeled_entity in labeled_entities:  # 标注实体
                
                stop_flag = 0
                for predicted_entity in predicted_entities:  # 模型预测实体
                    if predicted_entity['offset'][1] <= labeled_entity['offset'][0]:
                        # 即两个实体毫无交集
                        continue
                        
                    elif predicted_entity['offset'][0] >= labeled_entity['offset'][1]:
                        # 两个实体毫无交集，但是模型预测实体的循环已经向前跳走了。
                        
                        if stop_flag == 1:
                            # 模型预测的实体和标注实体已有过交集，因此跳出循环
                            break

                        elif stop_flag == 0:
                            # 模型预测的实体和标注实体没有任何交集，直接跳过
                            
                            context_info = text[
                                max(int(labeled_entity['offset'][0]) - context_pad, 0):
                                min(int(labeled_entity['offset'][1]) + context_pad, text_length)]
                            diff_item = {'context': context_info,
                                         'labeled_entity': labeled_entity,
                                         'predicted_entity': None}
                            different_entity_pairs.append(diff_item)
                            break

                    elif predicted_entity['offset'][0] == labeled_entity['offset'][0] \
                        and predicted_entity['offset'][1] == labeled_entity['offset'][1]:
                        
                        if predicted_entity['type'] == labeled_entity['type']:
                            # 模型预测和标注的实体完全一致
                            break
                        else:
                            # 模型预测和标注的实体位置相同，但是类型不同
                            context_info = text[
                                max(int(labeled_entity['offset'][0]) - context_pad, 0):
                                min(int(labeled_entity['offset'][1]) + context_pad, text_length)]
                            diff_item = {'context': context_info,
                                         'labeled_entity': labeled_entity,
                                         'predicted_entity': predicted_entity}
                            different_entity_pairs.append(diff_item)
                            break

                    if stop_flag == 0:
                        stop_flag += 1

                    context_info = text[
                        max(min(labeled_entity['offset'][0], 
                                predicted_entity['offset'][0]) - context_pad, 0):
                        min(max(labeled_entity['offset'][1],
                                predicted_entity['offset'][1]) + context_pad,
                            text_length)]
                    diff_item = {'context': context_info,
                                 'labeled_entity': labeled_entity,
                                 'predicted_entity': predicted_entity}
                    different_entity_pairs.append(diff_item)

            # 找算法预测到，但是人工没有标注的实体
            for predicted_entity in predicted_entities:
                stop_flag = 0
                for labeled_idx, labeled_entity in enumerate(labeled_entities):
                    if predicted_entity['offset'][0] >= labeled_entity['offset'][1]:
                        # 模型预测和标注的实体毫无交集
                        if labeled_idx == len(labeled_entities) - 1:
                            # 标注集已经达到最后一个，但依然未和模型预测相交
                            context_info = text[
                                max(int(predicted_entity['offset'][0]) - context_pad, 0):
                                min(int(predicted_entity['offset'][1]) + context_pad, text_length)]
                            diff_item = {
                                'context': context_info,
                                'labeled_entity': None,
                                'predicted_entity': predicted_entity}
                            different_entity_pairs.append(diff_item)
                            
                        continue
                        
                    elif predicted_entity['offset'][1] <= labeled_entity['offset'][0]:
                        # 模型预测和标注的实体毫无交集，但标注实体循环已经跳走。
                        if stop_flag == 0:  # 没有交集
                            context_info = text[
                                max(int(predicted_entity['offset'][0]) - context_pad, 0):
                                min(int(predicted_entity['offset'][1]) + context_pad, text_length)]
                            
                            diff_item = {'context': context_info,
                                         'labeled_entity': labeled_entity,
                                         'predicted_entity': predicted_entity}
                            different_entity_pairs.append(diff_item)
                            break

                        elif stop_flag == 1:
                            # 说明有交集，不予理睬
                            break

                    if stop_flag == 0:  # 标注和模型预测的实体有交集
                        stop_flag += 1
                        
    return different_entity_pairs


if __name__ == '__main__':
    text = '张三在西藏拉萨游玩！之后去新疆。'
    labeled_entities = [
        {'text': '西藏拉萨', 'offset': [3, 7], 'type': 'Location'},
        {'text': '张三', 'offset': [0, 4], 'type': 'Person'},
        {'text': '新疆', 'offset': [13, 15], 'type': 'Location'}]
    
    predicted_entities = [
        {'text': '张三在', 'offset': [2, 15], 'type': 'Person'},
        {'text': '西藏拉萨', 'offset': [3, 7], 'type': 'Person'},
        # {'text': '新疆', 'offset': [13, 15], 'type': 'Location'},
        {'text': '。', 'offset': [15, 16], 'type': 'Location'}]
    
    res = entity_compare(
        text, labeled_entities, predicted_entities, context_pad=1)
    for i in res:
        print(i)
