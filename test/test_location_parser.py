# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestLocationParser(unittest.TestCase):
    """ 测试地址解析工具 """

    def test_location_parser(self):
        """ test func parse_location """

        location_string_list = [
            ['河北区', True, True,
             {'province': '天津市', 'city': '天津市', 'county': '河北区',
              'detail': '', 'full_location': '天津市河北区',
              'orig_location': '河北区', 'town': None, 'village': None}],
            ['湘潭城塘社区', True, True,
             {'province': '湖南省', 'city': '湘潭市', 'county': None,
              'detail': '城塘社区', 'full_location': '湖南省湘潭市城塘社区',
              'orig_location': '湘潭城塘社区', 'town': None, 'village': None}],
            ['湘潭县城塘社区', True, True,
             {'province': '湖南省', 'city': '湘潭市', 'county': '湘潭县',
              'detail': '城塘社区', 'full_location': '湖南省湘潭市湘潭县城塘社区',
              'orig_location': '湘潭县城塘社区', 'town': None, 'village': None}],
            ['云南省红河哈尼族彝族自治州元阳县黄茅岭乡', True, True,
             {'province': '云南省', 'city': '红河哈尼族彝族自治州', 'county': '元阳县',
              'detail': '黄茅岭乡',
              'full_location': '云南省红河哈尼族彝族自治州元阳县黄茅岭乡',
              'orig_location': '云南省红河哈尼族彝族自治州元阳县黄茅岭乡',
              'town': '黄茅岭乡', 'village': None}],
            # 省、市同名
            ['吉林省吉林市小皇村', True, True,
             {'province': '吉林省', 'city': '吉林市', 'county': None,
              'detail': '小皇村', 'full_location': '吉林省吉林市小皇村',
              'orig_location': '吉林省吉林市小皇村',
              'town': None, 'village': None}],
            ['重庆解放碑', True, True,
             {'province': '重庆市', 'city': '重庆市', 'county': None,
              'detail': '解放碑', 'full_location': '重庆市解放碑',
              'orig_location': '重庆解放碑', 'town': None, 'village': None}],
            # 市、县同名，仅出现一个，仅匹配市
            ['湖南湘潭城塘社区', True, True,
             {'province': '湖南省', 'city': '湘潭市', 'county': None,
              'detail': '城塘社区', 'full_location': '湖南省湘潭市城塘社区',
              'orig_location': '湖南湘潭城塘社区',
              'town': None, 'village': None}],
            # 市、县同名，同时出现
            ['湖南湘潭市湘潭县城塘社区', True, True,
             {'province': '湖南省', 'city': '湘潭市', 'county': '湘潭县',
              'detail': '城塘社区', 'full_location': '湖南省湘潭市湘潭县城塘社区',
              'orig_location': '湖南湘潭市湘潭县城塘社区',
              'town': None, 'village': None}],
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

