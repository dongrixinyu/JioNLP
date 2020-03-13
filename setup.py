# -*- coding=utf-8 -*-

import os

from setuptools import setup, find_packages


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
LONGDOC = '''
jionlp
================================================================================

面向公司算法和使用部门提供算法api接口

安装方法：
代码使用 Python 3 

-   半自动安装：
    $ git clone http://git.bbdops.com/BBD-AI-Lab/BBD-Tools-Documentation.git
    $ cd BBD-Tools-Documentation
    $ pip install .
-   通过 import bbd_tools as bbd 来引用

'''

__name__ = 'jionlp'
__author__ = "cuiguoer"
__copyright__ = "Copyright 2020, dongrixinyu"
__credits__ = []
__license__ = "Apache License 2.0"
__maintainer__ = "dongrixinyu"
__email__ = "dongrixinyu.89@163.com"

__url__ = 'https://github.com/dongrixinyu/jionlp'
__description__ = 'Simple, Keras-powered multilingual NLP framework,' \
                  ' allows you to build your models in 5 minutes for named entity recognition (NER),' \
                  ' part-of-speech tagging (PoS) and text classification tasks. ' \
                  'Includes BERT, GPT-2 and word2vec embedding.'



with open(os.path.join(DIR_PATH, 'requirements.txt'), 
          'r', encoding='utf-8') as f:
    requirements = f.readlines()

setup(name=__name__,
      version='0.1.0',
      url=__url__,
      author=__author__,
      author_email=__email__,
      description=__description__,
      long_description=LONGDOC,
      license=__license__,
      py_modules=[],
      packages=find_packages(),
      include_package_data=True,
      install_requires=requirements,
      entry_points={
          'console_scripts': [
              # 'scheduler_start = algorithm_platform.scheduler.server: start',
          ]
      },
      test_suite='nose.collector',
      tests_require=['nose'])

