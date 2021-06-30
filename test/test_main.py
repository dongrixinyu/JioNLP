
import unittest

from test_text_aug import TestTextAug
from test_time_parser import TestTimeParser


if __name__ == '__main__':

    suite = unittest.TestSuite()

    tests = [
        TestTimeParser('test_time_parser'),  # 测试时间解析
        TestTextAug('test_ReplaceEntity'),  # 测试实体替换增强
    ]
    suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)



