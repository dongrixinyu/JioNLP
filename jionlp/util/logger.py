# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler


_LEVELS = {
    'CRITICAL': logging.CRITICAL,
    'ERROR': logging.ERROR,
    'WARN': logging.WARNING,
    'WARNING': logging.WARNING,
    'INFO': logging.INFO,
    'DEBUG': logging.DEBUG,
    'NOTSET': logging.NOTSET
}


def _logging_level_from_str(level):
    level = level.upper()
    if level in _LEVELS:
        return _LEVELS[level]
    return logging.INFO


def set_logger(level='INFO', log_dir_name='.jio_nlp_logs'):
    level = _logging_level_from_str(level)
    logger = logging.getLogger(__name__)
    logger.setLevel(level)
    
    # 日志需要写在用户目录下，不可随意修改
    user_dir_name = os.path.expanduser('~')
    filename_directory = None
    if log_dir_name.startswith("/"):
        filename_directory = log_dir_name
    else:
        filename_directory = os.path.join(user_dir_name, log_dir_name)
    if not os.path.exists(filename_directory):
        os.makedirs(filename_directory)

    # 输出流控制器
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level)

    # 文件输出控制器
    file_handler = TimedRotatingFileHandler(
        os.path.join(filename_directory, "log.txt"),
        when="midnight", backupCount=30)

    file_handler.setLevel(level)
    file_handler.suffix = "%Y%m%d"
    formatter = logging.Formatter(
        fmt="%(asctime)s %(levelname)s %(funcName)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    length = 20
    logger.log(level, "-" * length + " logging start " + "-" * length)
    logger.log(level, "LEVEL: {}".format(logging.getLevelName(level)))
    logger.log(level, "PATH:  {}".format(filename_directory))
    logger.log(level, "-" * (length * 2 + 15))

    logger.addHandler(stream_handler)
    
    return logger
