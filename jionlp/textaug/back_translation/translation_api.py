# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# Email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


"""
调用公开大厂翻译 API 完成文本回译数据增强

DESCRIPTION:
    1、包括百度、谷歌、有道、有道（免费版）、腾讯、讯飞
    2、翻译质量最高的 api 是 Deepl

"""

import os
import pdb
import hmac
import json
import time
import uuid
import base64
import random
import urllib
import hashlib
import datetime
import binascii
import requests

from jionlp import logging


__all__ = ['BaiduApi', 'GoogleApi', 'YoudaoApi', 
           'YoudaoFreeApi', 'TencentApi', 'XunfeiApi']


def check_lang_name(func):
    """ 检查源语言和目标语言的缩写名是否正确 """
    def wrapper(self, *args, **kargs):
        from_lang = kargs['from_lang']
        to_lang = kargs['to_lang']
        exception_string = 'The API does not contain {} language'
        if from_lang not in self.lang_pool:
            raise ValueError(exception_string.format(from_lang))
        if to_lang not in self.lang_pool:
            raise ValueError(exception_string.format(to_lang))
            
        f = func(self, *args, **kargs)
        return f

    return wrapper


def gap_sleep(func):
    """ 两次调用之间的时间间隔，以在每次调用之前等待实现 """
    def wrapper(self, *args, **kargs):
        time.sleep(self.gap_time)
        f = func(self, *args, **kargs)
        return f
    
    return wrapper


def manage_appkey(func):

    def wrapper(self, *args, **kargs):
        # 按索引检索的 appkey
        if self.appkey_obj_list is not None:
            count = 0
            while count <= self.appkey_num:
                self.appkey_obj = self.appkey_obj_list[self.appkey_index]

                count += 1
                try:
                    f = func(self, *args, **kargs)
                    break

                except Exception as err:

                    # 替换密钥的索引
                    if self.appkey_index == self.appkey_num - 1:
                        self.appkey_index = 0
                    else:
                        self.appkey_index += 1

                    # 统计，若循环次数大于密钥个数，即全部密钥被尝试，则退出；否则继续尝试下一个密钥
                    if count < self.appkey_num:
                        logging.warning(
                            'The appkey {} of `{}` is invalid.'.format(
                                json.dumps(self.appkey_obj, ensure_ascii=False),
                                self.__class__.__name__))
                    else:
                        logging.error(err)
                        raise Exception(err)
                        break

        else:
            f = func(self, *args, **kargs)

        return f

    return wrapper


class TranslationApi(object):
    """ 翻译接口基础类，完成

    1、appkey 是否可用的检测与管理
    2、睡眠等待时间，装饰器实现
    3、管理请求头
    4、检查语言缩写编号是否符合要求，装饰器实现

    """
    def __init__(self, appkey_obj_list, gap_time,
                 lang_pool=['zh', 'en']):
        """
        appkey_obj: 调用接口的用户密钥，各个接口各不一样
        gap_time: 两次调用的间隔睡眠时间

        """
        self.gap_time = gap_time
        self.appkey_obj_list = appkey_obj_list

        self.appkey_obj = self.appkey_obj_list[0] if self.appkey_obj_list is not None else None
        self.appkey_num = len(self.appkey_obj_list) if self.appkey_obj_list is not None else 0  # 密钥总个数
        self.appkey_index = 0  # 从第 0 个开始计数
        """
        self.appkey_manager = dict()
        for i, _ in enumerate(self.appkey_obj):
            self.appkey_manager.update(
                {i: {'total_num': 0, 'wrong_num': 0, 'ratio': 1.0}})
        """
        self.lang_pool = lang_pool  # 语言种类池
        
    def manage_appkey(self):
        """ 管理有效的请求 密钥，将结果返回
        针对一个 api 接口，所有的密钥都存于 self.appkey_obj 中，该 list 中存在多个
        密钥，每次调用都从中抽取一个使用，当该密钥的允许次数耗尽，则跳转下一个可用的密钥
        在使用密钥报错时，进行日志跟踪。

        Args:
            self: 无需传参数

        Returns:
            obj: 密钥列表中的其中一个

        """
        if self.appkey_obj is None:
            return None

        # 按照 self.appkey_index 从前向后索引密钥，如报错，则进行下一个密钥请求
        appkey_obj = self.appkey_obj[self.appkey_index]

        return appkey_obj
    
    
class BaiduApi(TranslationApi):
    """ 百度翻译 api 的调用接口

    参考文档：https://api.fanyi.baidu.com/doc/21
    支持语言：中文(zh)、英文(en)、西班牙语(spa)、德文(de)、法语(fra)、
            日语(jp)、俄语(ru)、葡萄牙语(pt)
    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:

    Examples:
        >>> baidu_api = BaiduApi(
                [{'appid': '20200618000498778',
                 'secretKey': 'raHalLakgYitNuzGOoBZ'}])
        >>> text = '她很好看。'
        >>> res = baidu_api(text, from_lang='zh', to_lang='en')
        >>> print(res)

        # She looks good.

    """
    def __init__(self, appkey_obj_list=None, gap_time=0,
                 url='http://api.fanyi.baidu.com/api/trans/vip/translate',
                 lang_pool=['zh', 'en', 'jp', 'spa', 'de',
                            'fra', 'jp', 'ru', 'pt']):
        self.url = url
        super(BaiduApi, self).__init__(appkey_obj_list, gap_time, lang_pool)
        
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='zh', to_lang='en'):
        """ 对一段文本进行翻译 """
        salt = random.randint(32768, 65536)
        salt = str(salt)
        sign = ''.join([self.appkey_obj['appid'], text, 
                        salt, self.appkey_obj['secretKey']])
        sign = hashlib.md5(sign.encode()).hexdigest()

        post_data = {'q': text, 
                     'from': from_lang, 'to': to_lang,
                     'appid': self.appkey_obj['appid'],
                     'salt': salt, 'sign': sign}
        response = requests.post(self.url, data=post_data)

        if response.status_code == 200:
            try:
                response_json = json.loads(response.text)
                return response_json['trans_result'][0]['dst']
            except Exception:
                exception_string = ''.join(
                    ['Http请求失败，状态码：', str(response.status_code),
                     '，错误信息：\n', response.text])
                raise Exception(exception_string)
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)


class GoogleApi(TranslationApi):
    """ Google 翻译 api 的调用接口

    支持语言：中文(zh)、英文(en)、西班牙语(es)、德文(de)、法语(fr)、
            日语(ja)、俄语(ru)

    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:
        str: 目标语言字符串

    Examples:
        >>> google_api = GoogleApi()
        >>> text = '她很好看。'
        >>> res = google_api(text, from_lang='zh', to_lang='ja')
        >>> print(res)

        # She is pretty.

    """
    def __init__(self, appkey_obj_list=None, gap_time=0,
                 url='http://translate.google.cn/translate_a/single',
                 lang_pool=['zh', 'en', 'ja', 'es', 'de', 'fr', 'ru']):
        self.url = url
        super(GoogleApi, self).__init__(appkey_obj_list, gap_time, lang_pool)
        
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='zh', to_lang='en'):
        """ 对一段文本进行翻译 """
        post_data = {'client': 'gtx', 'dt': 't',
                     'dj': 1, 'ie': 'UTF-8',
                     'sl': from_lang, 'tl': to_lang,
                     'q': text}
        # print(to_lang)
        response = requests.post(self.url, data=post_data, timeout=3)
        
        time.sleep(self.gap_time)
        
        if response.status_code == 200:
            try:
                response_json = json.loads(response.text)
                return response_json['sentences'][0]['trans']
            except Exception:
                exception_string = ''.join(
                    ['Http请求失败，状态码：', str(response.status_code),
                     '，错误信息：\n', response.text])
                raise Exception(exception_string)
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)
        
        
class YoudaoApi(TranslationApi):
    """ 有道 翻译 api 的调用接口

    参考文档：http://ai.youdao.com/DOCSIRMA/html/自然语言翻译/API文档/文本翻译服务/文本翻译服务-API文档.html
    支持语言：中文(zh-CHS)、英文(en)、日文(ja)、法文(fr)、西班牙语(es)、
            韩文(ko)、葡萄牙文(pt)、俄语(ru)、德语(de)

    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:
        str: 目标语言字符串

    Examples:
        >>> youdao_api = YoudaoApi(
                appkey_obj_list=[{
                    'appid': '39856bd56b482cfc',
                    'app_secret': '87XpTE63nBVnrR0b6Hy0aTDWlkoq2l4A'}])
        >>> text = '她很好看。'
        >>> res = youdao_api(text, from_lang='zh-CHS', to_lang='ne')
        >>> print(res)

        # She's pretty.

    """
    def __init__(self, appkey_obj_list=None, gap_time=0,
                 url='https://openapi.youdao.com/api',
                 lang_pool=['zh-CHS', 'en', 'ja', 'fr', 'es', 'ko',
                            'pt', 'ru', 'de']):
        self.url = url
        super(YoudaoApi, self).__init__(appkey_obj_list, gap_time, lang_pool)
        
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='zh-CHS', to_lang='en'):
        """ 对一段文本进行翻译 """
        def _encrypt(sign_tr):
            # 对请求做签名
            hash_algorithm = hashlib.sha256()
            hash_algorithm.update(sign_str.encode('utf-8'))
            return hash_algorithm.hexdigest()
        
        def _truncate(text):
            # 对请求文本做删截
            if text is None:
                return None
            size = len(text)
            if size <= 20:
                return text
            else:
                return text[0:10] + str(size) + text[size - 10:size]

        data = dict()
        data['from'] = from_lang
        data['to'] = to_lang
        data['signType'] = 'v3'
        curtime = int(time.time())
        data['curtime'] = curtime

        salt = str(uuid.uuid1())
        sign_str = ''.join(
            [self.appkey_obj['appid'], _truncate(text),
             salt, str(curtime), self.appkey_obj['app_secret']])
        sign = _encrypt(sign_str)

        data['appKey'] = self.appkey_obj['appid']
        data['q'] = text
        data['salt'] = salt
        data['sign'] = sign

        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        response = requests.post(self.url, data=data, headers=headers)
        
        response_json = json.loads(response.text)
        if response.status_code == 200 and 'translation' in response_json:
            return response_json['translation'][0]
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)
    
    
class YoudaoFreeApi(TranslationApi):
    """ 有道免费的翻译 api 的调用接口，该接口模型与非免费版结果不一致

    参考文档：http://fanyi.youdao.com/
    支持语言：中文(zh-CHS)、英文(en)，属于 api 接口自动检测
    限制条件：
        1、免费试用

    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:
        str: 目标语言字符串

    Examples:
        >>> youdao_api = YoudaoFreeApi()
        >>> text = '她很好看。'
        >>> res = youdao_api(text, from_lang='zh-CHS', to_lang='en')
        >>> print(res)

        # She looks very nice.

    """
    def __init__(self, appkey_obj_list=None, gap_time=0,
                 url='http://fanyi.youdao.com/translate?&doctype=json&type=AUTO&i=',
                 lang_pool=['zh-CHS', 'en']):
        self.url = url
        super(YoudaoFreeApi, self).__init__(
            appkey_obj_list, gap_time, lang_pool)
        
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='zh-CHS', to_lang='en'):
        """ 对一段文本进行翻译 """
        response = requests.get(self.url + text)
        
        response_json = json.loads(response.text)
        if response.status_code == 200 and 'translateResult' in response_json:
            return response_json['translateResult'][0][0]['tgt']
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)


class TencentApi(TranslationApi):
    """ 腾讯 翻译 api 的调用接口

    参考文档：https://cloud.tencent.com/document/product/551/15619
    支持语言：中文(zh)、英文(en)、日文(ja)、法文(fr)、西班牙语(es)、
            韩文(ko)、葡萄牙文(pt)、俄语(ru)、德语(de)
    限制条件：
        1、默认接口请求频率限制：5次/秒
        2、文本翻译的每月免费额度为5百万字符
        3、单次请求的字符数不超过 2000（一个汉字、字母、标点都计为一个字符）

    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:
        str: 目标语言字符串

    Examples:
        >>> tencent_api = TencentApi(
                [{"project_id": "0",
                "secret_id": "AKID5zGGuInJwmLehbyKyYXGS3NXOXYLE96o",
                "secret_key": "buwiGXXifLt888rKQLwGH3asuhFbmeCX"}])
        >>> text = '她很好看。'
        >>> res = tencent_api(text, from_lang='zh', to_lang='en')
        >>> print(res)

        # She's pretty.

    """
    def __init__(self, appkey_obj_list=None, gap_time=1,
                 url='https://tmt.tencentcloudapi.com/',
                 host_name='tmt.tencentcloudapi.com',
                 lang_pool=['zh', 'en', 'ja', 'fr', 'es', 'ko',
                            'pt', 'ru', 'de']):
        self.url = url
        self.host_name = host_name
        super(TencentApi, self).__init__(appkey_obj_list, gap_time, lang_pool)
        headers = {'Content-Type': 'application/json'}
        
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='zh-CHS', to_lang='en'):
        """ 对一段文本进行翻译 """
        data = dict()
        data['Action'] = 'TextTranslate'
        data['Nonce'] = int(random.random() * 10000)
        data['ProjectId'] = self.appkey_obj['project_id']
        data['Region'] = 'ap-chengdu'
        data['SecretId'] = self.appkey_obj['secret_id']
        data['SignatureMethod'] = 'HmacSHA256'
        data['Source'] = from_lang
        data['SourceText'] = text
        data['Target'] = to_lang
        curtime = str(int(time.time()))
        data['Timestamp'] = curtime
        data['Version'] = '2018-03-21'

        # 用以上数据 data 进行签名
        request_str = ''.join(
            ['GET', self.host_name, '/?', 
             self.dict_to_str(data)])
        data['Signature'] = urllib.parse.quote(
            self.sign(request_str, data['SignatureMethod']))
        url = self.url + '?' + self.dict_to_str(data)
        
        response = requests.get(url)
        
        response_json = json.loads(response.text)
        if response.status_code == 200:
            # print(response_json['Response']['TargetText'])
            return response_json['Response']['TargetText']
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)
            
    def sign(self, sign_str, sign_method):
        """ 该方法主要是实现腾讯云的签名功能

        param secret_key: secret_key
        param sign_str: 传递进来字符串，加密时需要使用
        param sign_method: 加密方法
        """
        sign_str = sign_str.encode('utf-8')
        secret_key = self.appkey_obj['secret_key'].encode('utf-8')

        digest_mod = ''
        # 根据参数中的sign_method来选择加密方式
        if sign_method == 'HmacSHA256':
            digest_mod = hashlib.sha256
        elif sign_method == 'HmacSHA1':
            digest_mod = hashlib.sha1

        # 完成加密，生成加密后的数据
        hashed = hmac.new(secret_key, sign_str, digest_mod)
        base64 = binascii.b2a_base64(hashed.digest())[:-1]
        base64 = base64.decode()
        return base64
    
    @staticmethod
    def dict_to_str(dict_data):
        # 将 dict 转为 list 并且拼接成字符串
        temp_list = list()
        for eve_key, eve_value in dict_data.items():
            temp_list.append(str(eve_key) + '=' + str(eve_value))
        return '&'.join(temp_list)

    
class XunfeiApi(TranslationApi):
    """ 讯飞免费的翻译 api 的调用接口

    参考文档：https://www.xfyun.cn/doc/nlp/xftrans/API.html
            https://www.xfyun.cn/services/xftrans
    支持语言：中文(cn)、英文(en)、日文(ja)、法文(fr)、西班牙语(es)、
            俄语(ru)
    限制条件：
        1、一年 200 万字符免费
        2、字符数以翻译的源语言字符长度为标准计算。一个汉字、英文字母、标点符号等，均计为一个字符。
        3、单次请求长度控制在256个字符以内。
        4、不支持源语言语种自动识别

    Args:
        from_lang: 输入源语言
        to_lang: 输入目标语言

    Return:
        str: 目标语言的结果字符串

    Examples:
        >>> xunfei_api = XunfeiApi(
                appkey_obj_list=[{
                    "appid": "5f5846b1",  # 应用ID（到控制台获取）
                    # 接口APIKey（到控制台机器翻译服务页面获取）
                    "api_key": "52465bb3de9a258379e6909c4b1f2b4b",
                    # 接口APISercet（到控制台机器翻译服务页面获取）
                    "secret": "b21fdc62a7ed0e287f31cdc4bf4ab9a3"}])
        >>> text = '她很好看。'
        >>> res = xunfei_api(text, from_lang='cn', to_lang='en')
        >>> print(res)

        # She's good-looking.

    """
    def __init__(self, appkey_obj_list=None, gap_time=0,
                 url='https://itrans.xfyun.cn/v2/its',
                 lang_pool=['cn', 'en', 'ja', 'fr', 'es', 'ru']):
        self.host = 'itrans.xfyun.cn'
        self.request_uri = "/v2/its"
        # 设置 url
        self.url = 'https://' + self.host + self.request_uri
        self.url = url
        self.http_method = "POST"
        self.algorithm = "hmac-sha256"
        self.http_proto = "HTTP/1.1"
        
        # 设置当前时间
        curtime_utc = datetime.datetime.utcnow()
        self.date = self.httpdate(curtime_utc)

        super(XunfeiApi, self).__init__(
            appkey_obj_list, gap_time, lang_pool)

    @staticmethod
    def hashlib_256(res):
        m = hashlib.sha256(bytes(res.encode(encoding='utf-8'))).digest()
        result = "SHA-256=" + base64.b64encode(m).decode(encoding='utf-8')
        return result

    @staticmethod
    def httpdate(dt):
        """
        Return a string representation of a date according to RFC 1123
        (HTTP/1.1).

        The supplied date must be in UTC.
        """
        weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][dt.weekday()]
        month = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 
                 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][dt.month - 1]
        return '{0:s}, {1:02d} {2:s} {3:04d} {4:02d}:{5:02d}:{6:02d} GMT'.format(
            weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)
        
    def generate_signature(self, digest):
        signature_str = 'host: ' + self.host + '\n'
        signature_str += 'date: ' + self.date + '\n'
        signature_str += ''.join([self.http_method, ' ', self.request_uri,
                                 ' ', self.http_proto, '\n'])
        signature_str += "digest: " + digest
        signature = hmac.new(
            bytes(self.appkey_obj['secret'].encode(encoding='utf-8')),
            bytes(signature_str.encode(encoding='utf-8')),
            digestmod=hashlib.sha256).digest()
        result = base64.b64encode(signature)
        return result.decode(encoding='utf-8')

    def init_header(self, data):
        digest = self.hashlib_256(data)
        sign = self.generate_signature(digest)
        auth_header = 'api_key="{0:s}", algorithm="{1:s}", ' \
                      'headers="host date request-line digest", ' \
                      'signature="{2:s}"'.format(self.appkey_obj['api_key'], self.algorithm, sign)
        
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Method': 'POST',
            'Host': self.host,
            'Date': self.date,
            'Digest': digest,
            'Authorization': auth_header
        }
        return headers
    
    def get_body(self, text, from_lang='cn', to_lang='en'):
        content = str(base64.b64encode(text.encode('utf-8')), 'utf-8')
        post_data = {
            'common': {'app_id': self.appkey_obj['appid']},
            'business': {
                'from': from_lang,
                'to': to_lang,
            },
            'data': {
                'text': content,
            }
        }
        body = json.dumps(post_data)
        return body
    
    @check_lang_name
    @gap_sleep
    @manage_appkey
    def __call__(self, text, from_lang='cn', to_lang='en'):
        """ 对一段文本进行翻译 """
        if self.appkey_obj['appid'] == '':
            raise ValueError('APPID 为空')
        if self.appkey_obj['api_key'] == '':
            raise ValueError('APIKEY 为空')
        if self.appkey_obj['secret'] == '':
            raise ValueError('APISecret 为空')
        
        # 准备待传输数据
        body = self.get_body(text, from_lang=from_lang,
                             to_lang=to_lang)
        headers = self.init_header(body)

        response = requests.post(
            self.url, data=body, headers=headers, timeout=8)

        response_json = json.loads(response.text)
        if response.status_code == 200:
            if str(response_json['code']) != '0':
                print(response_json)
                raise AttributeError(''.join([
                    '请前往https://www.xfyun.cn/document/error-code?code=',
                    str(response_json['code']), '查询解决办法']))

            return response_json['data']['result']['trans_result']['dst']
        else:
            exception_string = ''.join(
                ['Http请求失败，状态码：', str(response.status_code),
                 '，错误信息：\n', response.text])
            raise Exception(exception_string)
    

if __name__ == '__main__':
    '''
    '''
    baidu_api = BaiduApi(
        {'appid': '20200618000498778', 
         'secretKey': 'raHalLakgYitNuzGOoBZ'},
        0)
    text = '她很好看。'
    res = baidu_api(text, from_lang='zh', to_lang='en')
    print(res)
    '''
    google_api = GoogleApi()
    text = '她很好看。'
    res = google_api(text, from_lang='zh', to_lang='en')
    print(res)
    
    
    youdao_api = YoudaoApi(
        appkey_obj={'appid': '39856bd56b482cfc',
                    'app_secret': '87XpTE63nBVnrR0b6Hy0aTDWlkoq2l4A'})
    text = '她很好看。'
    res = youdao_api(text, from_lang='zh-CHS', to_lang='en')
    print(res)
    
    
    youdao_api = YoudaoFreeApi()
    text = '她很好看。'
    res = youdao_api(text, from_lang='zh-CHS', to_lang='en')
    print(res)
    
    tencent_api = TencentApi(
        {"project_id": "0",
            "secret_id": "AKID5zGGuInJwmLehbyKyYXGS3NXOXYLE96o",
            "secret_key": "buwiGXXifLt888rKQLwGH3asuhFbmeCX"})
    text = '她很好看。'
    res = tencent_api(text, from_lang='zh', to_lang='en')
    print(res)
    
    
    xunfei_api = XunfeiApi(
        appkey_obj={
        # 应用ID（到控制台获取）
        "appid": "5f5846b1",
        # 接口APIKey（到控制台机器翻译服务页面获取）
        "api_key": "52465bb3de9a258379e6909c4b1f2b4b",
        # 接口APISercet（到控制台机器翻译服务页面获取）
        "secret": "b21fdc62a7ed0e287f31cdc4bf4ab9a3"})
    text = '她很好看。'
    start_time = time.time()
    res = xunfei_api(text, from_lang='cn', to_lang='en')
    print(time.time() - start_time)
    print(res)
    '''
