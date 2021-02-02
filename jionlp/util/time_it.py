# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import time


class TimeIt(object):
    ''' 程序运行的消耗时间统计
    Args:
        name(str): 指定代码段的功能含义，可不指定
        unit(str): 计时单位，包括 秒(s)与毫秒(ms)
        no_print(bool): 指定是否打印计时

    '''
    def __init__(self, name=None, unit='s', no_print=False):
        self.start_time = None
        self.restart_time = None  # 每次执行断点的重新计数时间
        self.cost_time = None
        self.no_print = no_print
        self.name = name if name is not None else 'None'
        self.unit = unit
        assert self.unit in ['s', 'ms'], '时间单位仅限于`秒`和`毫秒`'
        
    def __enter__(self):
        self.start_time = time.time()
        self.restart_time = time.time()
        return self
        
    def __exit__(self, *args, **kwargs):
        self.cost_time = time.time() - self.start_time
        if not self.no_print:
            if self.unit == 's':
                print('{0:s} totally costs {1:.3f} s.'.format(
                    self.name, self.cost_time))
            elif self.unit == 'ms':
                print('{0:s} totally costs {1:.1f} ms.'.format(
                    self.name, self.cost_time * 1000))
    
    def break_point(self, restart=True):
        """ 计算从起始（或上一断点）到当前断点调用的时间
        Args:
             restart(bool): 指定代码段的计时是否接下来从 0 开始。
        """
        if not restart:
            cost_time = time.time() - self.start_time
        else:
            cost_time = time.time() - self.restart_time
            
        if not self.no_print:
            if self.unit == 's':
                print('{0:s} break point costs {1:.3f} s.'.format(
                    self.name, cost_time))
            elif self.unit == 'ms':
                print('{0:s} break point costs {1:.1f} ms.'.format(
                    self.name, cost_time * 1000))
        
        self.restart_time = time.time()
        
        return cost_time

