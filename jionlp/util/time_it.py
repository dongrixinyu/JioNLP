# -*- coding=utf-8 -*-

import time


class TimeIt(object):
    ''' 程序运行的消耗时间统计 '''
    def __init__(self, name=None, unit='s'):
        self.start_time = None
        self.restart_time = None  # 每次执行断点的重新计数时间
        self.cost_time = None
        self.name = name if name is not None else 'None'
        self.unit = unit
        assert self.unit in ['s', 'ms'], '时间单位仅限于`秒`和`毫秒`'
        
    def __enter__(self):
        self.start_time = time.time()
        self.restart_time = time.time()
        return self
        
    def __exit__(self, *args, **kwargs):
        self.cost_time = time.time() - self.start_time
        print('{0:s} totally costs {1:.3f} s.'.format(
            self.name, self.cost_time))
    
    def break_point(self, restart=True):
        ''' 计算从起始（或上一断点）到当前断点调用的时间 '''
        if not restart:
            cost_time = time.time() - self.start_time
        else:
            cost_time = time.time() - self.restart_time
        print('{0:s} break point costs {1:.3f} s.'.format(
            self.name, cost_time))
        self.restart_time = time.time()
    