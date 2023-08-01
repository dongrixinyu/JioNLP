# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com


import re
import html

from jionlp.dictionary import html_entities_dictionary_loader
from .html_rule_pattern import *


class CleanHTML(object):

    def __init__(self):
        self.html_pattern = None

    def _prepare(self):
        self.html_pattern = True
        self.script_tag_pattern = re.compile(SCRIPT_TAG_PATTERN)
        self.style_tag_pattern = re.compile(STYLE_TAG_PATTERN)
        self.table_tag_pattern = re.compile(TABLE_TAG_PATTERN)
        self.form_tag_pattern = re.compile(FORM_TAG_PATTERN)
        self.unordered_list_tag_pattern = re.compile(UNORDERED_LIST_TAG_PATTERN)
        self.ordered_list_tag_pattern = re.compile(ORDERED_LIST_TAG_PATTERN)
        self.footer_tag_pattern = re.compile(FOOTER_TAG_PATTERN)
        self.navigation_tag_pattern = re.compile(NAVIGATION_TAG_PATTERN)

        self.meta_tag_pattern = re.compile(META_TAG_PATTERN)
        self.comment_tag_pattern = re.compile(COMMENT_TAG_PATTERN)
        self.break_line_tag_pattern = re.compile(BREAK_LINE_TAG_PATTERN)

        self.div_tag_start_pattern = re.compile(DIV_TAG_START_PATTERN)
        self.div_tag_end_pattern = re.compile(DIV_TAG_END_PATTERN)

        self.div_attr_remove_list = [
            'menu', 'nav',
            'header', 'footer', 'after-content',
            'archive', 'bloglist', 'blog-list', 'catalog',
            'sidebar', 'side-bar', 'side-content',
            'cookie']

        self.html_tag_pattern = re.compile(HTML_TAG_PATTERN)
        self.tab_new_line_pattern = re.compile(TAB_NEW_LINE_PATTERN)

        self.id_attr_pattern = re.compile(ID_ATTR_PATTERN)
        self.name_attr_pattern = re.compile(NAME_ATTR_PATTERN)
        self.class_attr_pattern = re.compile(CLASS_ATTR_PATTERN)
        self.content_attr_pattern = re.compile(CONTENT_ATTR_PATTERN)

        self.add_new_line_pattern = re.compile(ADD_NEW_LINE_PATTERN)

        self.html_entities_dict = {}
        tmp_html_entities_dict = html_entities_dictionary_loader()
        for key, val in tmp_html_entities_dict.items():
            self.html_entities_dict.update({key: val['characters']})
            for num in val['codepoints']:
                cp_key = '&#{};'.format(num)
                self.html_entities_dict.update({cp_key: val['characters']})
        self.html_entities_dict = dict(sorted(
            self.html_entities_dict.items(), reverse=True))

    def __call__(self, orig_html_text):
        """ 清洗 html 爬虫文本，为具有完整语义的正文文本。

        Args:
            orig_html_text: html 格式文本

        Returns:
            str: 清洗后的文本。

        """
        if self.html_pattern is None:
            self._prepare()

        # 对原始 html 文件直接去除其中多余的 \t \n 空格 等。
        orig_html_text, _ = self.tab_new_line_pattern.subn('', orig_html_text)

        # 获取 html 的元信息
        meta_info = self.extract_meta_info(orig_html_text)

        # remove <script>...</script> content, because these tags contain javascript text.
        html_text, _ = self.script_tag_pattern.subn('', orig_html_text)
        html_text, _ = self.style_tag_pattern.subn('', html_text)
        html_text, _ = self.table_tag_pattern.subn('', html_text)
        html_text, _ = self.form_tag_pattern.subn('', html_text)
        # html_text, _ = self.ordered_list_tag_pattern.subn('', html_text)
        # html_text, _ = self.unordered_list_tag_pattern.subn('', html_text)
        html_text, _ = self.footer_tag_pattern.subn('', html_text)

        html_text, _ = self.meta_tag_pattern.subn('', html_text)
        html_text, _ = self.comment_tag_pattern.subn('', html_text)

        # 去除那些带有导航的 div 标签
        while True:
            html_text, start_offset, tuned = self.remove_menu_div_tag(html_text)
            if not tuned:
                break

        # 将 <br> 替换为换行符 \n
        html_text, _ = self.break_line_tag_pattern.subn('\n', html_text)

        # 对 </p> 符进行字段换行替换
        html_text = self.add_new_line_pattern.sub(r'\n\1', html_text)

        content, _ = self.html_tag_pattern.subn('', html_text)

        # 替换 html entity
        content = html.unescape(content)

        # 清除其中多余的 符号。
        # content, _ = self.tab_new_line_pattern.subn('\n\n', content)
        # print(html_text)
        # print(content)
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
                matched_attr = matched_attr.group('TagName')
                try:
                    matched_content = self.content_attr_pattern.search(item).group('TagContent')
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

    def remove_menu_div_tag(self, html_text):
        """删除那些表示 menu、navigation 等信息的 div tag。

        Args:
            html_text: HTML 文档

        Returns: html 文档

        """
        start_offset = 0
        matched_item = None

        for idx, matched_item in enumerate(self.div_tag_start_pattern.finditer(html_text)):
            # 检查第一个 div 的属性 id class，如果有 menu，则剔除该部分。
            id_attr_res = self.id_attr_pattern.search(matched_item.group())
            class_attr_res = self.class_attr_pattern.search(matched_item.group())

            # 判断是否匹配到 menu nav 等 div 标签
            tuned_flag = False
            for keyword in self.div_attr_remove_list:
                if id_attr_res:
                    if keyword in id_attr_res.group('TagID').lower():
                        tuned_flag = True
                        break

                if class_attr_res:
                    if keyword in class_attr_res.group('TagClass').lower():
                        tuned_flag = True
                        break

            if tuned_flag:
                start_offset = matched_item.span()[1]
                break

        if start_offset != 0:
            nested_list = []
            end_offset = 0
            while True:
                start_res = self.div_tag_start_pattern.search(html_text[start_offset:])
                end_res = self.div_tag_end_pattern.search(html_text[start_offset:])

                # check matched res：
                if start_res is not None and end_res is not None:

                    if start_res.span()[0] < end_res.span()[0]:
                        nested_list.append(start_res)
                        start_offset = start_res.span()[1] + start_offset
                    elif start_res.span()[0] > end_res.span()[0]:
                        if len(nested_list) > 0:
                            nested_list.pop()
                            if len(nested_list) == 0:
                                end_offset = end_res.span()[1] + start_offset
                                break
                            else:
                                start_offset = end_res.span()[1] + start_offset
                        else:
                            # 初始 div 元素下，没有别的 div 子嵌套
                            end_offset = start_offset
                            break

                    else:
                        break

                elif start_res is not None and end_res is None:
                    break

                elif start_res is None and end_res is not None:
                    if len(nested_list) > 0:

                        nested_list.pop()
                        if len(nested_list) == 0:
                            end_offset = end_res.span()[1] + start_offset
                            break
                        else:
                            start_offset = end_res.span()[1] + start_offset
                    else:
                        # 初始 div 元素下，没有别的 div 子嵌套
                        end_offset = start_offset
                        break

                elif start_res is None and end_res is None:
                    break

            if end_offset != 0:
                # 找见初次 div 的 </div> 标签
                end_res = self.div_tag_end_pattern.search(html_text[end_offset:])
                if end_res is not None:
                    end_offset = end_res.span()[1] + end_offset

                html_text = html_text[:matched_item.span()[0]] + html_text[end_offset:]

                return html_text, matched_item.span()[0], True

            else:
                return html_text, matched_item.span()[0], False
        else:
            return html_text, 0, False

