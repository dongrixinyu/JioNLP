# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: www.jionlp.com


import os
import json


__all__ = ['read_file_by_iter', 'read_file_by_line',
           'write_file_by_line']


def read_file_by_iter(file_path, line_num=None, 
                      skip_empty_line=True, strip=True,
                      auto_loads_json=True):
    """读取一个文件的前 N 行，按迭代器形式返回返回，
    文件中按行组织，要求 utf-8 格式编码的自然语言文本。
    若每行元素为 json 格式可自动加载。

    Args:
        file_path(str): 文件路径
        line_num(int): 读取文件中的行数，若不指定则全部按行读出
        skip_empty_line(boolean): 是否跳过空行
        strip(bool): 将每一行的内容字符串做 strip() 操作
        auto_loads_json(bool): 是否自动将每行使用 json 加载，默认为真

    Returns:
        list: line_num 行的内容列表

    Examples:
        >>> file_path = '/path/to/stopwords.txt'
        >>> print(jio.read_file_by_iter(file_path, line_num=3))

        # ['在', '然后', '还有']

    """
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        while True:
            if line == '':  # 整行全空，说明到文件底
                break
            if line_num is not None:
                if count >= line_num:
                    break

            if line.strip() == '':
                if skip_empty_line:
                    count += 1
                    line = f.readline()
                else:
                    try:
                        if auto_loads_json:
                            cur_obj = json.loads(line.strip())
                            yield cur_obj
                        else:
                            if strip:
                                yield line.strip()
                            else:
                                yield line
                    except:
                        if strip:
                            yield line.strip()
                        else:
                            yield line
                    count += 1
                    line = f.readline()
                    continue
            else:
                try:
                    if auto_loads_json:
                        cur_obj = json.loads(line.strip())
                        yield cur_obj
                    else:
                        if strip:
                            yield line.strip()
                        else:
                            yield line
                except:
                    if strip:
                        yield line.strip()
                    else:
                        yield line

                count += 1
                line = f.readline()
                continue


def read_file_by_line(file_path, line_num=None, 
                      skip_empty_line=True, strip=True,
                      auto_loads_json=True):
    """ 读取一个文件的前 N 行，按列表返回，
    文件中按行组织，要求 utf-8 格式编码的自然语言文本。
    若每行元素为 json 格式可自动加载。

    Args:
        file_path(str): 文件路径
        line_num(int): 读取文件中的行数，若不指定则全部按行读出
        skip_empty_line(boolean): 是否跳过空行
        strip: 将每一行的内容字符串做 strip() 操作
        auto_loads_json(bool): 是否自动将每行使用 json 加载，默认是

    Returns:
        list: line_num 行的内容列表

    Examples:
        >>> file_path = '/path/to/stopwords.txt'
        >>> print(jio.read_file_by_line(file_path, line_num=3))

        # ['在', '然后', '还有']

    """
    content_list = list()
    count = 0
    with open(file_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        while True:
            if line == '':  # 整行全空，说明到文件底
                break
            if line_num is not None:
                if count >= line_num:
                    break

            if line.strip() == '':
                if skip_empty_line:
                    count += 1
                    line = f.readline()
                else:
                    try:
                        if auto_loads_json:
                            cur_obj = json.loads(line.strip())
                            content_list.append(cur_obj)
                        else:
                            if strip:
                                content_list.append(line.strip())
                            else:
                                content_list.append(line)
                    except:
                        if strip:
                            content_list.append(line.strip())
                        else:
                            content_list.append(line)

                    count += 1
                    line = f.readline()
                    continue
            else:
                try:
                    if auto_loads_json:
                        cur_obj = json.loads(line.strip())
                        content_list.append(cur_obj)
                    else:
                        if strip:
                            content_list.append(line.strip())
                        else:
                            content_list.append(line)
                except:
                    if strip:
                        content_list.append(line.strip())
                    else:
                        content_list.append(line)

                count += 1
                line = f.readline()
                continue
                
    return content_list


def write_file_by_line(data_list, file_path, start_line_idx=None,
                       end_line_idx=None, replace_slash_n=True):
    """ 将一个数据 list 按行写入文件中，
    文件中按行组织，以 utf-8 格式编码的自然语言文本。

    Args:
        data_list(list): 数据 list，每一个元素可以是 str, list, dict
        file_path(str): 写入的文件名，可以是绝对路径
        start_line_idx(int): 将指定行的数据写入文件，起始位置，None 指全部写入
        end_line_idx(int): 将指定行的数据写入文件，结束位置，None 指全部写入
        replace_slash_n(bool): 将每个字符串元素中的 \n 进行替换，避免干扰

    Returns:
        None

    Examples:
        >>> data_list = [{'text': '上海'}, {'text': '广州'}]
        >>> jio.write_file_by_line(data_list, 'sample.json')

    """
    if start_line_idx is None:
        start_line_idx = 0
    if end_line_idx is None:
        end_line_idx = len(data_list)

    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data_list[start_line_idx: end_line_idx]:
            if type(item) in [list, dict]:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
            elif type(item) is set:
                f.write(json.dumps(list(item), ensure_ascii=False) + '\n')
            elif type(item) is str:
                f.write(item.replace('\n', '') + '\n')
            elif type(item) in [int, float]:
                f.write(str(item) + '\n')
            else:
                wrong_line = 'the type of `{}` in data_list is `{}`'.format(
                    item, type(item))
                raise TypeError(wrong_line)
