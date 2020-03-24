# -*- coding=utf-8 -*-

from .file_io import read_file_by_iter
from .file_io import read_file_by_line
from .file_io import write_file_by_line
#from . import trie_tree
#from .ts_conversion import TSConversion

from .dictionary_loader import china_location_loader
from .dictionary_loader import world_location_loader
from .dictionary_loader import stopwords_loader
from .dictionary_loader import chinese_idiom_loader
from .dictionary_loader import pornography_loader

from .money_standardization import MoneyStandardization
from .id_card_parser import IDCardParser
from jionlp.util.fast_loader import FastLoader


money_standardization = MoneyStandardization()
id_card_parser = IDCardParser()
#rule = FastLoader('rule', globals(), 'jionlp.rule')
del MoneyStandardization
del FastLoader
