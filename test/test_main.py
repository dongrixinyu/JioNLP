
import unittest

from test_text_aug import TestTextAug
from test_time_parser import TestTimeParser
from test_location_parser import TestLocationParser


if __name__ == '__main__':

    suite = unittest.TestSuite()

    tests = [
        TestTimeParser('test_time_parser'),  # 测试时间解析
        TestLocationParser('test_location_parser'),  # 测试地址解析
        TestTextAug('test_ReplaceEntity'),  # 测试实体替换增强
    ]
    suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)



