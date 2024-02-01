# -*- coding=utf-8 -*-

import time
import unittest

import jionlp as jio


class TestTimeExtractor(unittest.TestCase):
    """ 测试时间解析工具 """

    def test_time_extractor(self):
        """ test jio.ner.extract_time """

        text_string_list = [
            ['大概六天后的3时1刻需要处理东西', [{'text': '六天后的3时1刻', 'offset': [2, 10], 'type': 'time_point'}]],
            ['时间定于2021年4月20日11:00时至2021年4月25日17:00时。', [{'text': '2021年4月20日11:00时至2021年4月25日17:00时', 'offset': [4, 37], 'type': 'time_span'}]],
            ['身份证号140302197706220124。', []],
            ['今年腊月18000吨物品被寄出。', [{'text': '今年腊月', 'offset': [0, 4], 'type': 'time_point'}]],
            ['腊月18，已经过了好几天。', [{'text': '腊月18', 'offset': [0, 4], 'type': 'time_point'}]],
            ['这个玩具一点都不好玩。', []],
            ['黎明主演的电影已上映。', []],
            ['一日之计在于晨...', []],
            ['有十分之一的概率，股票赔钱了。', []],
            ['住在南京网2021-09-21热度 578瞰地', [{'text': '2021-09-21', 'offset': [5, 15], 'type': 'time_point'}]],
            ['根据财税2016 36号文', [{'text': '2016', 'offset': [4, 8], 'type': 'time_span'}]],
            ['他在10月22出生', [{'text': '10月22', 'offset': [2, 7], 'type': 'time_point'}]],
            ['1月3至2月10', [{'text': '1月3至2月10', 'offset': [0, 8], 'type': 'time_span'}]],
            ['二十一', []],
            ['二十七点三', []],
            ['减八点八', []],
            ['加七点八', []],
            ['0点一', []],
            ['零点一', []],
            ['零点五', []],
            ['二十点六', []],
            ['调高二十四点五度', []],
            ['调高24点5度', []],
            ['升高10点五度', []],
        ]

        for item in text_string_list:
            time_res = jio.ner.extract_time(
                item[0], time_base=time.time(), with_parsing=False)
            print(item[0])
            self.assertEqual(time_res, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_time_extractor = [TestTimeExtractor('test_time_extractor')]
    suite.addTests(test_time_extractor)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

