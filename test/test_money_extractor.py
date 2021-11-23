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

