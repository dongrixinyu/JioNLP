# -*- coding=utf-8 -*-
"""
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP
"""

import os
import re

from setuptools import setup, find_packages


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
LONG_DOC = '''
==================================== JioNLP ====================================

中文 NLP 数据预处理工具包，完成训练 NLP 模型前后的数据预处理，如文本数据增强、文本清洗、特定
信息抽取、数据集概况分析、模型加速、相关模型任务 baseline、词典等。

# 安装：
    $ git clone https://github.com/dongrixinyu/JioNLP
    $ cd ./JioNLP
    $ pip install .

# 导入：
    >>> import jionlp as jio

'''
__version__ = ''

with open(os.path.join(DIR_PATH, 'README.md'),
          'r', encoding='utf-8') as f:
    readme_lines = f.readlines()
    version_pattern = re.compile('badge/version-(\d\.\d+\.\d+)-')
    for line in readme_lines:
        result = version_pattern.search(line)
        if result is not None:
            __version__ = result.group(1)

    LONG_DOC = '\n'.join(readme_lines)

__name__ = 'jionlp'
__author__ = "dongrixinyu"
__copyright__ = "Copyright 2020, dongrixinyu"
__credits__ = list()
__license__ = "Apache License 2.0"
__maintainer__ = "dongrixinyu"
__email__ = "dongrixinyu.89@163.com"
__url__ = 'https://github.com/dongrixinyu/JioNLP'
__description__ = 'Chinese NLP Preprocessing & Parsing'


with open(os.path.join(DIR_PATH, 'requirements.txt'), 
          'r', encoding='utf-8') as f:
    requirements = f.readlines()


setup(name=__name__,
      version=__version__,
      url=__url__,
      author=__author__,
      author_email=__email__,
      description=__description__,
      long_description=LONG_DOC,
      long_description_content_type='text/markdown',
      license=__license__,
      py_modules=list(),
      packages=find_packages(),
      include_package_data=True,
      install_requires=requirements,
      entry_points={
          'console_scripts': [
              'jio_help = jionlp.util:help',
          ]
      },
      test_suite='nose.collector',
      tests_require=['nose'])
