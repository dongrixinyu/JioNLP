# -*- coding=utf-8 -*-


import os
import pdb


from jionlp.util.file_io import read_file_by_line


DIR_PATH = os.path.dirname(os.path.abspath(__file__))
GRAND_DIR_PATH = os.path.dirname(DIR_PATH)


def pkuseg_postag_loader():
    """ 加载北大分词器的词性映射表 """
    content = read_file_by_line(os.path.join(
        DIR_PATH, 'pkuseg_postag_map.txt'))
    
    pkuseg_postag_map = dict()
    for line in content:
        segs = line.split('\t')
        pkuseg_postag_map.update({segs[0]: segs[1]})
    
    return pkuseg_postag_map
