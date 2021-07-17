# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


def bracket(regular_expression):
    return ''.join([r'(', regular_expression, r')'])


def bracket_absence(regular_expression):
    return ''.join([r'(', regular_expression, r')?'])


def absence(regular_expression):
    return ''.join([regular_expression, r'?'])

