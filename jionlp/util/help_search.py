# -*- coding=utf-8 -*-

import os

import jieba


FILE_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(FILE_PATH)


class HelpSearch(object):
    """ 搜索函数注释的说明。
    
    

    """
    def __init__(self, name=None):
        print('you could use `jio.help()` to search how to use jio functions.')
        self.function_list = None
        

    def _prepare(self):
        import jionlp as jio
        self.function_list = list()
        for function_name in dir(jio):
            res = eval('jio.' + function_name + '.__doc__')
            self.function_list.append({function_name: res})
    
    def description(self):
        """ 打印搜索工具的使用方法 """
        print('请输入关键词，以空格分隔，如“分句”')
    
    def command_parser(self):
        """ 解析输入的查询命令 """
    
    def search(self, ):
        """ 计算从起始（或上一断点）到当前断点调用的时间
        """
        
        
    def __call__(self):
        print(DIR_PATH)
        if self.function_list is None:
            self._prepare()
        
        input_string = input('请输入关键词，以空格分隔，如“分句”：')
        
        
        
        
        
        
        
        

