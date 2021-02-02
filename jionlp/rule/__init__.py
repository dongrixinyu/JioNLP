# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from .extractor import Extractor


extractor = Extractor()

clean_text = extractor.clean_text

extract_email = extractor.extract_email
extract_money = extractor.extract_money
extract_url = extractor.extract_url
extract_phone_number = extractor.extract_phone_number
extract_ip_address = extractor.extract_ip_address
extract_id_card = extractor.extract_id_card
extract_qq = extractor.extract_qq
extract_parentheses = extractor.extract_parentheses

remove_email = extractor.remove_email
remove_url = extractor.remove_url
remove_phone_number = extractor.remove_phone_number
remove_ip_address = extractor.remove_ip_address
remove_id_card = extractor.remove_id_card
remove_qq = extractor.remove_qq
remove_parentheses = extractor.remove_parentheses
remove_html_tag = extractor.remove_html_tag
remove_exception_char = extractor.remove_exception_char

check_chinese_char = extractor.check_chinese_char

del extractor
