# -*- coding=utf-8 -*-

#from bbd_nlp_apis.gadget import gadget
#from .gadget import read_file_by_line
from .file_io import read_file_by_line
from .file_io import write_file_by_line
from . import trie_tree
from . import ts_conversion 

from jionlp.util.fast_loader import FastLoader


rule = FastLoader('rule', globals(), 'jionlp.rule')

