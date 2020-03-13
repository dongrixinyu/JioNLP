# -*- coding=utf-8 -*-

import os
import re


class Extractor(object):
    ''' 规则抽取器 '''
    def __init__(self):
        #self.
        pass

__all__ = ['extract_email', 'replace_chinese','extract_cellphone', 'extract_cellphone', 'extract_cellphone_location',
           'get_location', 'extract_locations', 'replace_cellphoneNum', 'extract_time', 'extract_name', 'most_common']


class extractor():
    def __init__(self):
        pass

    def extract_email(self, text):
        """
        extract all email addresses from texts<string>
        eg: extract_email('我的email是ifee@baidu.com和dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: email_addresses_list<list>
        """
        if text=='':
            return []
        eng_texts = self.replace_chinese(text)
        eng_texts = eng_texts.replace(' at ','@').replace(' dot ','.')
        sep = ',!?:; ，。！？《》、|\\/'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]

        email_pattern = r'^[a-zA-Z0-9_-]+@[a-zA-Z0-9_-]+(\.[a-zA-Z_-]+)+$'

        emails = []
        for eng_text in eng_split_texts:
            result = re.match(email_pattern, eng_text, flags=0)
            if result:
                emails.append(result.string)
        return emails

    def extract_ids(self, text):
        """
        extract all ids from texts<string>
        eg: extract_ids('my ids is 150404198812011101 m and dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: ids_list<list>
        """
        if text == '':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele) == 18]

        id_pattern = r'^[1-9][0-7]\d{4}((19\d{2}(0[13-9]|1[012])(0[1-9]|[12]\d|30))|(19\d{2}(0[13578]|1[02])31)|(19\d{2}02(0[1-9]|1\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\d{3}(\d|X|x)?$'

        phones = []
        for eng_text in eng_split_texts_clean:
            result = re.match(id_pattern, eng_text, flags=0)
            if result:
                phones.append(result.string.replace('+86','').replace('-',''))
        return phones

    def replace_chinese(self, text):
        """
        remove all the chinese characters in text
        eg: replace_chinese('我的email是ifee@baidu.com和dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: text_without_chinese<str>
        """
        if text=='':
            return []
        filtrate = re.compile(u'[\u4E00-\u9FA5]')
        text_without_chinese = filtrate.sub(r' ', text)
        return text_without_chinese

    def extract_cellphone(self, text, nation):
        """
        extract all cell phone numbers from texts<string>
        eg: extract_email('my email address is sldisd@baidu.com and dsdsd@dsdsd.com,李林的邮箱是eewewe@gmail.com哈哈哈')
        :param: raw_text
        :return: email_addresses_list<list>
        """
        if text=='':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        if nation=='CHN':
            phone_pattern = r'^((\+86)?([- ])?)?(|(13[0-9])|(14[0-9])|(15[0-9])|(17[0-9])|(18[0-9])|(19[0-9]))([- ])?\d{3}([- ])?\d{4}([- ])?\d{4}$'

        phones = []
        for eng_text in eng_split_texts_clean:
            result = re.match(phone_pattern, eng_text, flags=0)
            if result:
                phones.append(result.string.replace('+86','').replace('-',''))
        return phones

    def extract_cellphone_location(self, phoneNum, nation='CHN'):
        """
        extract cellphone number locations according to the given number
        eg: extract_cellphone_location('181000765143',nation=CHN)
        :param: phoneNum<string>, nation<string>
        :return: location<dict>{'phone': '18100065143', 'province': '上海', 'city': '上海', 'zip_code': '200000', 'area_code': '021', 'phone_type': '电信'}
        """
        if nation=='CHN':
            p = Phone()
            loc_dict = p.find(phoneNum)
        if nation!='CHN':
            x = phonenumbers.parse(phoneNum, 'GB')
            if phonenumbers.is_possible_number(x):
                loc_dict = x
        # print(loc_dict)
        return loc_dict

    def get_location(self, word_pos_list):
        """
        get location by the pos of the word, such as 'ns'
        eg: get_location('内蒙古赤峰市松山区')
        :param: word_pos_list<list>
        :return: location_list<list> eg: ['陕西省安康市汉滨区', '安康市汉滨区', '汉滨区']
        """
        location_list = []
        if word_pos_list==[]:
            return []

        for i,t in enumerate(word_pos_list):
            word = t[0]
            nature = t[1]
            if nature == 'ns':
                loc_tmp = word
                count = i + 1
                while count < len(word_pos_list):
                    next_word_pos = word_pos_list[count]
                    next_pos = next_word_pos[1]
                    next_word = next_word_pos[0]
                    if next_pos=='ns' or 'n' == next_pos[0]:
                        loc_tmp += next_word
                    else:
                        break
                    count += 1
                location_list.append(loc_tmp)

        return location_list # max(location_list)

    def extract_locations(self, text):
        """
        extract locations by from texts
        eg: extract_locations('我家住在陕西省安康市汉滨区。')
        :param: raw_text<string>
        :return: location_list<list> eg: ['陕西省安康市汉滨区', '安康市汉滨区', '汉滨区']
        """
        if text=='':
            return []
        seg_list = [(str(t.word), str(t.nature)) for t in HanLP.segment(text)]
        location_list = self.get_location(seg_list)
        return location_list

    def replace_cellphoneNum(self, text):
        """
        remove cellphone number from texts. If text contains cellphone No., the extract_time will report errors.
        hence, we remove it here.
        eg: extract_locations('我家住在陕西省安康市汉滨区，我的手机号是181-0006-5143。')
        :param: raw_text<string>
        :return: text_without_cellphone<string> eg: '我家住在陕西省安康市汉滨区，我的手机号是。'
        """
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele)>=7 and len(ele)<17]
        for phone_num in eng_split_texts_clean:
            text = text.replace(phone_num,'')
        return text

    def replace_ids(self, text):
        """
        remove cellphone number from texts. If text contains cellphone No., the extract_time will report errors.
        hence, we remove it here.
        eg: extract_locations('我家住在陕西省安康市汉滨区，我的身份证号是150404198412011312。')
        :param: raw_text<string>
        :return: text_without_ids<string> eg: '我家住在陕西省安康市汉滨区，我的身份证号号是。'
        """
        if text == '':
            return []
        eng_texts = self.replace_chinese(text)
        sep = ',!?:; ：，.。！？《》、|\\/abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        eng_split_texts = [''.join(g) for k, g in groupby(eng_texts, sep.__contains__) if not k]
        eng_split_texts_clean = [ele for ele in eng_split_texts if len(ele) == 18]

        id_pattern = r'^[1-9][0-7]\d{4}((19\d{2}(0[13-9]|1[012])(0[1-9]|[12]\d|30))|(19\d{2}(0[13578]|1[02])31)|(19\d{2}02(0[1-9]|1\d|2[0-8]))|(19([13579][26]|[2468][048]|0[48])0229))\d{3}(\d|X|x)?$'
        ids = []
        for eng_text in eng_split_texts_clean:
            result = re.match(id_pattern, eng_text, flags=0)
            if result:
                ids.append(result.string)

        for phone_num in ids:
            text = text.replace(phone_num,'')
        return text

    def extract_time(self, text):
        """
        extract timestamp from texts
        eg: extract_time('我于2018年1月1日获得1000万美金奖励。')
        :param: raw_text<string>
        :return: time_info<time_dict> eg: {"type": "timestamp", "timestamp": "2018-11-27 11:00:00"}
        """
        if text=='':
            return []
        tmp_text = self.replace_cellphoneNum(text)
        tmp_text = self.replace_ids(tmp_text)
        tn = TimeNormalizer()
        res = tn.parse(target=tmp_text)  # target为待分析语句，timeBase为基准时间默认是当前时间
        return res

    def extract_name(self, text):
        """
        extract chinese names from texts
        eg: extract_time('急寻王龙，短发，王龙，男，丢失发型短发，...如有线索，请迅速与警方联系：19909156745')
        :param: raw_text<string>
        :return: name_list<list> eg: ['王龙', '王龙']
        """
        if text=='':
            return []
        seg_list = [(str(t.word), str(t.nature)) for t in HanLP.segment(text)]
        names = []
        for ele_tup in seg_list:
            if 'nr' in ele_tup[1]:
                names.append(ele_tup[0])
                # print(ele_tup[0],ele_tup[1])
        return self.most_common(names)

    def most_common(self, content_list):
        """
        return the most common element in a list
        eg: extract_time(['王龙'，'王龙'，'李二狗'])
        :param: content_list<list>
        :return: name<string> eg: '王龙'
        """
        if content_list==[]:
            return None
        if len(content_list)==0:
            return None
        return max(set(content_list), key=content_list.count)





if __name__ == '__main__':

    text = '急寻特朗普，男孩，于2018年11月27号11时在陕西省安康市汉滨区走失。丢失发型短发，...如有线索，请迅速与警方联系：18100065143，132-6156-2938，baizhantang@sina.com.cn 和yangyangfuture at gmail dot com'
    ex = extractor()

    emails = ex.extract_email(text)
    cellphones = ex.extract_cellphone(text,nation='CHN')
    cell_loc = []
    for cell in cellphones:
        cell_loc.append(ex.extract_cellphone_location(cell,'CHN'))

    locations = ex.extract_locations(text)
    times = ex.extract_time(text)
    names = ex.extract_name(text)

    result_dict = {}
    result_dict['email'] = emails
    result_dict['cellphone'] = cellphones
    result_dict['cellphone_location'] = cell_loc
    result_dict['location'] = locations
    result_dict['time'] = times
    result_dict['name'] = names
    for key in result_dict.keys():
        print(key,result_dict[key])























