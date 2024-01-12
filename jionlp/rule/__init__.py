# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com/


from .prompt import *
from .extractor import Extractor
from .checker import Checker
from .html_cleansing import CleanHTML

extractor = Extractor()

clean_text = extractor.clean_text

extract_chinese = extractor.extract_chinese
extract_email = extractor.extract_email
extract_url = extractor.extract_url
extract_phone_number = extractor.extract_phone_number
extract_ip_address = extractor.extract_ip_address
extract_id_card = extractor.extract_id_card
extract_qq = extractor.extract_qq
extract_wechat_id = extractor.extract_wechat_id
extract_parentheses = extractor.extract_parentheses
extract_motor_vehicle_licence_plate = extractor.extract_motor_vehicle_licence_plate

remove_email = extractor.remove_email
remove_url = extractor.remove_url
remove_phone_number = extractor.remove_phone_number
remove_ip_address = extractor.remove_ip_address
remove_id_card = extractor.remove_id_card
remove_qq = extractor.remove_qq
remove_parentheses = extractor.remove_parentheses
remove_html_tag = extractor.remove_html_tag
remove_exception_char = extractor.remove_exception_char
remove_redundant_char = extractor.remove_redundant_char

replace_email = extractor.replace_email
replace_url = extractor.replace_url
replace_phone_number = extractor.replace_phone_number
replace_ip_address = extractor.replace_ip_address
replace_id_card = extractor.replace_id_card
replace_qq = extractor.replace_qq
replace_chinese = extractor.replace_chinese

del extractor

checker = Checker()

check_any_chinese_char = checker.check_any_chinese_char
check_all_chinese_char = checker.check_all_chinese_char
check_any_arabic_num = checker.check_any_arabic_num
check_all_arabic_num = checker.check_all_arabic_num

clean_html = CleanHTML()
