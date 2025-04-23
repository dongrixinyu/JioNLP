# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & parsing tool for Chinese NLP
# website: www.jionlp.com


import os


FILE_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


class HelpSearch(object):
    """ 搜索 JioNLP 工具包内的所有函数注释的说明。
    若不知道 JioNLP 工具包支持的功能，可根据命令行提示键入若干关键词做搜索。
    
    Examples:
        >>> import jionlp as jio
        >>> jio.help()

        > please enter keywords in Chinese separated by space:数据增强
        > function name ==> jio.BackTranslation
        > 回译接口，集成多个公开免费试用机器翻译接 ...

    """
    def __init__(self):
        # print('# jionlp - 微信公众号: JioNLP  Github: `https://github.com/dongrixinyu/JioNLP`.')
        print('# jionlp - 微信公众号: JioNLP  最近作者想跳槽了，求内推，AI方向即可，wx号：shanzhuiyancheng')

        self.function_dict = None
        self.non_function_list = [
            # 辅助工具
            'Extractor', 'FastLoader', 'HelpSearch', 'IDCardParser',
            'guide', 'help', 'os', 'logging', 'unzip_file', 'zip_file',
            # 被 __call__ 的类
            'CharRadical', 'IdiomSolitaire', 'LocationParser',
            'PhoneLocation', 'Pinyin', 'RemoveStopwords', 'SplitSentence',
            'TSConversion', 'MoneyStandardization', 'LocationRecognizer',
            'HomophoneSubstitution', 'RandomAddDelete', 'SwapCharPosition',
            'TimeNormalizer',
            # 文件说明
            'ts_conversion', 'location_recognizer',
            # 多层函数的误例
            'keyphrase.ChineseKeyPhrasesExtractor',
            'ner.lexicon_ner', 'ner.ner_accelerate',
            'ner.ner_data_converter', 'ner.ner_entity_compare',
            'sentiment.sentiment_analysis',
            'summary.ChineseSummaryExtractor']

        self.middle_name_list = [
            'keyphrase', 'ner', 'sentiment', 'summary', 'text_classification']

    def _prepare(self):
        import jionlp as jio

        self.function_dict = dict()
        for function_name in dir(jio):
            if function_name == function_name.upper():
                continue
            if function_name.startswith('__'):
                continue
            if function_name in self.non_function_list:
                continue

            res = eval('jio.' + function_name + '.__doc__')
            if res is None:
                continue

            self.function_dict.update({function_name: res})

        for middle_name in self.middle_name_list:
            for function_name in dir(eval('jio.' + middle_name)):
                if function_name.startswith('_'):
                    continue

                full_function_name = middle_name + '.' + function_name
                if full_function_name in self.non_function_list:
                    continue

                res = eval('jio.' + full_function_name + '.__doc__')
                if res is None:
                    continue

                self.function_dict.update({full_function_name: res})

    @staticmethod
    def command_parser(input_string):
        """ 解析输入的查询命令 """
        search_word_list = input_string.split(' ')
        return search_word_list

    def search(self, search_word_list):
        """ 根据关键词搜索 """
        function_name_dict = dict()
        for word in search_word_list:
            for function_name, document in self.function_dict.items():
                if word in document:
                    if function_name in function_name_dict:
                        function_name_dict[function_name] += document.count(word)
                    else:
                        function_name_dict.update({function_name: document.count(word)})

        if function_name_dict == dict():
            return None

        function_name_tuple = sorted(function_name_dict.items(),
                                     key=lambda i: i[1], reverse=True)
        # print(function_name_tuple)
        for function_name, value in function_name_tuple:
            yield function_name

    def __call__(self):
        if self.function_dict is None:
            self._prepare()

        input_string = input('please enter Chinese keywords separated by space: ')

        search_word_list = self.command_parser(input_string)
        for function_name in self.search(search_word_list):
            print('\nfunction name ==> jio.' + function_name)
            print(self.function_dict[function_name])
            print('function name ==> jio.' + function_name)
            input_string = input('type in `n` for next function, `q` for quitting: ')
            if input_string == 'n':
                continue
            elif input_string == 'q':
                break
            else:
                break

