# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestMoneyParser(unittest.TestCase):
    """ 测试金额解析工具 """

    def test_money_parser(self):
        """ test jio.parse_money """

        money_string_list = [

            # 纯数金额
            ['82，225.00元', {'num': '82225.00', 'case': '元', 'definition': 'accurate'}],
            ['25481港元', {'num': '25481.00', 'case': '港元', 'definition': 'accurate'}],
            ['45564.44美元', {'num': '45564.44', 'case': '美元', 'definition': 'accurate'}],
            ['233,333，333,434.344元', {'num': '233333333434.34', 'case': '元', 'definition': 'accurate'}],

            # 数、汉字结合金额
            ['1.2万元', {'num': '12000.00', 'case': '元', 'definition': 'accurate'}],
            ['3千万亿日元', {'num': '3000000000000000.00', 'case': '日元', 'definition': 'accurate'}],
            ['新台币 177.1 亿元', {'num': '17710000000.00', 'case': '新台币', 'definition': 'accurate'}],
            ['15k左右', {'num': '15000.00', 'case': '元', 'definition': 'blur'}],
            ['30w上下', {'num': '300000.00', 'case': '元', 'definition': 'blur'}],

            # 纯汉字金额
            ['六十四万零一百四十三元一角七分', {'num': '640143.17', 'case': '元', 'definition': 'accurate'}],
            ['壹万二千三百四十五元', {'num': '12345.00', 'case': '元', 'definition': 'accurate'}],
            ['三百万', {'num': '3000000.00', 'case': '元', 'definition': 'accurate'}],
            ['肆佰叁拾萬', {'num': '4300000.00', 'case': '元', 'definition': 'accurate'}],
            ['肆佰叁拾萬圆整', {'num': '4300000.00', 'case': '元', 'definition': 'accurate'}],
            ['肆佰叁拾萬圆', {'num': '4300000.00', 'case': '元', 'definition': 'accurate'}],
            ['二十五万三千二百泰铢', {'num': '253200.00', 'case': '泰铢', 'definition': 'accurate'}],
            ['两个亿卢布', {'num': '200000000.00', 'case': '卢布', 'definition': 'accurate'}],
            ['十块三毛', {'num': '10.30', 'case': '元', 'definition': 'accurate'}],
            ['一百三十五块六角七分钱', {'num': '135.67', 'case': '元', 'definition': 'accurate'}],
            ['港币两千九百六十元', {'num': '2960.00', 'case': '港元', 'definition': 'accurate'}],

            # 修饰词
            ['约4.287亿美元', {'num': '428700000.00', 'case': '美元', 'definition': 'blur'}],
            ['近700万元', {'num': '7000000.00', 'case': '元', 'definition': 'blur-'}],
            ['至少九千块钱以上', {'num': '9000.00', 'case': '元', 'definition': 'blur+'}],
            ['不到1.9万台币', {'num': '19000.00', 'case': '新台币', 'definition': 'blur-'}],

            # 模糊金额
            ['3000多欧元', {'num': ['3000.00', '4000.00'], 'case': '欧元', 'definition': 'blur'}],
            ['几十万块', {'num': ['100000.00', '1000000.00'], 'case': '元', 'definition': 'blur'}],
            ['人民币数十亿元', {'num': ['1000000000.00', '10000000000.00'], 'case': '元', 'definition': 'blur'}],
            ['数十亿元人民币', {'num': ['1000000000.00', '10000000000.00'], 'case': '元', 'definition': 'blur'}],
            ['十几块钱', {'num': ['10.00', '20.00'], 'case': '元', 'definition': 'blur'}],
            ['大约十多欧元', {'num': ['10.00', '20.00'], 'case': '欧元', 'definition': 'blur'}],

            # 金额范围
            ['从8500到3万港元', {'num': ['8500.00', '30000.00'], 'case': '港元', 'definition': 'blur'}],
            ['1万-5万元', {'num': ['10000.00', '50000.00'], 'case': '元', 'definition': 'blur'}],
            ['1万元--5万元', {'num': ['10000.00', '50000.00'], 'case': '元', 'definition': 'blur'}],

            # 字段补全 金额范围
            ['10~15k元', {'num': ['10000.00', '15000.00'], 'case': '元', 'definition': 'blur'}],
            ['2——3万港币', {'num': ['20000.00', '30000.00'], 'case': '港元', 'definition': 'blur'}],
            ['两到三万港元', {'num': ['20000.00', '30000.00'], 'case': '港元', 'definition': 'blur'}],
            ['十八至三十万日元', {'num': ['180000.00', '300000.00'], 'case': '日元', 'definition': 'blur'}],

            # 修饰辅助信息
            ['50万元（含）以上', {'num': '500000.00', 'case': '元', 'definition': 'blur+'}],
            ['1万(含)-5万元', {'num': ['10000.00', '50000.00'], 'case': '元', 'definition': 'blur'}],

        ]

        for item in money_string_list:
            money_res = jio.parse_money(item[0])
            print(item[0])
            self.assertEqual(money_res, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_money_parser = [TestMoneyParser('test_money_parser')]
    suite.addTests(test_money_parser)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

