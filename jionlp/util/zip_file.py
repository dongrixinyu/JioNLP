# -*- coding=utf-8 -*-

import os
import shutil
import zipfile


FILE_PATH = os.path.abspath(__file__)
DIR_PATH = os.path.dirname(os.path.dirname(FILE_PATH))


def zip_file(file_list=None):
    """ 将某些 txt 文件压缩 """
    if file_list is None:
        file_list = ['china_location.txt', 'chinese_char_dictionary.txt',
                     'chinese_idiom.txt', 'chinese_word_dictionary.txt',
                     'idf.txt', 'pinyin_phrase.txt',
                     'word_topic_weight.json', 'topic_word_weight.json']

    dict_dir_path = os.path.join(DIR_PATH, 'dictionary')
    for _file in file_list:
        dict_file_path = os.path.join(dict_dir_path, _file)
        tmp_file_path = os.path.join(os.getcwd(), _file)
        shutil.copyfile(dict_file_path, tmp_file_path)

        zip_file_name = _file.split('.')[0] + '.zip'

        with zipfile.ZipFile(os.path.join(dict_dir_path, zip_file_name),
                             'w', zipfile.ZIP_DEFLATED) as zf:
            # zf.write(os.path.join(dict_dir_path, _file))
            zf.write(_file)

        os.remove(tmp_file_path)


def unzip_file():
    """ 将某些 txt 文件解压缩 """
    file_list = ['china_location.zip', 'chinese_char_dictionary.zip',
                 'chinese_idiom.zip', 'chinese_word_dictionary.zip',
                 'idf.zip', 'pinyin_phrase.zip',
                 'word_topic_weight.zip', 'topic_word_weight.zip']

    dict_dir_path = os.path.join(DIR_PATH, 'dictionary')
    for _zip_file in file_list:
        zip_file_path = os.path.join(dict_dir_path, _zip_file)
        with zipfile.ZipFile(zip_file_path, 'r') as zf:
            assert len(zf.namelist()) == 1
            for _file in zf.namelist():
                zf.extract(_file, dict_dir_path)

