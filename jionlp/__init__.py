# -*- coding=utf-8 -*-


__version__ = '1.1.0'

import os

from jionlp.util.logger import set_logger


logging = set_logger('INFO')


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









