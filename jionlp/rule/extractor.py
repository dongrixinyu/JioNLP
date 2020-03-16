# -*- coding=utf-8 -*-

import os
import re
import pdb

from .rule_pattern import *
from itertools import groupby


__all__ = ['extract_email', 'replace_chinese', 'extract_cellphone', 
           'extract_url', 'extract_phone_number', 
           'extract_cellphone_location', 'extract_money', 'get_location',
           'extract_locations', 'remove_email', 'remove_url',
           'remove_phone_number',
           'replace_cellphoneNum', 'extract_time', 'extract_name', 'most_common']


class Extractor(object):
    ''' 规则抽取器 '''
    def __init__(self):
        self.money_pattern = None
        self.email_pattern = None
        self.url_pattern = None
        self.phone_number_pattern = None
        self.ip_address_pattern = None
        self.id_card_pattern = None
        self.html_tag_pattern = None

    @staticmethod
    def _extract_base(pattern, text, with_offset=False):
        '''正则抽取器的基础函数
        
        Args:
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （抽取内容字段在文本中的位置信息）

        Returns:
            list: 返回结果
        
        '''
        if with_offset:
            results = [{'text': item.group(), 'offset': item.span()} 
                      for item in pattern.finditer(text)]
        else:
            results = [item.group() for item in pattern.finditer(text)]
        return results

    @staticmethod
    def _gen_redundant_char_ptn(redundant_char):
        """生成 redundant_char 的正则 pattern

        Args:
            redundant_char: 冗余字符集

        Returns:
            正则pattern

        """
        pattern_list = []
        for char in redundant_char:
            pattern_tmp = '(?<={char}){char}+'.format(char=re.escape(char))
            # pattern_tmp = re.escape(char) + '{2,}'
            pattern_list.append(pattern_tmp)
        pattern = '|'.join(pattern_list)
        pattern = re.compile(pattern)
        return pattern

    def clean_text(self, text, detect_utf8=False, remove_html_tag=True,
                   remove_exception_char=True, remove_url=True,
                   remove_redundant_char=True, remove_parentheses=True,
                   remove_emails=True, remove_phone_number=True,
                   convert_full_width=True, truncate_footer=True):
        """清洗文本

        Args:
            text(str): 待清理文本
            detect_utf8(bool): 是否检测文本编码，默认为按 utf8 编码
            remove_html_tag(bool): 是否删除html标签，如 <span> 等
            remove_exception_char(bool): 是否删除异常字符，如“敩衞趑”等
            remove_redundant_char(bool): 是否删除冗余字符，如“\n\n\n”，修剪为“\n”
            remove_parentheses(bool): 是否删除括号及括号内内容，如“（记者：小丽）”
            remove_url(bool): 是否删除url链接
            remove_emails(bool): 是否删除email
            remove_phone_number(bool): 是否删除电话号码

        Returns:
            str: 清理后的文本

        """
        if detect_utf8:
            if not self.detect_utf8(text):
                return ''
        
        if remove_html_tag:
            text = self.remove_html_tag(text)
        if remove_exception_char:
            text = self.remove_exception_char(text)
        if remove_redundant_char:
            text = self.remove_redundant_char(text)
        if remove_parentheses:
            text = self.remove_parentheses(text)
        if remove_url:
            text = self.remove_url(text)
        if remove_emails:
            text = self.remove_emails(text)
        if remove_phone_number:
            text = self.remove_phone_number(text)

        return text
        
    def extract_email(self, text, with_offset=False):
        """提取文本中的 E-mail

        Args:
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （E-mail 在文本中的位置信息）

        Returns:
            list: email列表

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
        return self._extract_base(self.email_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_id_card(self, text, with_offset=False):
        """提取文本中的 ID 身份证号

        Args:
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （E-mail 在文本中的位置信息）

        Returns:
            list: email列表

        """
        if self.id_card_pattern is None:
            self.id_card_pattern = re.compile(ID_CARD_PATTERN)
        return self._extract_base(self.id_card_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_ip_address(self, text, with_offset=False):
        """提取文本中的 IP 地址

        Args:
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （E-mail 在文本中的位置信息）

        Returns:
            list: email列表

        """
        if self.ip_address_pattern is None:
            self.ip_address_pattern = re.compile(IP_ADDRESS_PATTERN)
        return self._extract_base(self.ip_address_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_money(self, text, with_offset=False):
        """从文本中抽取出金额字符串，可以和 turn_money_std_fmt 函数配合使用，
        得到数字金额

        Args:
            text(str): 字符串文本

        Returns:
            list: email列表

        """
        if self.money_pattern is None:
            self.money_pattern = re.compile(MONEY_PATTERN)
        return self._extract_base(self.money_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_phone_number(self, text, with_offset=False):
        """从文本中抽取出电话号码

        Args:
            text(str): 字符串文本

        Returns:
            list: email列表

        """
        if self.phone_number_pattern is None:
            self.phone_number_pattern = re.compile(PHONE_NUMBER_PATTERN)
        return self._extract_base(self.phone_number_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_qq(self, text, with_offset=False):
        """从文本中抽取出 QQ 号码

        Args:
            text(str): 字符串文本

        Returns:
            list: email列表

        """
        if self.qq_pattern is None:
            self.qq_pattern = re.compile(QQ_PATTERN)
        return self._extract_base(self.qq_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_url(self, text):
        """提取文本中的url链接

        Args:
            text(str): 字符串文本

        Returns:
            list: url列表

        """
        if self.url_pattern is None:
            self.url_pattern = re.compile(URL_PATTERN)
        return self._extract_base(self.url_pattern, text, 
                                  with_offset=with_offset)
    
    def extract_parentheses(self, text, parentheses=None):
        """提取文本中的括号及括号内内容，当有括号嵌套时，提取每一对
        成对的括号的内容

        Args:
            text(str): 字符串文本
            parentheses: 要删除的括号类型，格式为:
            '左括号1右括号1左括号2右括号2...'，必须为成对的括号如'{}()[]'，
            默认为self.parentheses

        Returns:
            list: 括号内容列表

        """
        if parentheses is not None:
            if parentheses != self.parentheses:
                self.update_parentheses_ptn(parentheses)
        content_list = []
        parentheses_list = []
        idx_list = []
        finditer = self.extract_parentheses_ptn.finditer(text)
        for i in finditer:
            idx = i.start()
            parenthesis = text[idx]
            if parenthesis in self.parenthesis_dict.keys():
                if len(parentheses_list) > 0:
                    if parentheses_list[-1] == self.parenthesis_dict[parenthesis]:
                        parentheses_list.pop()
                        content_list.append(text[idx_list.pop():idx + 1])
            else:
                parentheses_list.append(parenthesis)
                idx_list.append(idx)
        return content_list

    def remove_email(self, text):
        """删除文本中的email

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除email后的文本

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
        return self.email_pattern.sub('', text)
    
    def detect_exception_char(self, text):
        """检测异常字符

        Args:
            text(str): 字符串文本

        Returns:
            list: 异常字符列表
        """
        return self.exception_char_ptn.findall(text)

    def remove_exception_char(self, text):
        """删除文本中的异常字符

        Args:
            text(str): 字符串文本

        Returns:
             str: 删除异常字符后的文本
        """
        return self.exception_char_ptn.sub('', text)

    def remove_html_tag(self, text):
        """删除文本中的html标签

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除html标签后的文本

        """
        if self.html_tag_pattern is None:
            self.html_tag_pattern = re.compile(HTML_TAG_PATTERN)
        return re.sub(self.html_tag_ptn, '', text)
    
    def remove_id_card(self, text):
        """删除文本中的email

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除email后的文本

        """
        if self.id_card_pattern is None:
            self.id_card_pattern = re.compile(ID_CARD_PATTERN)
        return self.id_card_pattern.sub('', text)
    
    def remove_ip_address(self, text):
        """删除文本中的email

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除email后的文本

        """
        if self.ip_address_pattern is None:
            self.ip_address_pattern = re.compile(IP_ADDRESS_PATTERN)
        return self.ip_address_pattern.sub('', text)
    
    def remove_parentheses(self, text, parentheses=None):
        """删除文本中的括号及括号内内容

        Args:
            text(str): 字符串文本
            parentheses: 要删除的括号类型，格式为:
            '左括号1右括号1左括号2右括号2...'，必须为成对的括号如'{}()[]'，
            默认为self.parentheses

        Returns:
            str: 删除括号及括号中内容后的文本
        """
        if parentheses is not None:
            if parentheses != self.parentheses:
                self.update_parentheses_ptn(parentheses)
        length = len(text)
        while True:
            text = self.remove_parentheses_ptn.sub('', text)
            if len(text) == length:
                return text
            length = len(text)

    def remove_phone_number(self, text):
        """删除文本中的电话号码

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除email后的文本

        """
        if self.phone_number_pattern is None:
            self.phone_number_pattern = re.compile(PHONE_NUMBER_PATTERN)
        return self.phone_number_pattern.sub('', text)
    
    def remove_qq(self, text):
        """删除文本中的电话号码

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除email后的文本

        """
        if self.qq_pattern is None:
            self.qq_pattern = re.compile(QQ_PATTERN)
        return self.qq_pattern.sub('', text)
    
    def remove_redundant_char(self, text, redundant_char=None):
        """删除文本中的冗余字符，当出现连续多个同一字符时，仅保留一个字符

        Args:
            text(str): 字符串文本
            redundant_char(str): 冗余字符集，默认为self.redundant_char

        Returns:
            str: 删除冗余字符后文本

        Examples:
            >>> text = '张三在   --成都'
            >>> print(bbs.remove_redundant_char(text, ' -'))
            张三在 -成都
        """
        if redundant_char is not None:
            if redundant_char != self.redundant_char:
                self.redundant_char_ptn = self._gen_redundant_char_ptn(redundant_char)
                self.redundant_char = redundant_char
        return self.redundant_char_ptn.sub('', text)
    
    def remove_url(self, text):
        """删除文本中的url链接

        Args:
            text(str): 字符串文本

        Returns:
            text: 删除url链接后的文本

        """
        if self.url_pattern is None:
            self.url_pattern = re.compile(URL_PATTERN)
        return self.url_pattern.sub('', text)
    
        
    def replace_chinese(self, text):
        """
        remove all the chinese characters in text
        eg: replace_chinese('我的email是ifee@baidu.com和dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: text_without_chinese<str>
        """
        if text=='':
            return []
        if self.chinese_char_pattern is None:
            self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)
        
        text_without_chinese = self.chinese_char_pattern.sub(r' ', text)
        return text_without_chinese




class extractor():
    def __init__(self):
        pass

    def extract_email(self, text):
        """
        extract all email addresses from texts<string>
        eg: extract_email('我的email是ifee@baidu.com和dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: email_addresses_list<list>
        """
        if text=='':
            return []
        eng_texts = self.replace_chinese(text)
        eng_texts = eng_texts.replace(' at ','@').replace(' dot ','.')
        sep = ',!?:; ，。！？《》、|\\/'
        pdb.set_trace()
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]

        email_pattern = r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z_-]+)+$'

        emails = []
        for eng_text in eng_split_texts:
            result = re.match(email_pattern, eng_text, flags=0)
            if result:
                emails.append(result.string)
        pdb.set_trace()
        return emails

    def extract_ids(self, text):
        """
        extract all ids from texts<string>
        eg: extract_ids('my ids is 150404198812011101 m and dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: ids_list<list>
        """
        if text == '':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele) == 18]

        id_pattern = r'^[1-9][0-7]\d{4}((19\d{2}(0[13-9]|1[012])(0[1-9]|[12]\d|30))|(19\d{2}(0[13578]|1[02])31)|(19\d{2}02(0[1-9]|1\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\d{3}(\d|X|x)?$'

        phones = []
        for eng_text in eng_split_texts_clean:
            result = re.match(id_pattern, eng_text, flags=0)
            if result:
                phones.append(result.string.replace('+86','').replace('-',''))
        return phones

    def replace_chinese(self, text):
        """
        remove all the chinese characters in text
        eg: replace_chinese('我的email是ifee@baidu.com和dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: text_without_chinese<str>
        """
        if text=='':
            return []
        filtrate = re.compile(u'[\u4E00-\u9FA5]')
        text_without_chinese = filtrate.sub(r' ', text)
        return text_without_chinese

    def extract_cellphone(self, text, nation):
        """
        extract all cell phone numbers from texts<string>
        eg: extract_email('my email address is sldisd@baidu.com and dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: email_addresses_list<list>
        """
        if text=='':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        if nation=='CHN':
            phone_pattern = r'^((\+86)?([- ])?)?(|(13[0-9])|(14[0-9])|(15[0-9])|(17[0-9])|(18[0-9])|(19[0-9]))([- ])?\d{3}([- ])?\d{4}([- ])?\d{4}$'

        phones = []
        for eng_text in eng_split_texts_clean:
            result = re.match(phone_pattern, eng_text, flags=0)
            if result:
                phones.append(result.string.replace('+86','').replace('-',''))
        return phones

    def extract_cellphone_location(self, phoneNum, nation='CHN'):
        """
        extract cellphone number locations according to the given number
        eg: extract_cellphone_location('181000765143',nation=CHN)
        :param: phoneNum<string>, nation<string>
        :return: location<dict>{'phone': '18100065143', 'province': '上海', 'city': '上海', 'zip_code': '200000', 'area_code': '021', 'phone_type': '电信'}
        """
        if nation=='CHN':
            p = Phone()
            loc_dict = p.find(phoneNum)
        if nation!='CHN':
            x = phonenumbers.parse(phoneNum, 'GB')
            if phonenumbers.is_possible_number(x):
                loc_dict = x
        # print(loc_dict)
        return loc_dict

    def get_location(self, word_pos_list):
        """
        get location by the pos of the word, such as 'ns'
        eg: get_location('内蒙古赤峰市松山区')
        :param: word_pos_list<list>
        :return: location_list<list> eg: ['陕西省安康市汉滨区', '安康市汉滨区', '汉滨区']
        """
        location_list = []
        if word_pos_list==[]:
            return []

        for i,t in enumerate(word_pos_list):
            word = t[0]
            nature = t[1]
            if nature == 'ns':
                loc_tmp = word
                count = i + 1
                while count < len(word_pos_list):
                    next_word_pos = word_pos_list[count]
                    next_pos = next_word_pos[1]
                    next_word = next_word_pos[0]
                    if next_pos=='ns' or 'n' == next_pos[0]:
                        loc_tmp += next_word
                    else:
                        break
                    count += 1
                location_list.append(loc_tmp)

        return location_list # max(location_list)

    def extract_locations(self, text):
        """
        extract locations by from texts
        eg: extract_locations('我家住在陕西省安康市汉滨区。')
        :param: raw_text<string>
        :return: location_list<list> eg: ['陕西省安康市汉滨区', '安康市汉滨区', '汉滨区']
        """
        if text=='':
            return []
        seg_list = [(str(t.word), str(t.nature)) for t in HanLP.segment(text)]
        location_list = self.get_location(seg_list)
        return location_list

    def replace_cellphoneNum(self, text):
        """
        remove cellphone number from texts. If text contains cellphone No., the extract_time will report errors.
        hence, we remove it here.
        eg: extract_locations('我家住在陕西省安康市汉滨区，我的手机号是181-0006-5143。')
        :param: raw_text<string>
        :return: text_without_cellphone<string> eg: '我家住在陕西省安康市汉滨区，我的手机号是。'
        """
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        for phone_num in eng_split_texts_clean:
            text = text.replace(phone_num,'')
        return text

    def replace_ids(self, text):
        """
        remove cellphone number from texts. If text contains cellphone No., the extract_time will report errors.
        hence, we remove it here.
        eg: extract_locations('我家住在陕西省安康市汉滨区，我的身份证号是150404198412011312。')
        :param: raw_text<string>
        :return: text_without_ids<string> eg: '我家住在陕西省安康市汉滨区，我的身份证号号是。'
        """
        if text == '':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele) == 18]

        id_pattern = r'^[1-9][0-7]\d{4}((19\d{2}(0[13-9]|1[012])(0[1-9]|[12]\d|30))|(19\d{2}(0[13578]|1[02])31)|(19\d{2}02(0[1-9]|1\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\d{3}(\d|X|x)?$'
        ids = []
        for eng_text in eng_split_texts_clean:
            result = re.match(id_pattern, eng_text, flags=0)
            if result:
                ids.append(result.string)

        for phone_num in ids:
            text = text.replace(phone_num,'')
        return text

    def extract_time(self, text):
        """
        extract timestamp from texts
        eg: extract_time('我于2018年1月1日获得1000万美金奖励。')
        :param: raw_text<string>
        :return: time_info<time_dict> eg: {"type": "timestamp", "timestamp": "2018-11-27 11:00:00"}
        """
        if text=='':
            return []
        tmp_text = self.replace_cellphoneNum(text)
        tmp_text = self.replace_ids(tmp_text)
        tn = TimeNormalizer()
        res = tn.parse(target=tmp_text)  # target为待分析语句，timeBase为基准时间默认是当前时间
        return res

    def extract_name(self, text):
        """
        extract chinese names from texts
        eg: extract_time('急寻王龙，短发，王龙，男，丢失发型短发，...如有线索，请迅速与警方联系：19909156745')
        :param: raw_text<string>
        :return: name_list<list> eg: ['王龙', '王龙']
        """
        if text=='':
            return []
        seg_list = [(str(t.word), str(t.nature)) for t in HanLP.segment(text)]
        names = []
        for ele_tup in seg_list:
            if 'nr' in ele_tup[1]:
                names.append(ele_tup[0])
                # print(ele_tup[0],ele_tup[1])
        return self.most_common(names)

    def most_common(self, content_list):
        """
        return the most common element in a list
        eg: extract_time(['王龙'，'王龙'，'李二狗'])
        :param: content_list<list>
        :return: name<string> eg: '王龙'
        """
        if content_list==[]:
            return None
        if len(content_list)==0:
            return None
        return max(set(content_list), key=content_list.count)





if __name__ == '__main__':

    text = '急寻特朗普，男孩，于2018年11月27号11时在陕西省安康市汉滨区走失。丢失发型短发，...如有线索，请迅速与警方联系：18100065143，132-6156-2938，baizhantang@sina.com.cn 和yangyangfuture at gmail dot com'
    ex = extractor()

    emails = ex.extract_email(text)
    cellphones = ex.extract_cellphone(text, nation='CHN')
    cell_loc = []
    for cell in cellphones:
        cell_loc.append(ex.extract_cellphone_location(cell, 'CHN'))

    locations = ex.extract_locations(text)
    times = ex.extract_time(text)
    names = ex.extract_name(text)

    result_dict = {}
    result_dict['email'] = emails
    result_dict['cellphone'] = cellphones
    result_dict['cellphone_location'] = cell_loc
    result_dict['location'] = locations
    result_dict['time'] = times
    result_dict['name'] = names
    for key in result_dict.keys():
        print(key,result_dict[key])























