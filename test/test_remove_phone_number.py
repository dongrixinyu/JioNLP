# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestRemovePhoneNumber(unittest.TestCase):
    """ 测试清除 phone_number 工具 """

    def test_remove_phone_number(self):
        """ test func remove_phone_number """

        phone_number_text_list = [
            [' 电话：(010)37283893 他手机号多少？18702812943. 还有一个是17209374283    ffewfqr23.f@163.com联系电话： （0351）89082910',
             '  他手机号多少？. 还有一个是    ffewfqr23.f@163.com'],
        ]

        for item in phone_number_text_list:
            clean_text = jio.remove_phone_number(item[0], delete_prefix=True)
            print(item[0])
            self.assertEqual(clean_text, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_remove_phone_number = [TestRemovePhoneNumber('test_remove_phone_number')]
    suite.addTests(test_remove_phone_number)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

