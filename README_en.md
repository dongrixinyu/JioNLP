<p align="center">
    <a alt="jionlp logo">
        <img src="../../blob/master/image/jionlp_logo.jpg" style="width:300px;height:100px">
    </a>
</p>
<p align="center">
    <a alt="License">
        <img src="https://img.shields.io/github/license/dongrixinyu/JioNLP?color=crimson" /></a>
    <a alt="Size">
        <img src="https://img.shields.io/badge/size-15.6m-orange" /></a>
    <a alt="Downloads">
        <img src="https://pepy.tech/badge/jionlp/month" /></a>
    <a alt="Version">
        <img src="https://img.shields.io/badge/version-1.5.21-green" /></a>
    <a href="https://github.com/dongrixinyu/JioNLP/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/dongrixinyu/JioNLP?color=blue" /></a>
</p>

### &emsp;&emsp; ——JioNLP：A Python Lib for Chinese NLP Preprocessing & Parsing
### &emsp;&emsp; ——installation method：```pip install jionlp```
### &emsp;&emsp; ——[JioNLP online](http://www.jionlp.com/) is provided for a quick trial of some functions
### &emsp;&emsp; ——[中文版 README.md](https://github.com/dongrixinyu/JioNLP)

- Doing NLP tasks, need to clean and filter the corpus? Use JioNLP
- Doing NLP tasks, need to extract key info? Use JioNLP
- Doing NLP tasks, need to do text augmentation? Use JioNLP
- Doing NLP tasks, need to get radical, pinyin, traditional info of Chinese character? Use JioNLP

#### In short, JioNLP offers a bundle of NLP task preprocessing and parsing tools, which is accurate, efficient, easy to use.
#### Main functions include: clean text, delete HTML tags, exceptional chars, redundent chars, convert full-angle chars to half-angle, extract email, qq, phone-num, parenthesis info, id cards, ip, url, money and case, nums, parse time text, extract keyphrase, load Chinese dictionaries, do Chinese text augmentation
 

#### Updata 2022-05-26
## Update [**Keyphrase extraction**](../../wiki/Gadget-说明文档#user-content-关键短语抽取) 

#### jio.keyphrase.extract_keyphrase: extract keyphrases from a Chinese text
```
>>> import jionlp as jio
>>> text = '浑水创始人：七月开始调查贝壳，因为“好得难以置信” 2021年12月16日，做空机构浑水在社交媒体上公开表示，正在做空美股上市公司贝壳...'

>>> keyphrases = jio.keyphrase.extract_keyphrase(text)
>>> print(keyphrases)
>>> print(jio.keyphrase.extract_keyphrase.__doc__)

# ['浑水创始人', '开始调查贝壳', '做空机构浑水', '美股上市公司贝壳', '美国证监会']

```


#### Update 2021-10-25
## Update [money text parser](../../wiki/正则抽取与解析-说明文档#user-content-货币金额解析)

#### jio.parse_money: parse a given money text to get a number, money case and definition of the money

```python
import jionlp as jio
text_list = ['约4.287亿美元', '两个亿卢布', '六十四万零一百四十三元一角七分', '3000多欧元', '三五佰块钱', '七百到九百亿泰铢'] 
moneys = [jio.parse_money(text) for text in text_list]

# 约4.287亿美元: {'num': '428700000.00', 'case': '美元', 'definition': 'blur'}
# 两个亿卢布: {'num': '200000000.00', 'case': '卢布', 'definition': 'accurate'}
# 六十四万零一百四十三元一角七分: {'num': '640143.17', 'case': '元', 'definition': 'accurate'}
# 3000多欧元: {'num': ['3000.00', '4000.00'], 'case': '欧元', 'definition': 'blur'}
# 三五百块钱: {'num': ['300.00', '500.00'], 'case': '元', 'definition': 'blur'}
# 七百到九百亿泰铢: {'num': ['70000000000.00', '90000000000.00'], 'case': '泰铢', 'definition': 'blur'}

```

#### Update 2022-03-07
## Update [Time sementic parser](../../wiki/时间语义解析-说明文档#user-content-时间语义解析)

#### jio.parse_time: parse a given time string

``` python
import time
import jionlp as jio
res = jio.parse_time('今年9月', time_base={'year': 2021})
res = jio.parse_time('零三年元宵节晚上8点半', time_base=time.time())
res = jio.parse_time('一万个小时')
res = jio.parse_time('100天之后', time.time())
res = jio.parse_time('四月十三', lunar_date=False)
res = jio.parse_time('每周五下午4点', time.time(), period_results_num=2)
print(res)

# {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-09-01 00:00:00', '2021-09-30 23:59:59']}
# {'type': 'time_point', 'definition': 'accurate', 'time': ['2003-02-15 20:30:00', '2003-02-15 20:30:59']}
# {'type': 'time_delta', 'definition': 'accurate', 'time': {'hour': 10000.0}}
# {'type': 'time_span', 'definition': 'blur', 'time': ['2021-10-22 00:00:00', 'inf']}
# {'type': 'time_period', 'definition': 'accurate', 'time': {'delta': {'day': 7}, 
# {'type': 'time_point', 'definition': 'accurate', 'time': ['2022-04-13 00:00:00', '2022-04-13 23:59:59']}
#  'point': {'time': [['2021-07-16 16:00:00', '2021-07-16 16:59:59'],
#                     ['2021-07-23 16:00:00', '2021-07-23 16:59:59']], 'string': '周五下午4点'}}}

```

- [About**time sementic parser**](../../wiki/时间语义解析-说明文档)
- [All test cases](../../blob/master/test/test_time_parser.py)


## Installation

- python>=3.6 and github
```
$ git clone https://github.com/dongrixinyu/JioNLP
$ cd ./JioNLP
$ pip install .
```
- pip
```
$ pip install jionlp
```


## Features

- import jionlp and check the main funcs and annotatiosn
```
>>> import jionlp as jio
>>> jio.help()  # input the keywords, such as “回译”, which means back translation
>>> dir(jio)
>>> print(jio.extract_parentheses.__doc__)
```
- If in Linux, the following command is a replacement of `jio.help()`.
```
$ jio_help
```

- **Star⭐** represents excellent features
### 1.Gadgets

| Features   | Function name   |Description   |Star   |
|--------|-------|-------|-------|
|[**help search tool**](../../wiki/Gadget-说明文档#user-content-查找帮助) |help|if you have no idea of JioNLP features, this tool can help you to scan with keywords | |
|[**time sementic parser**](../../wiki/时间语义解析-说明文档#user-content-时间语义解析) |parse_time|get the timestamp and span of a given time text |⭐|
|[**keyphrase extraction**](../../wiki/Gadget-说明文档#user-content-关键短语抽取) |extract_keyphrase|extract the keyphrases of a given text |⭐|
|[extractive **summary**](../../wiki/Gadget-说明文档#user-content-抽取式文本摘要) |extract_summary|extract the summary of a given text | |
|[**stopwords filter**](../../wiki/Gadget-说明文档#user-content-去除停用词) |remove_stopwords|delete the stopwords of a given words list generated from a text |⭐|
|[**sentence spliter**](../../wiki/Gadget-说明文档#user-content-文本分句) |split_sentence|split a text to sentences |⭐|
|[**location parser**](../../wiki/Gadget-说明文档#user-content-地址解析) |parse_location|get the **province, city, county, town and countryside** name of a location text |⭐|
|[telephone number parser](../../wiki/Gadget-说明文档#user-content-电话号码归属地运营商解析) |phone_location<br>cell_phone_location<br>landline_phone_location |get the **province, city, communication operators** of a telephone number ||
|[news **location recognizer**](../../wiki/Gadget-说明文档#user-content-新闻地名识别) |recognize_location|get the **country, province, city, county** name of a news text |⭐|
|[**solar lunar**date conversion](../../wiki/Gadget-说明文档#user-content-公历农历日期互转)|lunar2solar<br>solar2lunar |translate a lunar (solar) date to the solar (lunar) date ||
|[**ID cards** parser](../../wiki/Gadget-说明文档#user-content-身份证号码解析) |parse_id_card|get the **province, city, conty, birthday, gender, checking code** of a given Chinese ID card number |⭐|
|[**idiom solitaire**](../../wiki/Gadget-说明文档#user-content-成语接龙) |idiom_solitaire|a word game that a list of Chinese idioms which the first char of the latter idiom has the same pronunciation with the last char of the former idiom ||
|[**tranditional** chars to **simplified** chars](../../wiki/Gadget-说明文档#user-content-繁体转简体字) |tra2sim|translate traditional characters to simplified version | |
|[**simplified** chars to **traditional** chars](../../wiki/Gadget-说明文档#user-content-简体转繁体字) |sim2tra|translate simplified characters to traditional version | |
|[characters to **pinyin**](../../wiki/Gadget-说明文档#user-content-汉字转拼音) |pinyin|get the pinyin of chinese chars to add pronunciation info to the NLP model input |⭐ |
|[characters to **radical**](../../wiki/Gadget-说明文档#user-content-汉字转偏旁与字形) |char_radical|get the radical info of Chinese chars to add to the NLP model input |⭐ |
|[money **numbers to chars**](../../wiki/正则抽取与解析-说明文档#user-content-金额数字转汉字)|money_num2char|get the character of a given money number | |

### 2.Text Augmentation

- [**Description of all text augmentation methods**](../../wiki/数据增强-说明文档#user-content-数据增强方法对比)

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|------|
|[**back translation**](../../wiki/数据增强-说明文档#user-content-回译数据增强) |BackTranslation|get augmented text via back translation |⭐ |
|[**swap char position**](../../wiki/数据增强-说明文档#user-content-邻近汉字换位) |swap_char_position|get augmented text via swapping the position of adjacent chars | |
|[**homophone substitution**](../../wiki/数据增强-说明文档#user-content-同音词替换) |homophone_substitution|replace chars with the same pronunciation to get augmented text |⭐ |
|[randomly **add & delete chars**](../../wiki/数据增强-说明文档#user-content-随机增删字符) |random_add_delete|add and delete chars randomly in the text to get augmented text | |
|[NER **entity replacement**](../../wiki/数据增强-说明文档#user-content-ner实体替换) |replace_entity|replace the entity of the text via dictionary to get augmented text |⭐ |


### 3.Key info extraction and parsing with regular expression

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|-------|
|[**clean text**](../../wiki/正则抽取与解析-说明文档#user-content-清洗文本) |clean_text|delete exceptional, redundent chars, HTML tags, parenthesis, url, email, phone nums |⭐ |
|[extract **E-mail**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-e-mail) |extract_email|extract email info from text | |
|[parse **money text**](../../wiki/正则抽取与解析-说明文档#user-content-货币金额解析) |extract_money|parse money text |⭐ |
|[extract **phone number**](../../wiki/正则抽取与解析-说明文档#user-content-抽取电话号码) |extract_phone_number| extract landline and telephone number | |
|[extract Chinese **ID card** ](../../wiki/正则抽取与解析-说明文档#user-content-抽取身份证号) |extract_id_card|extract Chinese ID card info and parse it with **jio.parse_id_card**| |
|[extract **QQ**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-qq) |extract_qq|extract tencent QQ number | |
|[extract **URL**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-url-超链接) |extract_url|extract URL info | |
|[extract **IP**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-ip-地址) |extract_ip_address|extract IPv4 address| |
|[extract **parenthesis** info](../../wiki/正则抽取与解析-说明文档#user-content-抽取文本括号信息) |extract_parentheses|extract parenthesis info wrapped by **{}「」[]【】()（）<>《》** |⭐ |
|[delete **E-mail**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-e-mail) |remove_email|delete E-mail info from the given text | |
|[delete **URL**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-url) |remove_url |delete URL info| |
|[delete **phone num**](../../wiki/正则抽取与解析-说明文档#user-content-删除电话号码) |remove_phone_number|delete telephone numbers | |
|[delete **IP**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-ip-地址)|remove_ip_address|delete IP address | |
|[delete **Chinese ID card**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的身份证号) |remove_id_card|delete Chinese ID card info | |
|[delete **QQ**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-qq-号) |remove_qq|delete qq numbers| |
|[delete **HTML tags**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-html-标签) |remove_html_tag|delete HTML tags | |
|[delete **parenthesis** info](../../wiki/正则抽取与解析-说明文档#user-content-删除文本括号信息) |remove_parentheses|delete parenthesis info wrapped by **{}「」[]【】()（）<>《》** | |
|[delete exceptional chars](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的异常字符) |remove_exception_char|delete exceptional chars | |

### 4.file reader and writer

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|-------|
|[**read file by iteration**](../../wiki/文件读写-说明文档#user-content-文件读取iter) |read_file_by_iter |read file by iteration to get a json list ||
|[**read file by line**](../../wiki/文件读写-说明文档#user-content-文件读取list) |read_file_by_line |read file to get a json list |⭐ |
|[write file by line](../../wiki/文件读写-说明文档#user-content-文件写入) |write_file_by_line| write a list of text to the file |⭐ |
|[get the time consumption](../../wiki/文件读写-说明文档#user-content-计时器) |TimeIt | get the seconds of a given programming consuming | |
|[jionlp logger](../../wiki/文件读写-说明文档#user-content-日志处理设置函数) |set_logger |the logger used by jionlp | |

### 5.dictionaries

| Features   | Function name   |Description   |Star   |
|-----|-----|------|------|
|[**Chinese idiom** dict](../../wiki/词典加载-说明文档#user-content-加载成语词典) |chinese_idiom_loader|load Chinese idiom dictionary |⭐|
|[**xiehouyu** dict](../../wiki/词典加载-说明文档#user-content-加载歇后语词典) |xiehouyu_loader|load xiehouyu dictionary |⭐|
|[**Chinese location** dict](../../wiki/词典加载-说明文档#user-content-加载中国省市县地名词典) |china_location_loader|load Chinese location dictionary including province, city, county |⭐|
|[**Chinese location replacement** dict](../../wiki/词典加载-说明文档#user-content-加载中国区划调整词典) |china_location_change_loader|load replacement info of Chinese location dictionary from 2018 |⭐|
|[**world wide location** dict](../../wiki/词典加载-说明文档#user-content-加载世界国家城市地名词典) |world_location_loader|load world wide location | |
|[**Chinese character** dict](../../wiki/词典加载-说明文档#user-content-加载新华字典) |chinese_char_dictionary_loader|load Chinese character dictionary | |
|[**Chinese word** dict](../../wiki/词典加载-说明文档#user-content-加载新华词典) |chinese_word_dictionary_loader|load Chinese word dictionary | |

### 6.Named Entity Recognition(NER) auxiliary tools

- [NER dateset format description](../../wiki/NER-说明文档#user-content-前言)

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|-------|
|[extract **money entity**](../../wiki/NER-说明文档#user-content-货币金额实体抽取) |extract_money |extract money entity text from the given text |⭐ |
|[extract **time entity**](../../wiki/NER-说明文档#user-content-时间实体抽取) |extract_time |extract time entity text from the given text |⭐ |
|[**Lexicon NER**](../../wiki/NER-说明文档#user-content-基于词典-ner) |LexiconNER|get entities from the text via dictionary |⭐ |
|[**entity to tag**](../../wiki/NER-说明文档#user-content-entity-转-tag) |entity2tag|convert the entities info to tags for sequence labeling | |
|[**tag to entity**](../../wiki/NER-说明文档#user-content-tag-转-entity) |tag2entity|convert the tags of sequence labeling to entities | |
|[**char** token to **word** token](../../wiki/NER-说明文档#user-content-字-token-转词-token) |char2word|convert char token data to word token data | |
|[**word** token to **char** token](../../wiki/NER-说明文档#user-content-词-token-转字-token) |word2char|convert word token data to char token data | |
|[**entity compare**](../../wiki/NER-说明文档#user-content-比较-ner-标注实体与模型预测实体之间的差异) |entity_compare|compare the predicted entities with the golden entities |⭐ |
|[NER **acceleration of prediction**](../../wiki/NER-说明文档#user-content-ner-模型预测加速) |TokenSplitSentence<br>TokenBreakLongSentence<br>TokenBatchBucket|acceleration of NER prediction |⭐ |
|[**split dataset**](../../wiki/NER-说明文档#user-content-分割数据集) |analyse_dataset|split dataset info training, valid, test part and analyse the KL divergence info  |⭐ |
|[entity **collector**](../../wiki/NER-说明文档#user-content-实体收集) |collect_dataset_entities|collect all entities from labeled dataset to get a dictionary | |


### 7.Text Classification

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|------|
|[Naive bayes **words analysis**](../../wiki/文本分类-说明文档#user-content-朴素贝叶斯分析类别词汇) |analyse_freq_words|analyse the words frequency of different classes by naive bayes |⭐ |
|[**split dataset**](../../wiki/文本分类-说明文档#user-content-分割数据集) |analyse_dataset|split dataset info training, valid, test part and analyse the KL divergence info |⭐ |


### 8.Sentiment Analysis

| Features   | Function name   |Description   |Star   |
|--------|--------|-------|-------|
|[**sentiment analysis** based on dictionary](../../wiki/情感分析-说明文档#user-content-基于词典的情感分析) |LexiconSentiment|compute the sentiment value(0~1) of a given text | |

### 9.Chinese Word Segmentation(CWS)
| Features   | Function name   |Description   |Star   |
|--------|--------|-------|-------|
|[**word to tag**](../../wiki/分词-说明文档#user-content-word-转-tag) |cws.word2tag|convert the words list to a list of tags for CWS | |
|[**tag to word**](../../wiki/分词-说明文档#user-content-tag-转-word) |cws.tag2word|convert the list of tags to a words list for CWS | |
|[**compute F1**](../../wiki/分词-说明文档#user-content-统计-f1-值) |cws.f1|compute F1 value of the CWS models | |
|[**CWS dataset corrector**](../../wiki/分词-说明文档#user-content-分词数据矫正-标准词典) |cws.CWSDCWithStandardWords |correct the CWS datasets with dictionaries | |

### My Initial Intention

- NLP preprocessing and parsing is significant and time-consuming, especially for Chinese. This library offers a bundle of features to tackle these nasty jobs and you can focus more on training models. 
- If having any suggestions or problems with bugs, you can raise an issue via github.

### Welcome to join the wechat group of NLP technics
### Please scan the qr code below and send 【进群】
![image](../../blob/master/image/qrcode_for_gh.jpg)
### If this tool is useful to your development, please click the github star ⭐
### Or scan the Paypal or Wechat QR code to donate money (●'◡'●) Thanks ~~
- [Thanks](../../wiki/致谢篇) for your donation!

![image](../../blob/master/image/payment_code.jpg)
\
