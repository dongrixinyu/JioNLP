# -*- coding: utf-8 -*-
# @Author  : luozhenquan

from enum import Enum, unique


class item():
    def __init__(self, begin, end, prev_len, next_len, s):
        self.begin = begin
        self.end = end
        self.prev_len = prev_len
        self.next_len = next_len
        self.bias = Bias.MIDDLE
        self.s = s

    def setNextLen(self,next_len):
        self.next_len = next_len
        if self.prev_len >= self.next_len and self.next_len < 6:
            self.bias = Bias.RIGHT
        elif self.prev_len < self.next_len and self.prev_len < 6:
            self.bias = Bias.LEFT

    def setPrevLen(self,prev_len):
        self.prev_len = prev_len
        if self.prev_len >= self.next_len and self.next_len < 6:
            self.bias = Bias.RIGHT
        elif self.prev_len < self.next_len and self.prev_len < 6:
            self.bias = Bias.LEFT




try:
    @unique
    class Bias(Enum):
        LEFT = 0
        MIDDLE = 0.5
        RIGHT = 1
except ValueError as e:
    print(e)
