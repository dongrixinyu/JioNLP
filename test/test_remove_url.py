# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestRemoveUrl(unittest.TestCase):
    """ 测试清除 url 工具 """

    def test_remove_url(self):
        """ test func remove_url """

        url_text_list = [
            ['抖音知识分享 https://v.douyin.com/RtKFFah/ 复制Ci鏈接，打开Dou音搜索，直接观看視頻',
             '抖音知识分享  复制Ci鏈接，打开Dou音搜索，直接观看視頻'],
            ['抖音知识分享https://v.douyin.com/RtKFFah/复制Ci鏈接，打开Dou音搜索，直接观看視頻',
             '抖音知识分享复制Ci鏈接，打开Dou音搜索，直接观看視頻'],
            ['这是一个链接https://fb.watch/o2JPlWrxYr/?mibextid=cr9u03"',
             '这是一个链接"']
        ]

        for item in url_text_list:
            clean_text = jio.remove_url(item[0])
            print(item[0])
            self.assertEqual(clean_text, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_remove_url = [TestRemoveUrl('test_remove_url')]
    suite.addTests(test_remove_url)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

