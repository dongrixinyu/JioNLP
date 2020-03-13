# -*- coding=utf-8 -*-

import os
import time
from bbd_tools import logging


class LexiconNER(object):
    """
    使用范例:
    >>> from bbd_tools.algorithms.lexicon_ner import LexiconNER
    >>> lexicon_ner = LexiconNER(dicts_files)
    >>> result = lexicon_ner.predict(text)
    
    :参数:
        dicts_files: str 类型，一个词典文件或文件夹的路径，
            若非绝对路径，则默认文件在当前工作环境下。
            若为文件，则读取其中词汇，
            若为文件夹，则读取每一个文件的词汇。
            e.g.
            - /tmp/dicts_dir
                - person.txt
                    ```
                    张大山
                    岳灵珊
                    岳不群
                    ```
                - organization.txt
                    ```
                    成都数联铭品公司
                    四川省水利局
                    ```
            其中每一个词典文件的名字必须为 `类型` + `.txt`，
            每一个文件中的文字格式编码要求是 utf-8 格式，
            且词汇组织形式必须以换行符 “ \n ” 进行分割。
        text: str 类型，被搜索的文本内容。
    """
    def __init__(self, dicts_files):
        """
        :param dicts_files: 词典文件或文件夹路径，str 格式
        """
        if os.path.isfile(dicts_files):
            self.files = [dicts_files]
        elif os.path.isdir(dicts_files):
            self.files = os.listdir(dicts_files)

        # self.files = dicts_files  # 词典文件的路径 list
        self.types = []  # 存放词典的类型

        self.count = 0  # 用于统计总匹配词汇数量
        self.statistics_dict_items = []  # 用于统计每一个词典中的词汇数量
        self.statistics_dict_match = []  # 用于统计每一个词典中的词汇的被匹配数量
        self.trie_tree_obj = TrieTree()

        for file in self.files:  # 将词典 file 数据组织成 list，并构建成 Trie树
            self.statistics_dict_match.append(0)
            tmp_dict_name = os.path.basename(file)
            if "." in tmp_dict_name:
                tmp_dict_name = tmp_dict_name.split(".")[0]
            self.types.append(tmp_dict_name)
            if type(file) is not list:
                dict_list = self.read_file(os.path.join(dicts_files, file))  # 读取每个词典文件中的内容
            else:
                dict_list = file
            self.statistics_dict_items.append(len(dict_list))
            self.trie_tree_obj.build_trie_tree(dict_list, tmp_dict_name)

    @staticmethod
    def read_file(file):
        """
        读取词典中的文件
        :param file: 文件路径
        :return: list 类型的词汇列表
        """
        abs_file = os.path.abspath(file)
        with open(abs_file, 'r', encoding='utf8') as df:
            line = df.read()
        dict_list = line.split("\n")
        return dict_list

    def predict(self, string):
        """
        标注数据，给定一个文本的 string，标注出所有的数据
        :param string: 给定的文本 str 格式
        :return: 标注的数据
        """
        statistics = []
        for _ in self.statistics_dict_match:
            statistics.append(0)
        count = self.count

        start_time = time.time()
        record_list = []  # 输出最终结果
        i = 0
        end = len(string)
        while i < end:
            pointer_orig = string[i: self.trie_tree_obj.depth + i]
            pointer = pointer_orig.lower()
            step, typing = self.trie_tree_obj.search(pointer)
            if typing is not None:
                record = {"type": typing,
                          "text": pointer_orig[0: step],  # 经过大小写识别之后的字符串
                          "offset": [i, step + i]}
                statistics[self.types.index(typing)] += 1
                record_list.append(record)
            i += step

        for i in statistics:
            count += i
        logging.info('ner cost {:.2f} seconds.\nentity number is {}.'.format(
            time.time() - start_time, count))
        for i in self.types:
            logging.info('the number of items in dictionary "{}" is {}, '
                         'matched entity number is {} '.format(
                             i, self.statistics_dict_items[self.types.index(i)],
                             statistics[self.types.index(i)]))
        return record_list

    def generate_brat_data(self, text, text_name, brat_dir='brat_dir', remove_unmatch=True):
        '''
        标注数据并写为brat格式
        :param text: str 待标注文本
        :param text_name: 文本名
        :param brat_dir: brat文件保存目录
        :param ignore_unmatch: 是否忽略未匹配到的文本，当ignore_unmatch=True时，不生成未匹配到的文本的brat格式文本
        '''

        pred_list = self.predict(text)
        if len(pred_list) == 0 and remove_unmatch:
            return

        text_name = os.path.join(brat_dir, text_name)
        with open(text_name + '.txt', 'w', encoding='utf-8') as f:
            f.write(text)

        write_format = 'T{idx}\t{name} {offset1} {offset2}\t{text}\n'
        with open(text_name + '.ann', 'w', encoding='utf-8') as f:
            for idx, pred in enumerate(pred_list):
                line = write_format.format(idx=idx+1, name=pred['type'],
                                           offset1=pred['offset'][0], offset2=pred['offset'][1],
                                           text=pred['text'])
                f.write(line)


class TrieTree(object):
    """
    Trie 树的基本方法
    """
    def __init__(self):
        self.dict_trie = {}
        self.depth = 0

    def add_node(self, word, typing):
        """
        向 Trie 树添加节点
        :param word: 字典中的词汇
        :param typing: 词汇类型
        :return: None
        """
        word = word.strip()
        if word != "" and word != "\t" and word != " " and word != "\r":
            tree = self.dict_trie
            depth = len(word)
            word = word.lower()  # 将所有的字母全部转换成小写
            for char in word:
                if char in tree:
                    tree = tree[char]
                else:
                    tree[char] = {}
                    tree = tree[char]
            if depth > self.depth:
                self.depth = depth
            if 'type' in tree and tree['type'] != typing:
                logging.warning('entity “ {} ” belongs to “ {} ” and “ {} ” '
                                'at the same time.'.format(
                                    word, tree['type'], typing))
            else:
                tree['type'] = typing

    def build_trie_tree(self, dict_list, typing):
        """
        创建 trie 树
        :param dict_list: list
        :param typing: str
        :return: None
        """
        for word in dict_list:
            self.add_node(word, typing)

    def search(self, word):
        """
        搜索给定word字符串中与词典匹配的 entity
        :param word: 一个字符串
        :return: step,type.  None 代表字符串中没有要找的实体，
            如果返回字符串，则该字符串就是所要找的词汇的类型
        """
        tree = self.dict_trie
        res = None
        step = 0  # step 计数索引位置
        for char in word:
            if char in tree:
                tree = tree[char]
                step += 1
                if 'type' in tree:
                    res = (step, tree['type'])
            else:
                break
        if res:
            return res
        return 1, None
