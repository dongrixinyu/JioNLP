# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import json
import time
import ctypes
from jionlp import logging


class SimHash(object):

    def __init__(self, use_redis=True, f_topN=500, redis_db_name=list([13, 14, 15, 16]),
                 redis_host='0.0.0.0', redis_port=6379, redis_password='password',
                 delete_date_before=30, 
                 scheduler_args={"type": "cron", 
                                 "args": {"day": "1-31", "hour": 2, 
                                          "minute": 0, "second": 0}}):
        self.use_redis = use_redis
        if use_redis:  # 使用 redis 存储比较
            from bbd_tools.nlp.algorithms.simhash_redis.simhash_redis import SimHashRedisCheck
            
            # 配置数据库名
            sim_hash_redis_db_name = dict()
            for albe, db_name in zip('ABCD', redis_db_name):
                sim_hash_redis_db_name.update({'simhash_db_' + albe: db_name})
            
            self.sim_hash_redis_check = SimHashRedisCheck(sim_hash_redis_db_name)
            self.sim_hash_redis_check.init_redis(
                redis_host=redis_host, redis_port=redis_port,
                redis_password=redis_password, expire_time=delete_date_before)
            self.sim_hash_redis_check.add_schedule_job(scheduler_args)
            
        else:  # 不使用 redis，单纯计算
            from bbd_tools.nlp.algorithms.simhash_redis.simhash import SimHash
            self.sim_hash = SimHash(f_topN=500)

    def predict(self, text):
        if not self.use_redis:
            # 单纯做 simhash 计算
            hashcode = self.sim_hash.getSimHash(text)
            return str(hashcode)
        else:
            # 还要在 redis 里做比较
            hashcode = self.sim_hash_redis_check.getSimHash(text)
            search_status, _ = self.sim_hash_redis_check.search_sim_text_in_redis(
                hashcode, threshold=3)
            if search_status == 1:
                sim_hash = str(self.sim_hash_redis_check.merge_slice(_))
            else:
                sim_hash = str(hashcode)
            return sim_hash
        
    def compute_hamming_distance(self, hashcode1, hashcode2):
        return self.sim_hash.hammingDistance(hashcode1, hashcode2)

