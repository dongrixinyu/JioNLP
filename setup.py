# -*- coding=utf-8 -*-

import os

from setuptools import setup, find_packages


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
LONGDOC = '''
==================================== JioNLP ====================================

一个全面简便的中文 NLP 工具包，做您的 NLP 任务的垫 jio 石。提供丰富的 NLP 功能。

安装：
```
$ git clone https://github.com/dongrixinyu/JioNLP
$ cd ./JioNLP
$ pip install .
```

导入：
```
>>> import jionlp as jio
```
'''
with open(os.path.join(DIR_PATH, 'README.md'),
          'r', encoding='utf-8') as f:
    LONGDOC = f.read()

__name__ = 'jionlp'
__author__ = "cuiguoer"
__copyright__ = "Copyright 2020, dongrixinyu"
__credits__ = []
__license__ = "Apache License 2.0"
__maintainer__ = "dongrixinyu"
__email__ = "dongrixinyu.89@163.com"
__url__ = 'https://github.com/dongrixinyu/JioNLP'
__description__ = ''#LONGDOC.split('安装：\n```')[0]



with open(os.path.join(DIR_PATH, 'requirements.txt'), 
          'r', encoding='utf-8') as f:
    requirements = f.readlines()

setup(name=__name__,
      version='1.3.2',
      url=__url__,
      author=__author__,
      author_email=__email__,
      description=__description__,
      long_description=LONGDOC,
      long_description_content_type='text/markdown',
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

