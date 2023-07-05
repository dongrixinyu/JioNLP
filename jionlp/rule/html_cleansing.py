# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re

from .html_rule_pattern import *


class CleanHTML(object):

    def __init__(self):
        self.html_pattern = None

    def _prepare(self):
        self.html_pattern = True
        self.script_tag_pattern = re.compile(SCRIPT_TAG_PATTERN)
        self.style_tag_pattern = re.compile(STYLE_TAG_PATTERN)
        self.table_tag_pattern = re.compile(TABLE_TAG_PATTERN)
        self.unordered_list_tag_pattern = re.compile(UNORDERED_LIST_TAG_PATTERN)
        self.ordered_list_tag_pattern = re.compile(ORDERED_LIST_TAG_PATTERN)

        self.meta_tag_pattern = re.compile(META_TAG_PATTERN)
        self.comment_tag_pattern = re.compile(COMMENT_TAG_PATTERN)
        self.break_line_tag_pattern = re.compile(BREAK_LINE_TAG_PATTERN)

        self.html_tag_pattern = re.compile(HTML_TAG_PATTERN)
        self.tab_new_line_pattern = re.compile(TAB_NEW_LINE_PATTERN)

        self.name_attr_pattern = re.compile(NAME_ATTR_PATTERN)
        self.content_attr_pattern = re.compile(CONTENT_ATTR_PATTERN)

        self.add_new_line_pattern = re.compile(ADD_NEW_LINE_PATTERN)

    def __call__(self, orig_html_text):
        """ 清洗 html 爬虫文本，为具有完整语义的正文文本。

        Args:
            orig_html_text: html 格式文本

        Returns:
            str: 清洗后的文本。

        """
        if self.html_pattern is None:
            self._prepare()

        meta_info = self.extract_meta_info(orig_html_text)

        # remove <script>...</script> content, because these tags contain javascript text.
        html_text, _ = self.script_tag_pattern.subn('', orig_html_text)
        html_text, _ = self.style_tag_pattern.subn('', html_text)
        html_text, _ = self.table_tag_pattern.subn('', html_text)
        html_text, _ = self.ordered_list_tag_pattern.subn('', html_text)
        html_text, _ = self.unordered_list_tag_pattern.subn('', html_text)

        html_text, _ = self.meta_tag_pattern.subn('', html_text)
        html_text, _ = self.comment_tag_pattern.subn('', html_text)

        # 将 <br> 替换为换行符 \n
        html_text, _ = self.break_line_tag_pattern.subn('\n', html_text)

        # 对 </p> 符进行字段换行替换
        html_text = self.add_new_line_pattern.sub(r'\n\1', html_text)

        content, _ = self.html_tag_pattern.subn('', html_text)
        # 清除其中多余的 符号。
        content, _ = self.tab_new_line_pattern.subn('\n\n', content)
        print(html_text)
        print(content)
        return content, meta_info

    def extract_meta_info(self, html_text):
        """ extract <meta>...</meta> content,
        because these tags contain description, keywords, classification, language text.

        Args:
            html_text:

        Returns:
            dict(str): meta info dict

        """
        meta_info = {}

        matched_res = self.meta_tag_pattern.findall(html_text)

        for item in matched_res:
            matched_attr = self.name_attr_pattern.search(item)
            if matched_attr is not None:
                matched_attr = matched_attr.group(2)
                try:
                    matched_content = self.content_attr_pattern.search(item).group(2)
                except:
                    continue
                if matched_attr == 'description':
                    meta_info.update({'description': matched_content})
                elif matched_attr == 'keywords':
                    meta_info.update({'keywords': matched_content})
                elif matched_attr == 'classification':
                    meta_info.update({'classification': matched_content})
                elif matched_attr == 'language':
                    meta_info.update({'language': matched_content})

        return meta_info




