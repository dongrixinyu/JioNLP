# -*- coding: utf-8 -*-
# @Author  : luozhenquan

class items():
    def __init__(self):
        self.items_ls = []

    def putNote(self, item):
        item_begin = item.begin
        item_end = item.end
        if len(self.items_ls) == 0:
            self.items_ls.append(item)
        else:
            tmp_item = self.items_ls[-1]
            tmp_item_beging = tmp_item.begin
            tmp_item_end = tmp_item.end
            if item_begin < tmp_item_end and not (item_begin > tmp_item_beging and item_end == tmp_item_end):
                prev_len = tmp_item.prev_len
                if item_end == tmp_item_end:
                    prev_len -= abs(item_begin - tmp_item_beging)
                item.setPrevLen(prev_len)
                item.setNextLen(20)
                self.items_ls[-1] = item
            elif not (item_begin > tmp_item_beging and item_end == tmp_item_end):
                tmp_len = item_begin - tmp_item_end
                item.setPrevLen(tmp_len)
                item.setNextLen(20)
                tmp_item.setNextLen(tmp_len)
                self.items_ls[-1] = tmp_item
                self.items_ls.append(item)
