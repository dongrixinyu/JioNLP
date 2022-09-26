# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestMoneyExtractor(unittest.TestCase):
    """ 测试货币金额解析工具 """

    def test_money_extractor(self):
        """ test func jio.ner.extract_money """

        money_string_list = [
            ['张三赔偿李大花人民币车费601,293.11元，工厂费一万二千三百四十五元,利息9佰日元，打印费十块钱。',
             [{'text': '601,293.11元', 'offset': [12, 23], 'type': 'money'},
              {'text': '一万二千三百四十五元', 'offset': [27, 37], 'type': 'money'},
              {'text': '9佰日元', 'offset': [40, 44], 'type': 'money'},
              {'text': '十块钱', 'offset': [48, 51], 'type': 'money'}]],
            ['税额共计壹仟玖佰圆整，限月今年12月31日缴清。',
             [{'text': '壹仟玖佰圆整', 'offset': [4, 10], 'type': 'money'}]],
            ['报账金额在1 万(含)-5 万元之间的交由上级批复。',
             [{'text': '1 万(含)-5 万元', 'offset': [5, 16], 'type': 'money'}]],
            ['我们薪酬能给到10k~15k。',
             [{'text': '10k~15k', 'offset': [7, 14], 'type': 'money'}]],
            ['基站总数是10000，其中有9000台是huawei 建的，还有一台是实验品。',
             []],
            ['2.2本计划投资3541.07万元2.3本项目……',
             [{'text': '3541.07万元', 'offset': [8, 17], 'type': 'money'}]],
            ['经查，公诉机关起诉指控的被盗财物数量依照人民币被害人陈述予以认定，被告人班x庭审中提出只有两瓶津威的辩解意见，依照有利于被告人的原则，',
             []],
            ['审判长李x审判员谢x审判员周x本件与原本核对无异二○一八年七月四日书记员龚x1000011Administratorjohnny172016-09-14T14:00:00Z2017-04-27T09:24:00ZNormal.dotm2111799MicrosoftOfficeWord011falsechinafalse115falsefalse14.',
             []],
            ['刑满释放后不足一个月又犯盗窃罪，系累犯，应从重处罚。"',
             []],
            ['数额巨大或者有其他严重情节的，处三年以上十年以下有期徒刑，并处罚金；',
             []],
            ['到了次日的凌晨2许时就发现车被盗了，该车价值2000余元',
             [{'text': '2000余元', 'offset': [22, 28], 'type': 'money'}]],
            ['年末结转和结余10.56亿元。',
             [{'text': '10.56亿元', 'offset': [7, 14], 'type': 'money'}]],
        ]

        for item in money_string_list:
            moneys = jio.ner.extract_money(item[0], with_parsing=False)
            self.assertEqual(moneys, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_money_extractor = [TestMoneyExtractor('test_money_extractor')]
    suite.addTests(test_money_extractor)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

