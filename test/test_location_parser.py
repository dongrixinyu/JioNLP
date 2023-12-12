# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestLocationParser(unittest.TestCase):
    """ 测试地址解析工具 """

    def test_location_parser(self):
        """ test func parse_location """

        location_string_list = [
            ['柳州地区忻城县', False, True,
             {'province': '广西壮族自治区', 'city': '来宾市', 'county': '忻城县', 'detail': '', 'full_location': '广西壮族自治区来宾市忻城县',
              'orig_location': '柳州地区忻城县'}
             ],
            ['湖北省襄樊市小水街222号', False, True,
             {'province': '湖北省', 'city': '襄阳市', 'county': None,
              'detail': '小水街222号', 'full_location': '湖北省襄阳市小水街222号',
              'orig_location': '湖北省襄樊市小水街222号'}
             ],
            ['老河口市天气', True, True,
             {'province': '湖北省', 'city': '襄阳市', 'county': '老河口市',
              'detail': '天气', 'full_location': '湖北省襄阳市老河口市天气',
              'orig_location': '老河口市天气', 'town': None, 'village': None}
             ],
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
            # 市、县重名,
            ['西安交通大学', True, False,
             {'province': '陕西省', 'city': '西安市', 'county': None, 'detail': '交通大学', 'full_location': '陕西省西安市交通大学',
              'orig_location': '西安交通大学', 'town': None, 'village': None}
             ],  # 此例会和 “吉林省通辽市西安区” 混淆
            ['河北省秦皇岛市经济技术开发区', True, False,
             {'province': '河北省', 'city': '秦皇岛市', 'county': '经济技术开发区',
              'detail': '', 'full_location': '河北省秦皇岛市经济技术开发区',
              'orig_location': '河北省秦皇岛市经济技术开发区',
              'town': None, 'village': None}
             ],
            ['江西南昌市新建区松湖镇江西省南昌市新建区松湖镇松湖中心小学', True, True,
             {'province': '江西省', 'city': '南昌市', 'county': '新建区',
              'detail': '松湖镇江西省南昌市新建区松湖镇松湖中心小学',
              'full_location': '江西省南昌市新建区松湖镇江西省南昌市新建区松湖镇松湖中心小学',
              'orig_location': '江西南昌市新建区松湖镇江西省南昌市新建区松湖镇松湖中心小学',
              'town': '松湖镇', 'village': None}
             ],
            ['湖南省长沙市', True, False,
             {'province': '湖南省', 'city': '长沙市', 'county': None,
              'detail': '', 'full_location': '湖南省长沙市',
              'orig_location': '湖南省长沙市', 'town': None, 'village': None}
             ],
            ['香港九龙半岛清水湾香港科技大学', False, False,
             {'province': '香港特别行政区', 'city': '香港', 'county': '九龙城区',
              'detail': '半岛清水湾香港科技大学',
              'full_location': '香港特别行政区九龙城区半岛清水湾香港科技大学',
              'orig_location': '香港九龙半岛清水湾香港科技大学'}
             ]
        ]

        for item in location_string_list:
            loc_res = jio.parse_location(
                item[0], town_village=item[1], change2new=item[2])
            print(item[0])
            # print(time_res)
            self.assertEqual(loc_res, item[3])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_location_parser = [TestLocationParser('test_location_parser')]
    suite.addTests(test_location_parser)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

