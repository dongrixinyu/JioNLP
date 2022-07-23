# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestLocationParser(unittest.TestCase):
    """ 测试地址解析工具 """

    def test_location_parser(self):
        """ test func parse_location """

        location_string_list = [
            ['西湖区蒋村花园小区管局农贸市场', True, True,
             {'province': None, 'city': None, 'county': '西湖区',
              'detail': '蒋村花园小区管局农贸市场',
              'full_location': '西湖区蒋村花园小区管局农贸市场',
              'orig_location': '西湖区蒋村花园小区管局农贸市场',
              'town': None, 'village': None}],
            ['山西长治潞州区山禾路2号', False, False,
             {'province': '山西省', 'city': '长治市', 'county': '潞州区',
              'detail': '山禾路2号',
              'full_location': '山西省长治市潞州区山禾路2号',
              'orig_location': '山西长治潞州区山禾路2号'}],
            ['东兴市北仑大道59号', True, False,
             {'province': '广西壮族自治区', 'city': '防城港市', 'county': '东兴市',
              'detail': '北仑大道59号',
              'full_location': '广西壮族自治区防城港市东兴市北仑大道59号',
              'orig_location': '东兴市北仑大道59号',
              'town': None, 'village': None}
             ],
            ['北海市重庆路其仓11号', True, False,
             {'province': '广西壮族自治区', 'city': '北海市', 'county': None,
              'detail': '重庆路其仓11号',
              'full_location': '广西壮族自治区北海市重庆路其仓11号',
              'orig_location': '北海市重庆路其仓11号',
              'town': None, 'village': None}
             ],
            ['海南藏族自治州', True, False,
             {'province': '青海省', 'city': '海南藏族自治州', 'county': None,
              'detail': '', 'full_location': '青海省海南藏族自治州',
              'orig_location': '海南藏族自治州',
              'town': None, 'village': None}
             ],

        ]

        for item in location_string_list:
            time_res = jio.parse_location(
                item[0], town_village=item[1], change2new=item[2])
            print(item[0])
            self.assertEqual(time_res, item[3])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_location_parser = [TestLocationParser('test_location_parser')]
    suite.addTests(test_location_parser)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

