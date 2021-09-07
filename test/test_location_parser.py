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

