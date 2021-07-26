# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import re
import pdb

from .rule_pattern import *


__all__ = ['Extractor']


class Extractor(object):
    """ 规则抽取器 """
    def __init__(self):
        self.money_pattern = None
        self.email_pattern = None
        self.email_domain_pattern = None
        self.url_pattern = None
        self.phone_number_pattern = None
        self.ip_address_pattern = None
        self.id_card_pattern = None
        self.html_tag_pattern = None
        self.qq_pattern = None
        self.strict_qq_pattern = None
        self.cell_phone_pattern = None
        self.landline_phone_pattern = None
        self.extract_parentheses_pattern = None
        self.remove_parentheses_pattern = None
        self.parentheses_pattern = PARENTHESES_PATTERN
        self.parentheses_dict = None
        self.redundant_pattern = None
        self.exception_pattern = None
        self.full_angle_pattern = None
        self.chinese_char_pattern = None

    @staticmethod
    def _extract_base(pattern, text, with_offset=False):
        """ 正则抽取器的基础函数

        Args:
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （抽取内容字段在文本中的位置信息）

        Returns:
            list: 返回结果

        """
        if with_offset:
            '''
            if pattern == self.strict_qq_pattern:
                for item in pattern.finditer(text):
                    pdb.set_trace()
                pdb.set_trace()
            #'''
            results = [{'text': item.group(1), 
                        'offset': (item.span()[0] - 1, item.span()[1] - 1)}
                      for item in pattern.finditer(text)]
        else:
            results = [item.group(1) for item in pattern.finditer(text)]
        
        return results

    def remove_redundant_char(self, text):
        """去除冗余字符

        Args:
            text: 待处理文本

        Returns:
            正则pattern

        """
        if self.redundant_pattern is None:
            pattern_list = list()
            for char in REDUNDANT_PATTERN:
                pattern_tmp = '(?<={char}){char}+'.format(
                    char=re.escape(char))
                pattern_list.append(pattern_tmp)
            
            redundant_pattern = '|'.join(pattern_list)
            self.redundant_pattern = re.compile(redundant_pattern)
            
        return self.redundant_pattern.sub('', text)

    def clean_text(self, text, remove_html_tag=True,
                   convert_full2half=True,
                   remove_exception_char=True, remove_url=True,
                   remove_redundant_char=True, remove_parentheses=True,
                   remove_email=True, remove_phone_number=True):
        """ 清洗文本

        Args:
            text(str): 待清理文本
            remove_html_tag(bool): 是否删除html标签，如 <span> 等
            remove_exception_char(bool): 是否删除异常字符，如“敩衞趑”等
            convert_full2half(bool): 是否将全角字符转换为半角
            remove_redundant_char(bool): 是否删除冗余字符，如“\n\n\n”，修剪为“\n”
            remove_parentheses(bool): 是否删除括号及括号内内容，如“（记者：小丽）”
            remove_url(bool): 是否删除 url 链接
            remove_email(bool): 是否删除 email
            remove_phone_number(bool): 是否删除电话号码

        Returns:
            str: 清理后的文本

        """
        
        if remove_html_tag:
            text = self.remove_html_tag(text)
        if remove_exception_char:
            text = self.remove_exception_char(text)
        if convert_full2half:
            text = self.convert_full2half(text)
        if remove_redundant_char:
            text = self.remove_redundant_char(text)
        if remove_parentheses:
            text = self.remove_parentheses(text)
        if remove_url:
            text = self.remove_url(text)
        if remove_email:
            text = self.remove_email(text)
        if remove_phone_number:
            text = self.remove_phone_number(text)

        return text
        
    def convert_full2half(self, text):
        """ 将全角字符转换为半角字符
        其中分为空格字符和非空格字符
        """
        if self.full_angle_pattern is None:
            self.full_angle_pattern = re.compile(FULL_ANGLE_ALPHABET)
        
        final_text_list = list()
        cursor = 0
        for item in self.full_angle_pattern.finditer(text):
            # 补充前段字符串
            if item.span()[0] == 0:
                pass
            else:
                final_text_list.append(text[cursor: item.span()[0]])
                
            # 替换
            for char in item.group():
                if char == '\u3000':  # 全角空格直接替换
                    final_text_list.append(' ')
                else:
                    final_text_list.append(chr(ord(char) - 65248))
            cursor = item.span()[1]  
            
        if len(text) > cursor:  # 补充最后的字符串
            final_text_list.append(text[cursor:])
        
        return ''.join(final_text_list)
        
    def extract_email(self, text, detail=False):
        """ 提取文本中的 E-mail

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （E-mail 在文本中的位置信息）

        Returns:
            list: email列表

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
            
        text = ''.join(['#', text, '#'])
        results = self._extract_base(self.email_pattern, text, 
                                     with_offset=detail)
        if not detail:
            return results
        else:
            if self.email_domain_pattern is None:
                self.email_domain_pattern = re.compile(EMAIL_DOMAIN_PATTERN)
                
            detail_results = list()
            for item in results:
                domain_name = self.email_domain_pattern.search(
                    item['text']).group(1)
                item.update({'domain_name': domain_name})
                detail_results.append(item)
            return detail_results
            
    def extract_id_card(self, text, detail=False):
        """ 提取文本中的 ID 身份证号

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （身份证在文本中的位置信息）

        Returns:
            list: 身份证信息列表

        """
        if self.id_card_pattern is None:
            self.id_card_pattern = re.compile(ID_CARD_PATTERN)

        text = ''.join(['#', text, '#'])
        return self._extract_base(self.id_card_pattern, text, 
                                  with_offset=detail)
        
    def extract_ip_address(self, text, detail=False):
        """ 提取文本中的 IP 地址

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （IP 地址在文本中的位置信息）

        Returns:
            list: IP 地址列表

        """
        if self.ip_address_pattern is None:
            self.ip_address_pattern = re.compile(IP_ADDRESS_PATTERN)
        
        text = ''.join(['#', text, '#'])
        return self._extract_base(self.ip_address_pattern, text, 
                                  with_offset=detail)
    
    def extract_money(self, text):
        """从文本中抽取出金额字符串，可以和 money_standardization 函数配合使用，
        得到数字金额

        Args:
            text(str): 字符串文本

        Returns:
            list: email列表

        """
        if self.money_pattern is None:
            self.money_pattern = re.compile(MONEY_PATTERN)
            
        res = list()
        for item in self.money_pattern.finditer(text):
            # print(item.group())
            res.append(item.group())
        
        return res
    
    def extract_phone_number(self, text, detail=False):
        """从文本中抽取出电话号码

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （电话号码在文本中的位置信息）

        Returns:
            list: 电话号码列表

        """
        if self.cell_phone_pattern is None:
            self.cell_phone_pattern = re.compile(CELL_PHONE_PATTERN)
            
        if self.landline_phone_pattern is None:
            self.landline_phone_pattern = re.compile(LANDLINE_PHONE_PATTERN)
            
        text = ''.join(['#', text, '#'])
        cell_results = self._extract_base(
            self.cell_phone_pattern, text, with_offset=detail)
        landline_results = self._extract_base(
            self.landline_phone_pattern, text, with_offset=detail)
        
        if not detail:
            return cell_results + landline_results
        else:
            detail_results = list()
            for item in cell_results:
                item.update({'type': 'cell_phone'})
                detail_results.append(item)
            for item in landline_results:
                item.update({'type': 'landline_phone'})
                detail_results.append(item)
            return detail_results
        
    def extract_qq(self, text, detail=False, strict=True):
        """从文本中抽取出 QQ 号码

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （QQ 在文本中的位置信息）
            strict(bool): QQ号很容易和其他数字混淆，因此选择采用严格或宽松规则匹配

        Returns:
            list: email列表

        """
        if self.qq_pattern is None:
            self.qq_pattern = re.compile(QQ_PATTERN)
            self.strict_qq_pattern = re.compile(STRICT_QQ_PATTERN)
        
        text = ''.join(['#', text, '#'])
        tmp_res = self._extract_base(
            self.qq_pattern, text, with_offset=detail)
        
        if not strict:
            return tmp_res
        else:
            # 将无法匹配 qq 字符的 qq 号删除
            match_flag = self.strict_qq_pattern.search(text)
            if match_flag:
                return tmp_res
            else:
                return list()
    
    def extract_url(self, text, detail=False):
        """提取文本中的url链接

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （URL 在文本中的位置信息）

        Returns:
            list: url列表

        """
        if self.url_pattern is None:
            self.url_pattern = re.compile(URL_PATTERN)
        text = ''.join(['￥', text, '￥'])  # 因 # 可出现于 url
        
        return self._extract_base(self.url_pattern, text, 
                                  with_offset=detail)

    def _extract_parentheses(self, text, parentheses=PARENTHESES_PATTERN):
        # 额外分支 Ghs 提供的方法
        if self.extract_parentheses_pattern is None or self.parentheses_pattern != parentheses:
            import regex as reg
            self.parentheses_pattern = parentheses
            parentheses_per = zip(self.parentheses_pattern[:-1], self.parentheses_pattern[1:])
            self.extract_parentheses_pattern = f"(?:{'|'.join('{left}([^{left}{right}]*){right}'.format(left=reg.escape(f), right=reg.escape(e)) for f, e in parentheses_per)})"

        return [{'context': [j for j in i.groups() if j][0], 'offset': i.span(), 'origin': i.group()}
                for i in reg.compile(self.extract_parentheses_pattern).finditer(text)]

    def extract_parentheses(self, text, parentheses=PARENTHESES_PATTERN, detail=False):
        """ 提取文本中的括号及括号内内容，当有括号嵌套时，提取每一对
        成对的括号的内容

        Args:
            text(str): 字符串文本
            parentheses: 要删除的括号类型，格式为:
                '左括号1右括号1左括号2右括号2...'，必须为成对的括号如'{}()[]'，
                默认为self.parentheses
            detail: 是否打印括号内容位置信息

        Returns:
            list: [
                    {
                        'context'(str): 'the context between parentheses',
                        'offset'(tuple): 'the location of extracted text'
                    },  # 当 detail 为 True 时
                    'the context between parentheses',  # 当 detail 为 False 时
                    ...
                ]

        """
        if self.extract_parentheses_pattern is None or self.parentheses_pattern != parentheses:
            self.parentheses_pattern = parentheses

            extract_pattern = '[' + re.escape(self.parentheses_pattern) + ']'
            extract_pattern = re.compile(extract_pattern)
            
            p_length = len(self.parentheses_pattern)

            parentheses_dict = dict()
            for i in range(0, p_length, 2):
                value = self.parentheses_pattern[i]
                key = self.parentheses_pattern[i + 1]
                parentheses_dict.update({key: value})
            
            self.parentheses_dict = parentheses_dict
            self.extract_parentheses_pattern = extract_pattern

        content_list = list()
        parentheses_list = list()
        idx_list = list()
        finditer = self.extract_parentheses_pattern.finditer(text)
        for i in finditer:
            idx = i.start()
            parentheses = text[idx]

            if parentheses in self.parentheses_dict.keys():
                if len(parentheses_list) > 0:
                    if parentheses_list[-1] == self.parentheses_dict[parentheses]:
                        parentheses_list.pop()
                        if detail:
                            start_idx = idx_list.pop()
                            end_idx = idx + 1
                            content_list.append(
                                {'content': text[start_idx: end_idx],
                                 'offset': (start_idx, end_idx)})
                        else:
                            content_list.append(text[idx_list.pop(): idx + 1])
            else:
                parentheses_list.append(parentheses)
                idx_list.append(idx)
                
        return content_list

    def remove_email(self, text):
        """ 删除文本中的 email

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除 email 后的文本

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
            
        text = ''.join(['#', text, '#'])
        return self.email_pattern.sub('', text)[1:-1]

    def remove_exception_char(self, text):
        """ 删除文本中的异常字符

        Args:
            text(str): 字符串文本

        Returns:
             str: 删除异常字符后的文本
        """
        if self.exception_pattern is None:
            self.exception_pattern = re.compile(EXCEPTION_PATTERN)
        
        return self.exception_pattern.sub(' ', text)

    def remove_html_tag(self, text):
        """ 删除文本中的 html 标签

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除 html 标签后的文本

        """
        if self.html_tag_pattern is None:
            self.html_tag_pattern = re.compile(HTML_TAG_PATTERN)
        return re.sub(self.html_tag_pattern, '', text)
    
    def remove_id_card(self, text):
        """ 删除文本中的身份证号

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除身份证 id 后的文本

        """
        if self.id_card_pattern is None:
            self.id_card_pattern = re.compile(ID_CARD_PATTERN)
            
        text = ''.join(['#', text, '#'])
        return self.id_card_pattern.sub('', text)[1:-1]
    
    def remove_ip_address(self, text):
        """ 删除文本中的 ip 地址

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除 ip 地址后的文本

        """
        if self.ip_address_pattern is None:
            self.ip_address_pattern = re.compile(IP_ADDRESS_PATTERN)
            
        text = ''.join(['#', text, '#'])
        return self.ip_address_pattern.sub('', text)[1:-1]
    
    def remove_parentheses(self, text, parentheses=PARENTHESES_PATTERN):
        """ 删除文本中的括号及括号内内容

        Args:
            text(str): 字符串文本
            parentheses: 要删除的括号类型，格式为:
                '左括号1右括号1左括号2右括号2...'，必须为成对的括号如'{}()[]'，
                默认为self.parentheses

        Returns:
            str: 删除括号及括号中内容后的文本

        """
        if self.remove_parentheses_pattern is None or self.parentheses_pattern != parentheses:
            self.parentheses_pattern = parentheses

            p_length = len(self.parentheses_pattern)
            remove_pattern_list = list()
            remove_pattern_format = '{left}[^{left}{right}]*{right}'
            
            for i in range(0, p_length, 2):
                left = re.escape(self.parentheses_pattern[i])
                right = re.escape(self.parentheses_pattern[i + 1])
                remove_pattern_list.append(
                    remove_pattern_format.format(left=left, right=right))
                
            remove_pattern = '|'.join(remove_pattern_list)
            remove_pattern = re.compile(remove_pattern)

            self.remove_parentheses_pattern = remove_pattern

        length = len(text)
        while True:
            text = self.remove_parentheses_pattern.sub('', text)
            if len(text) == length:
                return text
            length = len(text)

    def remove_phone_number(self, text):
        """ 删除文本中的电话号码

        Args:
            text(str): 字符串文本

        Returns:
            str: 删除电话号码后的文本

        """
        if self.cell_phone_pattern is None:
            self.cell_phone_pattern = re.compile(CELL_PHONE_PATTERN)
            
        if self.landline_phone_pattern is None:
            self.landline_phone_pattern = re.compile(LANDLINE_PHONE_PATTERN)
        
        text = ''.join(['#', text, '#'])
        text = self.cell_phone_pattern.sub('', text)
        text = self.landline_phone_pattern.sub('', text)
        
        return text[1:-1]
    
    def remove_qq(self, text, strict=True):
        """ 删除文本中的电 QQ 号

        Args:
            text(str): 字符串文本
            strict(bool): QQ 号容易与其他数字混淆，因此选择严格规则或宽松规则

        Returns:
            str: 删除 QQ 后的文本

        """
        if self.qq_pattern is None:
            self.qq_pattern = re.compile(QQ_PATTERN)
            self.strict_qq_pattern = re.compile(STRICT_QQ_PATTERN) 

        if strict:
            # 将无法匹配 qq 字符的文本直接返回
            match_flag = self.strict_qq_pattern.search(text)
            if not match_flag:
                return text
        
        text = ''.join(['#', text, '#'])
        return self.qq_pattern.sub('', text)[1:-1]
    
    def remove_url(self, text):
        """ 删除文本中的 url 链接

        Args:
            text(str): 字符串文本

        Returns:
            text: 删除 url 链接后的文本

        """
        if self.url_pattern is None:
            self.url_pattern = re.compile(URL_PATTERN)
            
        text = ''.join(['￥', text, '￥'])
        return self.url_pattern.sub('', text)[1:-1]

    def replace_chinese(self, text):
        """ 删除文本中的所有中文字符串

        将中文文字，替换为空格

        """
        if text == '':
            return []
        if self.chinese_char_pattern is None:
            self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)
        
        text_without_chinese = self.chinese_char_pattern.sub(r' ', text)
        return text_without_chinese

        # {'phone': '18100065143', 'province': '上海', 'city': '上海',
        # 'zip_code': '200000', 'area_code': '021', 'phone_type': '电信'}

    def check_chinese_char(self, text):
        """ 检查文本中是否包含中文字符 """
        if text == '':
            return False
        if self.chinese_char_pattern is None:
            self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)

        if self.chinese_char_pattern.search(text):
            return True

        return False

