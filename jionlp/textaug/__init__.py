# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


from .back_translation import BackTranslation, BaiduApi, YoudaoFreeApi, \
    YoudaoApi, GoogleApi, TencentApi, XunfeiApi
from .swap_char_position import SwapCharPosition
from .homophone_substitution import HomophoneSubstitution
from .random_add_delete import RandomAddDelete
from .replace_entity import ReplaceEntity

swap_char_position = SwapCharPosition()
homophone_substitution = HomophoneSubstitution()
random_add_delete = RandomAddDelete()

