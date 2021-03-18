

import unittest

import jionlp as jio


class TestTextAug(unittest.TestCase):
    """ 测试文本数据增强工具 """

    def test_ReplaceEntity(self):
        """ test class ReplaceEntity """

        # 准备的词典
        entities_dict = {
            "Person": {"马成宇": 1},
            "Company": {"百度": 4, "国力教育公司": 1},
            "Organization": {"延平区人民法院": 1}
        }
        # 输入的序列标注样本
        text = '腾讯致力于解决冲突，阿里巴巴致力于玩。小马爱玩。'
        entities = [{'type': 'Company', 'text': '腾讯', 'offset': (0, 2)},
                    {'type': 'Company', 'text': '阿里巴巴', 'offset': (10, 14)},
                    {'type': 'Person', 'text': '小马', 'offset': (19, 21)}]
        replace_entity = jio.ReplaceEntity(entities_dict)
        texts, entities = replace_entity(text, entities)

        # 预期结果
        standard_texts = ['腾讯致力于解决冲突，国力教育公司致力于玩。小马爱玩。',
                          '百度致力于解决冲突，阿里巴巴致力于玩。小马爱玩。',
                          '腾讯致力于解决冲突，阿里巴巴致力于玩。马成宇爱玩。']
        standard_entities = [
            [{'type': 'Company', 'text': '腾讯', 'offset': (0, 2)},
             {'text': '国力教育公司', 'type': 'Company', 'offset': [10, 16]},
             {'text': '小马', 'type': 'Person', 'offset': (21, 23)}],
            [{'text': '百度', 'type': 'Company', 'offset': [0, 2]},
             {'text': '阿里巴巴', 'type': 'Company', 'offset': (10, 14)},
             {'text': '小马', 'type': 'Person', 'offset': (19, 21)}],
            [{'type': 'Company', 'text': '腾讯', 'offset': (0, 2)},
             {'type': 'Company', 'text': '阿里巴巴', 'offset': (10, 14)},
             {'text': '马成宇', 'type': 'Person', 'offset': [19, 22]}]]

        self.assertEqual(texts, standard_texts)
        self.assertEqual(entities, standard_entities)

    # def test_





