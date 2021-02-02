# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import os
import re
# import pdb
import time
import redis
import ctypes
from threading import Thread
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler


def async(f):
    def wrapper(*args, **kwargs):
        thr = Thread(target=f, args=args, kwargs=kwargs)
        thr.start()

    return wrapper


class SimHashRedisCheck(object):
    def __init__(self, redis_db, f_topN=500):
        # SimHash
        self.f_topN = f_topN
        self.compute = None
        self.compute_extract = None
        self.HammingDist = None
        self.initializer()
        
        # redis information
        self.db_name_list = ['simhash_db_A', 'simhash_db_B', 'simhash_db_C', 'simhash_db_D']
        self.REDIS = redis_db
        # self.REDIS = {'simhash_db_A': 1, 'simhash_db_B': 2, 'simhash_db_C': 3, 'simhash_db_D': 4}
        # self.PIPE = {'simhash_db_A': None, 'simhash_db_B': None, 'simhash_db_C': None, 'simhash_db_D': None}
        # redis expire time
        self.expire_time = None
        self.logger = None

    """以下为SimHash功能"""
    def initializer(self):
        dirname = os.path.dirname(__file__)
        lib = ctypes.cdll.LoadLibrary(os.path.join(dirname, 'c++/simhash_c++.so'))
        lib.initializer(os.path.join(dirname, 'c++/jieba.dict.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/hmm_model.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/idf.utf8').encode(encoding='utf-8', errors='strict'),
                        os.path.join(dirname, 'c++/stop_words.utf8').encode(encoding='utf-8', errors='strict'))
        
        # compute
        compute = lib.compute
        compute.argtypes = [ctypes.c_char_p, ctypes.c_int]
        compute.restype = ctypes.c_ulonglong
        self.compute = compute
        
        # compute extract
        compute_extract = lib.compute_extract
        compute_extract.argtypes = [ctypes.c_char_p, ctypes.c_int]
        compute_extract.restype = ctypes.py_object
        self.compute_extract = compute_extract
        
        # HammingDist
        HammingDist = lib.HammingDist
        HammingDist.argtypes = [ctypes.c_ulonglong, ctypes.c_ulonglong]
        HammingDist.restype = ctypes.c_int
        self.HammingDist = HammingDist

    def getSimHash(self, text):
        """
        获取text文本hashcode
        :param text:
        :return:
        """
        hashcode = -1
        try:
            text = text.encode(encoding='utf-8', errors='strict')
            hashcode = self.compute(text, self.f_topN)
        except Exception as e:
            print('simhash compute:', e)
        finally:
            return hashcode

    def getSimHashFeatures(self, text):
        """
        获取text文本hashcode，以及计算hashcode使用的文本特征
        :param text:
        :return:
        """
        hashcode = -1
        features = {}
        try:
            text = text.encode(encoding='utf-8', errors='strict')
            res_list = self.compute_extract(text, self.f_topN)
            for i, tmp in enumerate(res_list):
                if i == 0:
                    hashcode = tmp
                else:
                    features.update({tmp[0] + u'': tmp[1]})
        except Exception as e:
            print('simhash compute and features extract:', e)
        finally:
            return hashcode, features

    def hammingDistance(self, value1, value2):
        """
        计算两个hashcode之间的海明距离
        :param value1:
        :param value2:
        :return:
        """
        dist = -1
        try:
            dist = self.HammingDist(value1, value2)
        except Exception as e:
            print('hamming distance compute:', e)
        finally:
            return dist

    """以下为RedisCheck功能"""
    def init_redis(self, redis_host='127.0.0.1', redis_port=6379, redis_password=None, expire_time=None):
        """
        初始化redis
        :param redis_host: host ip
        :param redis_port: host port
        :param redis_password: redis password
        :param expire_time: expire time
        :return:
        """
        self.expire_time = expire_time

        for k, v in self.REDIS.items():
            pool = redis.ConnectionPool(host=redis_host, port=redis_port, password=redis_password, db=v,
                                        decode_responses=True, max_connections=500, socket_connect_timeout=10)
            redis_connection = redis.Redis(connection_pool=pool)
            self.REDIS.update({k: redis_connection})

    def close_redis(self):
        """
        关闭redis连接（可不用）
        :return:
        """
        for k, v in self.REDIS.iteritems():
            v.connection_pool.disconnect()

    @staticmethod
    def one_count(value):
        """
        计算数字value对应二进制中1的个数
        :param value:
        :return:
        """
        # print(u'value:', bin(value))
        i = 0
        while value:
            value &= (value - 1)
            i += 1
        return i

    def possible_one_count(self, value, threshold=3, totalwidth=64):
        """
        计算数字value对应二进制中1的个数；并且返回在海明距离阈值范围内，所有可能的hashcode对应二进制中1的个数；
        :param value:
        :param threshold:
        :param totalwidth:
        :return:
        """
        # print(u'value:', value, u'one_count', self.one_count(value), bin(value))
        count = self.one_count(value)
        possible_one_list = []
        for i in range(threshold + 1):
            if i == 0:
                possible_one_list.append(count)
                continue
            if count - i >= 0:
                possible_one_list.append(count - i)
            if count + i <= totalwidth:
                possible_one_list.append(count + i)
        return count, possible_one_list

    @staticmethod
    def part_slice(data, part_index, width=16, totalwidth=64):
        """
        将64位simhash分片，返回目标片与剩余片
        :param data:
        :param part_index:
        :param width:
        :param totalwidth:
        :return:
        """
        before_index = (int(totalwidth / width) - part_index + 1) * width
        before_part = data >> before_index
        right_s = data - (before_part << before_index)
        part = right_s >> before_index - width
        behind_part = right_s - (part << before_index - width)
        remain = (before_part << before_index - width) + behind_part
        # print('data:', bin(data))
        # print('before_part:', bin(before_part))
        # print('behind_part:', bin(behind_part))
        # print('part:', bin(part))
        # print('remain:', bin(remain))
        return part, remain

    @staticmethod
    def merge_slice(slice_data):
        """
        合并64位simhash分片
        :param slice_data: 格式为idx_part_remain，如'1_43936_222996178912124'
        :return:
        """
        info_list = slice_data.split('_')
        part_idx = int(info_list[0])
        part = int(info_list[1])
        remain = int(info_list[2])
        move_dist = (4 - part_idx) * 16

        remain_l = remain >> move_dist << move_dist
        remain_r = remain - remain_l
        data = (remain_l << 16) + (part << move_dist) + remain_r

        return data

    def check(self, hashcode, threshold):
        """
        检测hashcode是否在redis存储中
        :param hashcode:
        :param threshold:
        :return: True  -- 存在相似文本，并返回相似文本伪hashcode
                 False -- 不存在相似文本，并返回hashcode待存储信息
        """
        one, possible_one_list = self.possible_one_count(hashcode, threshold=threshold, totalwidth=64)
        keyList = list()
        for db_name, i in zip(self.db_name_list, range(1, 5)):
            members_list, remained, hashcode_x, key_info = self.search_hashcode_keys(hashcode, (db_name, i),
                                                                                     (one, possible_one_list))
            if members_list is None:
                return 2, ''  # hashcode检索过程错误（检查redis数据过期与不过期是否混用，不然就是redis报错）

            for stored_remained_set in members_list:
                if len(stored_remained_set) != 0:
                    for stored_remained in stored_remained_set:
                        hamm_dis = self.hammingDistance(remained, int(stored_remained))
                        if hamm_dis <= threshold:
                            # return 1, hashcode_x  # 存在相似文本，返回数据库相似文本伪hashcode
                            return 1, hashcode_x + '_' + stored_remained  # 存在相似文本，返回数据库相似文本伪hashcode
                        else:
                            pass
                else:
                    pass
            keyList.append(key_info)

        return 0, keyList

    def search_hashcode_keys(self, hashcode, part_info, one_info):
        """
        批量查询hashcode可能的key值
        :param hashcode:
        :param part_info:
        :param one_info:
        :return:
        """
        members_list, remained, hashcode_x, key_info = None, None, None, None
        try:
            (db_name, i) = part_info
            (one, possible_one_list) = one_info
            KeyPart, remained = self.part_slice(hashcode, i, width=16, totalwidth=64)
            KeyPart_str = str(KeyPart)
            remained_str = str(remained)
            with self.REDIS[db_name].pipeline() as pipe:
                for tmp_one in possible_one_list:
                    key = str(tmp_one) + '_' + KeyPart_str
                    if type(self.expire_time) == int and self.expire_time >= 1:
                        pipe.zrange(key, 0, -1)
                    else:
                        pipe.smembers(key)
                members_list = pipe.execute()
            key_info = (str(one) + '_' + KeyPart_str, remained_str, db_name)
            # hashcode_x = str(i) + '_' + KeyPart_str + '_' + remained_str
            hashcode_x = str(i) + '_' + KeyPart_str
        except Exception as e:
            print('redis search error:', e)
            members_list, remained, hashcode_x, key_info = None, None, None, None
        finally:
            return members_list, remained, hashcode_x, key_info

    def store_hashcode(self, keyList):
        """
        存储hashcode到redis中，按key的取值位置分别存在4个db中
        :param keyList:
        :return:
        """
        res = True
        try:
            for key, remained, db_name in keyList:
                save_status = self.REDIS[db_name].sadd(key, remained)
                if save_status == 0:
                    res = False
                    break
        except Exception as e:
            res = False
            print(e)
        finally:
            # redis无回滚，简单实现
            try:
                if res is False:
                    for key, remained, db_name in keyList:
                        if self.REDIS[db_name].sismember(key, remained) is True:
                            self.REDIS[db_name].srem(key, remained)
            except Exception as e:
                print('redis rollback:', e)

            return res

    def store_hashcode_expire(self, keyList):
        """
        存储hashcode到redis中，按key的取值位置分别存在4个db中
        :param keyList:
        :return:
        """
        stt = int(time.time())
        res = True
        try:
            for key, remained, db_name in keyList:
                # save_status = self.REDIS[db_name].zadd(key, remained, stt)
                save_status = self.REDIS[db_name].zadd(key, {remained: stt})
                if save_status == 0:
                    res = False
                    break
        except Exception as e:
            res = False
            print(e)
        finally:
            # redis无回滚，简单实现
            try:
                if res is False:
                    for key, remained, db_name in keyList:
                        if self.REDIS[db_name].zscore(key, remained) is not None:
                            self.REDIS[db_name].zrem(key, remained)
            except Exception as e:
                print('redis rollback:', e)

            return res

    def search_sim_text_in_redis(self, hashcode, threshold=3):
        """
        在redis数据中存储搜索相似文章并存储数据，redis中set存储结构
        :param hashcode: 文本的hashcode
        :param threshold: 判断两个文本是否相似的阈值，海明距离小于等于该值，认为相似
        :return: '0' -- 不存在相似文本，并返回hashcode存储结果
                 '1' -- 存在相似文本，返回相似文本伪hashcode
                 '2' -- 不存在相似文本，但hashcode存储失败
                 '3' -- hashcode检索过程错误
        """
        rel, _ = self.check(hashcode, threshold)
        if rel == 1:
            return 1, _
        elif rel == 0:
            if type(self.expire_time) == int and self.expire_time >= 1:
                store_status = self.store_hashcode_expire(_)
            else:
                store_status = self.store_hashcode(_)

            if store_status is True:
                return 0, 'store %d successful!' % hashcode
            else:
                return 2, 'store %d failed!' % hashcode
        else:
            return 3, 'search %d failed!' % hashcode

    """以下为定时清理redis中过期simhash功能"""
    def delete_job(self):
        """
        定时清理redis中过期simhash
        :return:
        """
        try:
            tmp_msg = 'Start schedule job at %s!' % datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.logger is not None:
                self.logger.info(tmp_msg)
            else:
                print(tmp_msg)

            expire = int(time.time()) - self.expire_time * 3600 * 24
            rem_count = 0
            for k, v in self.REDIS.items():
                keys = v.keys()
                with v.pipeline() as pipe:
                    for key in keys:
                        pipe.zremrangebyscore(key, 0, expire)
                    rem_count_list = pipe.execute()
                    rem_count += sum(rem_count_list)

            tmp_msg = 'Finish schedule job at %s, and total removed %d expired element!'\
                      % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), rem_count)
            if self.logger is not None:
                self.logger.info(tmp_msg)
            else:
                print(tmp_msg)
        except Exception as e:
            tmp_msg = 'Schedule job error at %s: %s'\
                      % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), e)
            if self.logger is not None:
                self.logger.error(tmp_msg)
            else:
                print(tmp_msg)

    @async
    def add_schedule_job(self, scheduler_args=None, logger=None):
        """
        添加定时任务
        :return:
        """
        try:
            flag = False
            scheduler = None
            if type(self.expire_time) == int and self.expire_time >= 1:
                self.logger = logger
                scheduler = BlockingScheduler()

                if scheduler_args['type'] == 'cron':
                    info = scheduler_args['args']
                    scheduler.add_job(self.delete_job, scheduler_args['type'],
                                      day=info['day'], hour=info['hour'], minute=info['minute'], second=info['second'])
                    flag = True
                elif scheduler_args['type'] == 'interval':
                    info = scheduler_args['args']
                    if info.get('seconds', None) is not None:
                        scheduler.add_job(self.delete_job, scheduler_args['type'], seconds=info['seconds'])
                        flag = True

                if flag is True:
                    tmp_msg = 'The expire time is \'%d\' day, and the scheduler is started!' % self.expire_time
                else:
                    tmp_msg = 'The scheduler\'s args is wrong, and please check it!!!'

            else:
                tmp_msg = 'The expire time parameter \'%s\' is error, and program will not start a scheduler.' \
                          ' Please check it!!!' % str(self.expire_time)

            if self.logger is not None:
                self.logger.info(tmp_msg)
            else:
                print(tmp_msg)

            if flag is True and scheduler is not None:
                scheduler.start()
        except Exception as e:
            tmp_msg = 'There is an error when start the scheduler: %s' % e
            if self.logger is not None:
                self.logger.info(tmp_msg)
            else:
                print(tmp_msg)


def main():
    redis_db_info = {'simhash_db_A': 11, 'simhash_db_B': 12, 'simhash_db_C': 13, 'simhash_db_D': 14}
    r_sh = SimHashRedisCheck(redis_db_info)

    text1 = '小明，你妈妈喊你回家吃饭了'
    text2 = '小明，你妈妈喊你回家吃饭'
    text3 = '小明放学回家'
    hashcode1 = r_sh.getSimHash(text1)
    hashcode2 = r_sh.getSimHash(text2)
    hashcode3 = r_sh.getSimHash(text3)

    print(hashcode1)
    print(hashcode2)
    print(hashcode3)
    print(r_sh.hammingDistance(hashcode1, hashcode2))
    print(r_sh.hammingDistance(hashcode1, hashcode3))

    # pdb.set_trace()
    r_sh.init_redis(redis_host='127.0.0.1', redis_port=3360, redis_password='simhashx', expire_time=1)
    # scheduler_args = {'type': 'cron', 'args': {'day': '1-31', 'hour': 2, 'minute': 0, 'second': 0}}
    scheduler_args = {'type': 'interval', 'args': {'seconds': 10}}
    r_sh.add_schedule_job(scheduler_args, logger=None)
    print(r_sh.search_sim_text_in_redis(hashcode1, threshold=3))
    print(r_sh.search_sim_text_in_redis(hashcode2, threshold=3))
    print(r_sh.search_sim_text_in_redis(hashcode3, threshold=3))
    print(u'over')

    # pdb.set_trace()
    # r_sh.delete_job()


if __name__ == '__main__':
    main()
