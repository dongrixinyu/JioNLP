# -*- coding=utf-8 -*-

import unittest

import jionlp as jio


class TestIdiomSolitaire(unittest.TestCase):
    """ 测试地址解析工具 """

    def test_idiom_solitaire(self):
        """ test func idiom_solitaire """

        idiom = '道阻且长'
        idiom = jio.idiom_solitaire(idiom, same_pinyin=False, same_tone=True)
        self.assertEqual(idiom[0], '长')

        idiom = jio.idiom_solitaire('', same_pinyin=False, same_tone=True)
        self.assertEqual(idiom, '')


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_idiom_solitaire = [TestIdiomSolitaire('test_idiom_solitaire')]
    suite.addTests(test_idiom_solitaire)

    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)

