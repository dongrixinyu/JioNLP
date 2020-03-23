# -*- coding=utf-8 -*-

#from bbd_nlp_apis.gadget import gadget
#from .gadget import read_file_by_line
from .file_io import read_file_by_line
from .file_io import write_file_by_line
from . import trie_tree
from . import ts_conversion 

from .dictionary_loader import china_location_loader
from .dictionary_loader import world_location_loader
from .dictionary_loader import stopwords_loader
from .dictionary_loader import chinese_idiom_loader
from .dictionary_loader import pornography_loader

from .money_standardization import 

from jionlp.util.fast_loader import FastLoader


#rule = FastLoader('rule', globals(), 'jionlp.rule')
del FastLoader
