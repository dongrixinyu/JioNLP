# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re

from .rule_pattern import *


__all__ = ['Extractor']


class Extractor(object):
    """ 规则抽取器 """
    def __init__(self):
        self.money_pattern = None
        self.email_pattern = None
        self.email_domain_pattern = None
        self.email_prefix_pattern = None
        self.url_pattern = None
        self.phone_number_pattern = None
        self.ip_address_pattern = None
        self.id_card_pattern = None
        self.html_tag_pattern = None
        self.qq_pattern = None
        self.strict_qq_pattern = None
        self.wechat_id_pattern = None
        self.strict_wechat_id_pattern = None
        self.cell_phone_pattern = None
        self.landline_phone_pattern = None
        self.phone_prefix_pattern = None
        self.extract_parentheses_pattern = None
        self.remove_parentheses_pattern = None
        self.parentheses_pattern = PARENTHESES_PATTERN
        self.parentheses_dict = None
        self.redundant_pattern = None
        self.exception_pattern = None
        self.full_angle_pattern = None
        self.chinese_char_pattern = None
        self.chinese_chars_pattern = None
        self.motor_vehicle_licence_plate_pattern = None

    @staticmethod
    def _extract_base(pattern, text, with_offset=False):
        """ 正则抽取器的基础函数

        Args:
            pattern(re.compile): 正则表达式对象
            text(str): 字符串文本
            with_offset(bool): 是否携带 offset （抽取内容字段在文本中的位置信息）

        Returns:
            list: 返回结果

        """
        if with_offset:
            results = [{'text': item.group(1), 
                        'offset': (item.span()[0] - 1, item.span()[1] - 1)}
                       for item in pattern.finditer(text)]
        else:
            results = [item.group(1) for item in pattern.finditer(text)]
        
        return results

    def remove_redundant_char(self, text, redundant_chars=None):
        """去除冗余字符

        Args:
            text(str): 待处理文本
            redundant_chars(str|list): 自定义待去除的冗余字符串 或 list，
                如 ”哈嗯~“，或 ['哈', '嗯', '\u3000']，若不指定则采用默认的冗余字符串。

        Returns:
            删除冗余字符后的文本

        """
        if self.redundant_pattern is None:
            pattern_list = list()
            if redundant_chars is None:
                redundant_chars = REDUNDANT_PATTERN

            for char in redundant_chars:
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
                   remove_email=True, remove_phone_number=True,
                   delete_prefix=False, redundant_chars=None):
        """ 清洗文本，关键字参数均默认为 True

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
            delete_prefix(bool): 是否删除 email 和 电话号码的前缀，如 `E-mail: xxxx@gmail.com`
            redundant_chars(str|list|None): 自定义待去除的冗余字符串 或 list，
                如 ”哈嗯~“，或 ['哈', '嗯', '\u3000']，若不指定则采用默认的冗余字符串。

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
            text = self.remove_redundant_char(
                text, redundant_chars=redundant_chars)
        if remove_parentheses:
            text = self.remove_parentheses(text)
        if remove_url:
            text = self.remove_url(text)
        if remove_email:
            text = self.remove_email(text, delete_prefix=delete_prefix)
        if remove_phone_number:
            text = self.remove_phone_number(text, delete_prefix=delete_prefix)

        return text

    def convert_full2half(self, text):
        """ 将全角字符转换为半角字符
        其中分为空格字符和非空格字符
        """
        if self.full_angle_pattern is None:
            self.full_angle_pattern = str.maketrans(FULL_ANGLE_ALPHABET, HALF_ANGLE_ALPHABET)

        return text.translate(self.full_angle_pattern)

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
            
        text = ''.join(['龥', text, '龥'])
        results = self._extract_base(self.email_pattern, text, 
                                     with_offset=detail)
        if not detail:
            return results
        else:
            if self.email_domain_pattern is None:
                self.email_domain_pattern = re.compile(EMAIL_DOMAIN_PATTERN)
                
            detail_results = []
            for item in results:
                domain_name = self.email_domain_pattern.search(item['text']).group(1)
                item.update({'domain_name': domain_name})
                detail_results.append(item)
            return detail_results

    def extract_motor_vehicle_licence_plate(self, text, detail=False):
        """ 提取文本中的机动车牌号

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （机动车牌号在文本中的位置信息）

        Returns:
            list: 机动车牌号信息列表

        """
        if self.motor_vehicle_licence_plate_pattern is None:
            self.motor_vehicle_licence_plate_pattern = re.compile(
                MOTOR_VEHICLE_LICENCE_PLATE_PATTERN)

        text = ''.join(['#', text, '#'])
        return self._extract_base(
            self.motor_vehicle_licence_plate_pattern, text,
            with_offset=detail)

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
            detail_results = []
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
            list: QQ 号列表

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
                return []

    def extract_wechat_id(self, text, detail=False, strict=True):
        """从文本中抽取出 微信号 号码

        微信官方定义的微信号规则：

        1、可使用6-20个字母、数字、下划线和减号；
        2、必须以字母开头（字母不区分大小写）；
        3、不支持设置中文。

        Args:
            text(str): 字符串文本
            detail(bool): 是否携带 offset （微信号 在文本中的位置信息）
            strict(bool): 微信号 很容易和其他数字混淆，因此选择采用严格或宽松规则匹配

        Returns:
            list: 微信号 列表

        """
        if self.wechat_id_pattern is None:
            self.wechat_id_pattern = re.compile(WECHAT_ID_PATTERN)
            self.strict_wechat_id_pattern = re.compile(STRICT_WECHAT_ID_PATTERN)

        text = ''.join(['#', text, '#'])
        tmp_res = self._extract_base(
            self.wechat_id_pattern, text, with_offset=True)

        if not strict:
            return tmp_res
        else:
            # 将无法匹配 微信号 字符的 微信号 删除
            # 注意该规则未经充分的数据验证，仅凭启发式规则定义而成。
            final_res = []
            for item in tmp_res:
                end_offset = item['offset'][0]
                start_offset = max(0, end_offset - 8)  # 此处的考察范围 8 为一个默认值
                match_flag = self.strict_wechat_id_pattern.search(
                    text[start_offset: end_offset])

                if match_flag:
                    if detail:
                        final_res.append(item)
                    else:
                        final_res.append(item['text'])

            return final_res

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

        content_list = []
        parentheses_list = []
        idx_list = []
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

    def remove_email(self, text, delete_prefix=False):
        """ 删除文本中的 email

        Args:
            text(str): 字符串文本
            delete_prefix(bool): 删除电子邮箱前的前缀符，如 `E-mail: xxxx@163.com`
                由于计算前缀符的匹配，该方法计算效率会慢。

        Returns:
            str: 删除 email 后的文本

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
            self.email_prefix_pattern = re.compile(EMAIL_PREFIX_PATTERN, re.I)

        text = ''.join(['龥', text, '龥'])
        if not delete_prefix:
            text = self.email_pattern.sub('', text)
            return text[1:-1]

        else:
            results = self._extract_base(self.email_pattern, text, with_offset=True)
            prefix_results = self._extract_base(self.email_prefix_pattern, text, with_offset=True)

            offset_list = [item['offset'][0] for item in results]

            clean_prefix_offsets = [
                item['offset'] for item in prefix_results if item['offset'][1] in offset_list]

            final_text_list = []
            for idx, item in enumerate(clean_prefix_offsets):
                if idx == 0:
                    final_text_list.append(text[0: item[0]+1])

                if idx == len(clean_prefix_offsets) - 1:
                    final_text_list.append(text[item[1]+1:])
                else:
                    final_text_list.append(text[item[1]+1: clean_prefix_offsets[idx + 1][0]+1])

            text = ''.join(final_text_list) if len(final_text_list) > 0 else text
            text = self.email_pattern.sub('', text)

        return text[1:-1]

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

    def remove_phone_number(self, text, delete_prefix=False):
        """ 删除文本中的电话号码

        Args:
            text(str): 字符串文本
            delete_prefix(bool): 删除电话号码前缀，如 `电  话：198xxxxxxxx`

        Returns:
            str: 删除电话号码后的文本

        """
        if self.cell_phone_pattern is None:
            self.cell_phone_pattern = re.compile(CELL_PHONE_PATTERN)
            self.phone_prefix_pattern = re.compile(PHONE_PREFIX_PATTERN, re.I)

        if self.landline_phone_pattern is None:
            self.landline_phone_pattern = re.compile(LANDLINE_PHONE_PATTERN)
            self.phone_prefix_pattern = re.compile(PHONE_PREFIX_PATTERN, re.I)
        
        text = ''.join(['#', text, '#'])

        if not delete_prefix:
            text = self.cell_phone_pattern.sub('', text)
            text = self.landline_phone_pattern.sub('', text)

        else:
            cell_results = self._extract_base(self.cell_phone_pattern, text, with_offset=True)
            landline_results = self._extract_base(self.landline_phone_pattern, text, with_offset=True)
            results = sorted(cell_results + landline_results, key=lambda i: i['offset'][0])

            prefix_results = self._extract_base(self.phone_prefix_pattern, text, with_offset=True)

            offset_list = [item['offset'][0] for item in results]

            clean_prefix_offsets = [
                item['offset'] for item in prefix_results if item['offset'][1] in offset_list]

            final_text_list = []
            for idx, item in enumerate(clean_prefix_offsets):
                if idx == 0:
                    final_text_list.append(text[0: item[0]+1])

                if idx == len(clean_prefix_offsets) - 1:
                    final_text_list.append(text[item[1]+1:])
                else:
                    final_text_list.append(text[item[1]+1: clean_prefix_offsets[idx + 1][0]+1])

            text = ''.join(final_text_list) if len(final_text_list) > 0 else text
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

    def replace_email(self, text, token='<email>'):
        """ 替换文本中的 email 为归一化标签

        Args:
            text(str): 字符串文本
            token(str): 替换 email 的 token，默认为 `<email>`，与预训练模型保持一致

        Returns:
            str: 替换 email 为归一化 token 后的文本

        """
        if self.email_pattern is None:
            self.email_pattern = re.compile(EMAIL_PATTERN)
            self.email_prefix_pattern = re.compile(EMAIL_PREFIX_PATTERN, re.I)

        text = ''.join(['#', text, '#'])

        text = self.email_pattern.sub(token, text)
        return text[1:-1]

    def replace_id_card(self, text, token='<id>'):
        """ 替换文本中的身份证号为归一化标签

        Args:
            text(str): 字符串文本
            token(str): 替换 id 的 token，默认为 `<id>`，与预训练模型保持一致

        Returns:
            str: 替换身份证 id 为归一化 token 后的文本

        """
        if self.id_card_pattern is None:
            self.id_card_pattern = re.compile(ID_CARD_PATTERN)

        text = ''.join(['#', text, '#'])
        return self.id_card_pattern.sub(token, text)[1:-1]

    def replace_ip_address(self, text, token='<ip>'):
        """ 替换文本中的 ip 地址为归一化标签

        Args:
            text(str): 字符串文本
            token(str): 替换 ip 的 token，默认为 `<ip>`，与预训练模型保持一致

        Returns:
            str: 替换 ip 地址为归一化 token 后的文本

        """
        if self.ip_address_pattern is None:
            self.ip_address_pattern = re.compile(IP_ADDRESS_PATTERN)

        text = ''.join(['#', text, '#'])
        return self.ip_address_pattern.sub(token, text)[1:-1]

    def replace_phone_number(self, text, token='<tel>'):
        """ 替换文本中的电话号码为归一化标签 token

        Args:
            text(str): 字符串文本
            token(str): 替换 tel 的 token，默认为 `<tel>`，与预训练模型保持一致

        Returns:
            str: 替换电话号码后为归一化标签 token 的文本

        """
        if self.cell_phone_pattern is None:
            self.cell_phone_pattern = re.compile(CELL_PHONE_PATTERN)
            self.phone_prefix_pattern = re.compile(PHONE_PREFIX_PATTERN)

        if self.landline_phone_pattern is None:
            self.landline_phone_pattern = re.compile(LANDLINE_PHONE_PATTERN)
            self.phone_prefix_pattern = re.compile(PHONE_PREFIX_PATTERN, re.I)

        text = ''.join(['#', text, '#'])

        text = self.cell_phone_pattern.sub(token, text)
        text = self.landline_phone_pattern.sub(token, text)

        return text[1:-1]

    def replace_qq(self, text, strict=True, token='<qq>'):
        """ 替换文本中的电 QQ 号为归一化标签

        Args:
            text(str): 字符串文本
            strict(bool): QQ 号容易与其他数字混淆，因此选择严格规则或宽松规则
            token(str): 替换 QQ 的 token，默认为 `<qq>`，与预训练模型保持一致

        Returns:
            str: 替换 QQ 为归一化 token 后的文本

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
        return self.qq_pattern.sub(token, text)[1:-1]

    def replace_url(self, text, token='<url>'):
        """ 将文本中的 url 链接归一化

        Args:
            text(str): 字符串文本
            token(str): 替换 url 的 token，默认为 `<url>`，与预训练模型保持一致

        Returns:
            text: 将 url 链接文本统一替换成标准字符串，默认为 token `<url>`
                token可以自行定义。

        """
        if self.url_pattern is None:
            self.url_pattern = re.compile(URL_PATTERN)

        text = ''.join(['￥', text, '￥'])
        return self.url_pattern.sub(token, text)[1:-1]

    def replace_chinese(self, text, substitute=r' '):
        """ 替换文本中的所有中文字符串为空格，默认为空格，可以自定义指定目标字符。

        Args:
            text(str): 输入的文本
            substitute(str): 将中文文字，替换为何种字符串，默认为一个空格

        Return:
            list(str): 中文文本列表，若两段中文之间有其它字符，则按序排列在列表中

        Examples:
            >>> import jionlp as jio
            >>> print(jio.replace_chinese('【新华社消息】（北京时间）从昨天...'))

            # '【     】（    ）   ...'

        """
        if text == '':
            return list()

        if self.chinese_char_pattern is None:
            self.chinese_char_pattern = re.compile(CHINESE_CHAR_PATTERN)

        if type(substitute) is not str:
            raise TypeError('the `substitute` is not string.')

        text_without_chinese = self.chinese_char_pattern.sub(substitute, text)

        return text_without_chinese

    def extract_chinese(self, text):
        """ 抽取出文本中的所有中文字符串

        Args:
            text(str): 输入的文本

        Return:
            list(str): 中文文本列表，若两段中文之间有其它字符，则按序排列在列表中

        Examples:
            >>> import jionlp as jio
            >>> print(jio.extract_chinese('【新华社消息】（北京时间）从昨天...'))

            # ['新华社消息', '北京时间','从昨天']

        """
        if text == '':
            return list()

        if self.chinese_chars_pattern is None:
            self.chinese_chars_pattern = re.compile(CHINESE_CHAR_PATTERN + '+')

        chinese_text_list = self.chinese_chars_pattern.findall(text)

        return chinese_text_list
