# -*- coding=utf-8 -*-


__version__ = '1.1.0'

import os

from jionlp.util.logger import set_logger


logging = set_logger('INFO')


guide = """
╭─────────────────────────────────────────────────────────────────────────╮
│ ◎ ○ ○ ░░░░░░░░░░░░░░░░░░░░░  Important Message  ░░░░░░░░░░░░░░░░░░░░░░░░│
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│              We renamed again for consistency and clarity.              │
│                   From now on, it is all `kashgari`.                    │
│  Changelog: https://github.com/BrikerMan/Kashgari/releases/tag/v1.0.0   │
│                                                                         │
│         | Backend          | pypi version   | desc           |          │
│         | ---------------- | -------------- | -------------- |          │
│         | TensorFlow 2.x   | kashgari 2.x.x | coming soon    |          │
│         | TensorFlow 1.14+ | kashgari 1.x.x |                |          │
│         | Keras            | kashgari 0.x.x | legacy version |          │
│                                                                         │
╰─────────────────────────────────────────────────────────────────────────╯
"""



from jionlp.util import *
from jionlp.dictionary import *
from jionlp.rule import *
from jionlp.gadget import *
from jionlp.algorithm import *
#from jionlp import rule
#from jionlp import gadget
#from jionlp import util
#from jionlp import algorithm
#from jionlp import dictionary

from jionlp.util.fast_loader import FastLoader


#rule = FastLoader('rule', globals(), 'jionlp.rule')









