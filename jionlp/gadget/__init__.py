# -*- coding=utf-8 -*-

#from . import trie_tree
#from .ts_conversion import TSConversion

from .money_standardization import MoneyStandardization
from .id_card_parser import IDCardParser
from jionlp.util.fast_loader import FastLoader


money_standardization = MoneyStandardization()
id_card_parser = IDCardParser()
#rule = FastLoader('rule', globals(), 'jionlp.rule')
del MoneyStandardization
del FastLoader
