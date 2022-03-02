
import unittest

from test_text_aug import TestTextAug
from test_time_parser import TestTimeParser
from test_location_parser import TestLocationParser
from test_idiom_solitaire import TestIdiomSolitaire
from test_money_parser import TestMoneyParser
from test_time_extractor import TestTimeExtractor
from test_money_extractor import TestMoneyExtractor
from test_remove_url import TestRemoveUrl
from test_remove_email import TestRemoveEmail
from test_remove_phone_number import TestRemovePhoneNumber


if __name__ == '__main__':

    suite = unittest.TestSuite()

    tests = [
        TestTimeParser('test_time_parser'),  # 测试 时间解析
        TestLocationParser('test_location_parser'),  # 测试 地址解析
        TestTextAug('test_ReplaceEntity'),  # 测试 实体替换增强
        TestIdiomSolitaire('test_idiom_solitaire'),  # 测试 成语接龙
        TestMoneyParser('test_money_parser'),  # 测试 金额抽取与规范化
        TestTimeExtractor('test_time_extractor'),  # 测试 时间实体抽取
        TestMoneyExtractor('test_money_extractor'),  # 测试 货币金额实体抽取
        TestRemoveUrl('test_remove_url'),  # 测试 清洗文本中的超链接
        TestRemoveEmail('test_remove_email'),  # 测试 清洗文本中的 email
        TestRemovePhoneNumber('test_remove_phone_number')  # 测试 清洗文本中的电话号码
    ]

    suite.addTests(tests)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)



