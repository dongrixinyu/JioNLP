# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestRemoveEmail(unittest.TestCase):
    """ 测试清除 email 工具 """

    def test_remove_email(self):
        """ test func remove_email """

        email_text_list = [
            ['Beihang University E-mail 给她打电话啊 Email:  dongrixinyu.89@163.com ， 中国ffewfqr23.f@gmail.com。',
             'Beihang University E-mail 给她打电话啊  ， 中国。'],
            ['xxx@xxx.COM.................................................',
             '.................................................'],
        ]

        for item in email_text_list:
            clean_text = jio.remove_email(item[0], delete_prefix=True)
            print(item[0])
            self.assertEqual(clean_text, item[1])


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_remove_email = [TestRemoveEmail('test_remove_email')]
    suite.addTests(test_remove_email)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

