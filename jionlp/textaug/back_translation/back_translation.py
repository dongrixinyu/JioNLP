# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import traceback

from multiprocessing import Pool, Manager  # , Lock, RLock

from jionlp import logging
from jionlp.util.time_it import TimeIt

from .translation_api import BaiduApi, GoogleApi, YoudaoApi, \
    YoudaoFreeApi, TencentApi, XunfeiApi


class BackTranslation(object):
    """ 回译接口，集成多个公开免费试用机器翻译接口，进行数据增强
    即，给定一条文本，分别使用多个接口，对数据进行回译增强，该接口
    实现了针对各个厂商的 API 的并行处理

    Args:
        text(str): 待回译文本

    Return:
        list(str): 回译得到的文本 list

    Example:
        >>> import jionlp as jio
        >>> xunfei_api = jio.XunfeiApi(
                [{"appid": "5f5846b1",
                  "api_key": "52465bb3de9a258379e6909c4b1f2b4b",
                  "secret": "b21fdc62a7ed0e287f31cdc4bf4ab9a3"}])
        >>> tencent_api = jio.TencentApi(
                [{"project_id": "0",
                  "secret_id": "AKID5zGGuInJwmLehbyKyYXGS3NXOXYLE96o",
                  "secret_key": "buwiGXXifLt888rKQLwGH3dsfsdmeCX"},  # 错误的 api
                 {"project_id": "0",
                  "secret_id": "AKID5zGGuInJwmLehbyKyYXGS3NXOXYLE",
                  "secret_key": "buwiGXXifLt888rKQLwGH3asuhFbmeCX"}])  # 错误的 api
        >>> youdao_free_api = jio.YoudaoFreeApi()
        >>> youdao_api = jio.YoudaoApi(
                [{'appid': '39856bd56b482cfc',
                  'app_secret': '87XpTE63nBVnrR0b6Hy0aTDWlkoq2l4A'}])
        >>> google_api = jio.GoogleApi()
        >>> baidu_api = jio.BaiduApi(
                [{'appid': '20200618000498778',
                  'secretKey': 'raHalLakgYitNuzGOoB2'},  # 错误的密钥
                 {'appid': '20200618000498778',
                  'secretKey': 'raHalLakgYitNuzGdsoB2'},  # 错误的密钥
                 {'appid': '20200618000498778',
                  'secretKey': 'raHalLakgYitNuzGOoBZ'}], gap_time=0.5)

        >>> apis = [baidu_api, youdao_api, google_api,
                    youdao_free_api, tencent_api, xunfei_api]

        >>> back_trans = jio.BackTranslation(mt_apis=apis)
        >>> text = '饿了么凌晨发文将推出新功能，用户可选择是否愿意多等外卖员 5 分钟，你愿意多等这 5 分钟吗？'
        >>> result = back_trans(text)
        >>> print(result)

        # ['饿了么将在凌晨推出一项新功能。用户可以选择是否愿意额外等待外卖人员5分钟。您想多等5分钟吗？',
        #  '《饿了么》将在凌晨推出一档新节目。用户可以选择是否愿意等待餐饮人员多花5分钟。您愿意再等五分钟吗？',
        #  'Ele.me将在早晨的最初几个小时启动一个新的功能。用户可以选择是否准备好再等5分钟。你不想再等五分钟吗？',
        #  'Eleme将在清晨推出新的功能。用户可以选择是否愿意再等5分钟工作人员。你想再等五分钟吗？']

    """

    def __init__(self, mt_apis=list()):
        self.chinese_alias = ['zh', 'cn']
        self.mt_apis = mt_apis
        self.api_num = len(mt_apis)
        # self.lock = Lock()

    def __call__(self, text):
        api_pool = Pool(processes=self.api_num, )
        # initializer=self.get_lock,#)
        # initargs=())

        with TimeIt(name='total'):
            with Manager() as manager:
                result_list = manager.list()
                try:
                    # res = self.iter_api_by_language_wrapper(
                    #    text, self.mt_apis[5], result_list)
                    # pdb.set_trace()

                    for cur_api in self.mt_apis:
                        api_pool.apply_async(
                            self.iter_api_by_language_wrapper,
                            (text, cur_api, result_list,))

                    api_pool.close()
                except Exception as err:
                    traceback.print_exc()
                    api_pool.terminate()
                api_pool.join()

                back_tran_result = [item for item in iter(result_list)]

        # 过滤回译结果
        back_tran_result = self.filter_results(text, back_tran_result)
        return back_tran_result

    def iter_api_by_language_wrapper(self, text, mt_api, manager):
        try:
            with TimeIt(name=mt_api.__class__.__name__) as ti:
                res = self.iter_api_by_language(text, mt_api)

        except Exception as err:
            traceback.print_exc()
            logging.error(err)
        # with self.lock:
        # lock.acquire()
        manager.extend(res)
        # lock.release()

    def iter_api_by_language(self, text, mt_api):
        """ 迭代 某个 api 的所有可选的目标语言，并回译回去

        Args:
            text(str): 待回译文本
            mt_api: 某个翻译的 api 对象

        Return:
            list(str): 由该 mt_api 回译得到的文本 list

        """
        # 准备待遍历外文语言标记符
        lang_list = mt_api.lang_pool

        def _filter_chinese(lang_list):
            # 过滤掉中文的标记，仅保留外文标记，用于遍历
            chinese_lang = None
            foreign_lang_list = list()
            for lang in lang_list:
                match_flag = False
                for chinese_ali in self.chinese_alias:
                    if chinese_ali in lang:
                        match_flag = True
                        chinese_lang = lang
                        break
                if not match_flag:
                    foreign_lang_list.append(lang)

            return foreign_lang_list, chinese_lang

        foreign_lang_list, chinese_lang = _filter_chinese(lang_list)

        # 遍历所有的回译调用结果
        api_result_list = list()
        for foreign_lang in foreign_lang_list:
            try:
                tmp = mt_api(text, from_lang=chinese_lang, to_lang=foreign_lang)
                result = mt_api(tmp, from_lang=foreign_lang, to_lang=chinese_lang)
                api_result_list.append(result)
            except Exception as err:
                traceback.print_exc()

        return api_result_list

    @staticmethod
    def filter_results(text, back_tran_results):
        """ 对得到的数据增强结果做过滤，
        1、去除重复的结果
        2、按照中-外-中，字符长度相差不可过大原则，去除一部分结果 """
        back_tran_results = list(set(back_tran_results))

        def _length_filter(orig_text, trans_line):
            # 将原始的文本与翻译的句子做长短对比
            # 规则很多，暂按最简单操作
            orig_len = len(orig_text)
            tran_len = len(trans_line)
            if tran_len == 0:
                return False
            if (orig_len / tran_len) < 1 / 3 or (orig_len / tran_len) > 3:
                return False
            else:
                return True

        back_tran_results = [line for line in back_tran_results
                             if _length_filter(text, line)]
        return back_tran_results


if __name__ == '__main__':
    xunfei_api = XunfeiApi(
        appkey_obj={
            "appid": "5f5846b1",
            "api_key": "52465bb3de9a258379e6909c4b1f2b4b",
            "secret": "b21fdc62a7ed0e287f31cdc4bf4ab9a3"})
    tencent_api = TencentApi(
        {"project_id": "0",
         "secret_id": "AKID5zGnJwmLehbyKyYXGS3NXOE96o",
         "secret_key": "buwiGXt888rKQLwGH3asumeCX"})
    youdao_free_api = YoudaoFreeApi()
    youdao_api = YoudaoApi(
        appkey_obj={'appid': '39856bd56b482cfc',
                    'app_secret': '87XpTE63nBVnrR0b6Hy0aTDWlkoq2l4A'})
    google_api = GoogleApi()
    baidu_api = BaiduApi(
        {'appid': '20200618000498778',
         'secretKey': 'raHalLakgYitNuzGOoBZ'},
        1)

    apis = [baidu_api, youdao_api,  # google_api,
            youdao_free_api, tencent_api, xunfei_api]

    back_trans = BackTranslation(mt_apis=apis)
    text = '饿了么凌晨发文将推出新功能，用户可选择是否愿意多等外卖员 5 分钟，你愿意多等这 5 分钟吗？'
    result = back_trans(text)
    print(result)
