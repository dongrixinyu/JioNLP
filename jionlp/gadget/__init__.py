# -*- coding=utf-8 -*-

#from . import trie_tree
#from .ts_conversion import TSConversion

from .money_standardization import MoneyStandardization
from .split_sentence import SplitSentence
from .id_card_parser import IDCardParser
from .location_parser import LocationParser
from jionlp.util.fast_loader import FastLoader


money_standardization = MoneyStandardization()
id_card_parser = IDCardParser()
split_sentence = SplitSentence()
location_parser = LocationParser()


#rule = FastLoader('rule', globals(), 'jionlp.rule')
del MoneyStandardization
del FastLoader
