# -*- coding=utf-8 -*-

import os
import re

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
__version__ = ''
with open(os.path.join(DIR_PATH, 'README.md'),
          'r', encoding='utf-8') as f:
    readme_lines = f.readlines()
    version_pattern = re.compile('badge/version-(\d\.\d+\.\d+)-')
    for line in readme_lines:
        result = version_pattern.search(line)
        if result is not None:
            __version__ = result.group(1)

    LONGDOC = '\n'.join(readme_lines)

__name__ = 'jionlp'
__author__ = "dongrixinyu"
__copyright__ = "Copyright 2020, dongrixinyu"
__credits__ = []
__license__ = "Apache License 2.0"
__maintainer__ = "dongrixinyu"
__email__ = "dongrixinyu.89@163.com"
__url__ = 'https://github.com/dongrixinyu/JioNLP'
__description__ = 'Preprocessing tool for Chinese NLP'


with open(os.path.join(DIR_PATH, 'requirements.txt'), 
          'r', encoding='utf-8') as f:
    requirements = f.readlines()


setup(name=__name__,
      version=__version__,
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
              'jio_help = jionlp.util:help',
          ]
      },
      test_suite='nose.collector',
      tests_require=['nose'])

