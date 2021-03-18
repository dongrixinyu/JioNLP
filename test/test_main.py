
import unittest

from test_text_aug import TestTextAug


if __name__ == '__main__':

    suite = unittest.TestSuite()
    test_text_aug = [TestTextAug('test_ReplaceEntity')]
    suite.addTests(test_text_aug)



    runner = unittest.TextTestRunner(verbosity=1)
    runner.run(suite)



