# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from .money_standardization import MoneyStandardization
from .money_num2char import MoneyNum2Char
from .split_sentence import SplitSentence
from .id_card_parser import IDCardParser
from .location_parser import LocationParser
from .location_recognizer import LocationRecognizer
from .lunar_solar_date import LunarSolarDate
from .time_parser import TimeParser
from .remove_stopwords import RemoveStopwords
from .ts_conversion import TSConversion
from .pinyin import Pinyin
from .char_radical import CharRadical
from .phone_location import PhoneLocation
from .idiom_solitaire import IdiomSolitaire
from jionlp.util.fast_loader import FastLoader


money_standardization = MoneyStandardization()
money_num2char = MoneyNum2Char()
parse_id_card = IDCardParser()
split_sentence = SplitSentence()
parse_location = LocationParser()
recognize_location = LocationRecognizer()
remove_stopwords = RemoveStopwords()
tra_sim_conversion = TSConversion()
tra2sim = tra_sim_conversion.tra2sim
sim2tra = tra_sim_conversion.sim2tra
pinyin = Pinyin()
idiom_solitaire = IdiomSolitaire()
char_radical = CharRadical()
phone_location = PhoneLocation()
cell_phone_location = phone_location.cell_phone_location
landline_phone_location = phone_location.landline_phone_location
lunar_solar_date = LunarSolarDate()
lunar2solar = lunar_solar_date.to_solar_date
solar2lunar = lunar_solar_date.to_lunar_date
parse_time = TimeParser()

# rule = FastLoader('rule', globals(), 'jionlp.rule')
del tra_sim_conversion
# del FastLoader
