
import unittest

from test_text_aug import TestTextAug
from test_time_parser import TestTimeParser


if __name__ == '__main__':

    suite = unittest.TestSuite()
    # 测试实体替换增强
    test_text_aug = [TestTextAug('test_ReplaceEntity')]
    suite.addTests(test_text_aug)

    # 测试时间解析
    test_time_parser = [TestTimeParser('test_time_parser')]
    suite.addTests(test_time_parser)


    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)



