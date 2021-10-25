<p align="center">
    <a alt="jionlp logo">
        <img src="../../blob/master/image/jionlp_logo.jpg" / style="width:300px;height:130px">
    </a>
</p>
<p align="center">
    <a alt="License">
        <img src="https://img.shields.io/github/license/dongrixinyu/JioNLP?color=crimson" /></a>
    <a alt="Size">
        <img src="https://img.shields.io/badge/size-18.9m-orange" /></a>
    <a alt="Downloads">
        <img src="https://img.shields.io/badge/downloads-5k-yellow" /></a>
    <a alt="Version">
        <img src="https://img.shields.io/badge/version-1.3.38-green" /></a>
    <a href="https://github.com/dongrixinyu/JioNLP/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/dongrixinyu/JioNLP?color=blue" /></a>
</p>

### &emsp;&emsp; ——JioNLP：中文 NLP 预处理工具包 A Python Lib for Chinese NLP Preprocessing
### &emsp;&emsp; ——安装：```pip install jionlp```
### &emsp;&emsp; ——[JioNLP在线版](http://182.92.160.94:16666/#/) 可快速试用部分功能（测试版，可能存在不稳定）

- 做 NLP 任务，需要清洗、过滤语料？用 JioNLP
- 做 NLP 任务，需要做信息抽取？用 JioNLP
- 做 NLP 任务，需要数据增强？用 JioNLP
- 做 NLP 任务，需要给模型添加偏旁、拼音、词典、繁体转换信息？用 JioNLP
#### 总之，JioNLP 提供 NLP 任务预处理功能，准确、高效、零使用门槛，并提供一步到位的查阅入口。

#### 功能主要包括：文本清洗，删除HTML标签、删除异常字符、删除冗余字符，转换全角字母、数字、空格为半角，抽取及删除E-mail及域名、抽取及删除（手机号、座机号）电话号码、抽取及删除QQ号、抽取及删除括号内容、抽取及删除身份证号、抽取及删除IP地址、抽取及删除URL超链接、抽取及删除货币金额与单位，金额数字转大写汉字，时间语义解析，解析身份证号信息、解析手机号码归属地、解析座机区号归属地、解析手机号码运营商，按行快速读写文件，（多功能）停用词过滤，（优化的）分句，地址解析，新闻地域识别，繁简体转换，汉字转拼音，汉字偏旁、字形、四角编码、五笔编码拆解，基于词典的情感分析，色情数据过滤，反动数据过滤，关键短语抽取，抽取式文本摘要，成语接龙，成语词典、歇后语词典、新华字典、新华词典、停用词典、中国地名词典、中国县级地名变更词典、世界地名词典，时间实体抽取，基于词典的NER，NER的字、词级别转换，NER的entity和tag格式转换，NER模型的预测阶段加速并行工具集，NER标注和模型预测的结果差异对比，NER标注数据集分割与统计，NER实体收集、文本分类标注数据集的分割与统计、回译数据增强、相邻近汉字换位数据增强、同音词替换数据增强、随机增删字符数据增强、实体替换数据增强、公历转农历日期、农历转公历日期


#### Update 2021-10-25
## 更新 [货币金额实体抽取](../../wiki/NER-说明文档#user-content-货币金额实体抽取)

#### jio.ner.extract_money 从文本中抽取货币金额实体（不依赖模型，纯规则）。
#### 配合 jio.parse_time 货币金额解析使用（见下）
``` python
import jionlp as jio
text = '张三赔偿李大花人民币车费601,293.11元，工厂费大约一万二千三百四十五元,利息9佰日元，打印费人民币十块钱。'
res = jio.ner.extract_money(text, with_parsing=False)
print(res)

# [{'text': '601,293.11元', 'offset': [12, 23], 'type': 'money'},
#  {'text': '大约一万二千三百四十五元', 'offset': [27, 39], 'type': 'money'},
#  {'text': '9佰日元', 'offset': [42, 46], 'type': 'money'},
#  {'text': '人民币十块钱', 'offset': [50, 56], 'type': 'money'}]

```

#### Update 2021-10-25
## 更新 [货币金额解析](../../wiki/正则抽取与解析-说明文档#user-content-货币金额解析)

#### jio.parse_money 给定货币金额字符串，解析其标准金额、货币类型、精确度。

```python
import jionlp as jio
text_list = ['约4.287亿美元', '两个亿卢布', '六十四万零一百四十三元一角七分', '3000多欧元'] 
moneys = [jio.parse_money(text) for text in text_list]

# 约4.287亿美元: {'num': '428700000.00', 'case': '美元', 'definition': 'blur'}
# 两个亿卢布: {'num': '200000000.00', 'case': '卢布', 'definition': 'accurate'}
# 六十四万零一百四十三元一角七分: {'num': '640143.17', 'case': '元', 'definition': 'accurate'}
# 3000多欧元: {'num': ['3000.00', '4000.00'], 'case': '欧元', 'definition': 'blur'}

```

- 支持纯数字格式，如：987273.3美元
- 支持大写中文金额，如：柒仟六佰零弎萬肆仟叁佰贰拾壹元伍分
- 支持混合格式，如：1.26万港元
- 支持**修饰词**解析，如：将近6万块钱、至少1000块钱以上
- 支持**模糊金额**解析，如：两万多元钱，6千多亿日元
- 支持**口语化中文**格式，如：三十五块三毛；但对于“三十五块八”这样的字符串，在文本中存在**歧义**，如“三十五块八颗糖”等，因此，```jio.ner.extract_money``` 对于此字符串不予抽取，但```parse_money```可以将“三十五块八”看作完整的口语化金额，标准化为“35.80元”
- 支持多种常见货币类型：人民币，港元，澳门元，美元，日元，澳元，韩元，卢布，英镑，马克，法郎，欧元，加元, 泰铢等。

#### Update 2021-10-11
## 新增 [时间语义解析](../../wiki/时间语义解析-说明文档#user-content-时间语义解析)

#### jio.parse_time 给定时间字符串，解析其为时间戳、时长等。

``` python
import time
import jionlp as jio
res = jio.parse_time('今年9月', time_base={'year': 2021})
print(res)
res = jio.parse_time('零三年元宵节晚上8点半', time_base=time.time())
print(res)
res = jio.parse_time('一万个小时')
print(res)
res = jio.parse_time('100天之后', time.time())
print(res)
res = jio.parse_time('每周五下午4点', time.time())
print(res)

# {'type': 'time_span', 'definition': 'accurate', 'time': ['2021-09-01 00:00:00', '2021-09-30 23:59:59']}
# {'type': 'time_point', 'definition': 'accurate', 'time': ['2003-02-15 20:30:00', '2003-02-15 20:30:59']}
# {'type': 'time_delta', 'definition': 'accurate', 'time': {'hour': 10000.0}}
# {'type': 'time_span', 'definition': 'blur', 'time': ['2021-10-22 00:00:00', 'inf']}
# {'type': 'time_period', 'definition': 'accurate', 'time': {'delta': {'day': 7}, 
#  'point': {'time': ['2021-07-16 16:00:00', '2021-07-16 16:59:59'], 'string': '周五下午4点'}}}
```

- 目前支持年月日、时分秒、星期、季节、季度、节日、农历、时间范围、时间段、时间周期、模糊时间代词等解析。
- 支持对未来时间优先选择，参数为`ret_future(bool)`。
- [关于**时间语义解析**](../../wiki/时间语义解析-说明文档)
- 目前支持的所有 [测试用例](../../blob/master/test/test_time_parser.py)

#### 完整示例
[JioNLP在线版-时间抽取与解析](http://182.92.160.94:16666/#/extract_time)


## 安装 Installation

- python>=3.6 **github 版本略领先于 pip**
```
$ git clone https://github.com/dongrixinyu/JioNLP
$ cd ./JioNLP
$ pip install .
```
- pip 安装
```
$ pip install jionlp
```
- 可能存在的问题
```
# 如安装失败，遇到安装时提示的 pkuseg、Microsoft Visual C++、gcc、g++ 等信息，
# 则说明是 pkuseg 安装失败，需要在相应系统中安装 C 和 C++ 编译器，重新安装。
# pip install pkuseg
```

## 使用 Features

- 导入工具包，查看工具包的主要功能与函数注释
```
>>> import jionlp as jio
>>> jio.help()  # 输入关键词搜索工具包是否包含某功能，如输入“回译”
>>> dir(jio)
>>> print(jio.extract_parentheses.__doc__)
```
- 在 Linux 系统，可使用以下命令做搜索：
```
$ jio_help
```

- **星级⭐**代表优质特色功能
### 1.小工具集 Gadgets

| 功能   | 函数   |描述   |星级   |
|--------|-------|-------|-------|
|[**查找帮助**](../../wiki/Gadget-说明文档#user-content-查找帮助) |help|若不知道 JioNLP 有哪些功能，可根据命令行提示键入若干关键词做搜索 | |
|[**时间语义解析**](../../wiki/时间语义解析-说明文档#user-content-时间语义解析) |parse_time|给定时间文本，解析其时间语义（时间戳、时长）等 |⭐|
|[**关键短语抽取**](../../wiki/Gadget-说明文档#user-content-关键短语抽取) |extract_keyphrase|给定一篇文本，抽取其对应关键短语 |⭐|
|[抽取式**文本摘要**](../../wiki/Gadget-说明文档#user-content-抽取式文本摘要) |extract_summary|给定一篇文本，抽取其对应文摘 | |
|[**停用词过滤**](../../wiki/Gadget-说明文档#user-content-去除停用词) |remove_stopwords|给定一个文本被分词后的词 list，去除其中的停用词 |⭐|
|[**分句**](../../wiki/Gadget-说明文档#user-content-文本分句) |split_sentence|对文本按标点分句 |⭐|
|[**地址解析**](../../wiki/Gadget-说明文档#user-content-地址解析) |parse_location|给定一个包含国内地址字符串，识别其中的**省、市、县区、乡镇街道、村社**等信息 |⭐|
|[电话号码**归属地**、<br>**运营商**解析](../../wiki/Gadget-说明文档#user-content-电话号码归属地运营商解析) |phone_location<br>cell_phone_location<br>landline_phone_location |给定一个电话号码（手机号、座机号）字符串，识别其中的**省、市、运营商** ||
|[新闻**地名识别**](../../wiki/Gadget-说明文档#user-content-新闻地名识别) |recognize_location|给定新闻文本，识别其中的**国内省、市、县，国外国家、城市**等信息 |⭐|
|[**公历农历**日期互转](../../wiki/Gadget-说明文档#user-content-公历农历日期互转)|lunar2solar<br>solar2lunar |给定某公（农）历日期，将其转换为农（公）历 ||
|[**身份证号**解析](../../wiki/Gadget-说明文档#user-content-身份证号码解析) |parse_id_card|给定一个身份证号，识别对应的**省、市、县、出生年月、**<br>**性别、校验码**等信息 |⭐|
|[**成语接龙**](../../wiki/Gadget-说明文档#user-content-成语接龙) |idiom_solitaire|成语接龙，即前一成语的尾字和后一成语的首字（读音）相同 ||
|[**色情**数据过滤]() | | |
|[**反动**数据过滤]() | | |
|[**繁**体转**简**体](../../wiki/Gadget-说明文档#user-content-繁体转简体字) |tra2sim|繁体转简体，支持**逐字转**与**最大匹配**两种模式 | |
|[**简**体转**繁**体](../../wiki/Gadget-说明文档#user-content-简体转繁体字) |sim2tra|简体转繁体，支持**逐字转**与**最大匹配**两种模式 | |
|[汉字转**拼音**](../../wiki/Gadget-说明文档#user-content-汉字转拼音) |pinyin| 找出中文文本对应的汉语拼音，并可返回**声母**、**韵母**、**声调** |⭐ |
|[汉字转**偏旁与字形**](../../wiki/Gadget-说明文档#user-content-汉字转偏旁与字形) |char_radical| 找出中文文本对应的汉字字形结构信息，<br>包括**偏旁部首**(“河”氵)、**字形结构**(“河”左右结构)、<br>**四角编码**(“河”31120)、**汉字拆解**(“河”水可)、<br>**五笔编码**(“河”ISKG) |⭐ |
|[金额**数字转汉字**](../../wiki/正则抽取与解析-说明文档#user-content-金额数字转汉字)|money_num2char| 给定一条数字金额，返回其**汉字**大写结果 | |

### 2.数据增强

- [**文本数据增强各方法说明**](../../wiki/数据增强-说明文档#user-content-数据增强方法对比)

| 功能   | 函数   |描述   |星级  |
|--------|--------|-------|------|
|[**回译**](../../wiki/数据增强-说明文档#user-content-回译数据增强) |BackTranslation|给定一篇文本，采用各大厂云平台的机器翻译接口，<br>实现数据增强 |⭐ |
|[**邻近汉字换位**](../../wiki/数据增强-说明文档#user-content-邻近汉字换位) |swap_char_position|随机交换相近字符的位置，实现数据增强 | |
|[**同音词替换**](../../wiki/数据增强-说明文档#user-content-同音词替换) |homophone_substitution|相同读音词汇替换，实现数据增强 |⭐ |
|[随机**增删字符**](../../wiki/数据增强-说明文档#user-content-随机增删字符) |random_add_delete|随机在文本中增加、删除某个字符，对语义不造成影响 | |
|[NER**实体替换**](../../wiki/数据增强-说明文档#user-content-ner实体替换) |replace_entity|根据实体词典，随机在文本中替换某个实体，对语义不<br>造成影响，也广泛适用于序列标注、文本分类 |⭐ |


### 3.正则抽取与解析

| 功能   | 函数   |描述   |星级    |
|--------|--------|-------|-------|
|[**清洗文本**](../../wiki/正则抽取与解析-说明文档#user-content-清洗文本) |clean_text|去除文本中的**异常字符、冗余字符、HTML标签、括号信息、**<br>**URL、E-mail、电话号码，全角字母数字转换为半角** |⭐ |
|[抽取 **E-mail**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-e-mail) |extract_email|抽取文本中的 E-mail，返回**位置**与**域名** | |
|[解析 **货币金额**](../../wiki/正则抽取与解析-说明文档#user-content-货币金额解析) |extract_money|解析货币金额字符串 |⭐ |
|[抽取**电话号码**](../../wiki/正则抽取与解析-说明文档#user-content-抽取电话号码) |extract_phone_number| 抽取电话号码(含**手机号**、**座机号**)，返回**域名**、**类型**与**位置** | |
|[抽取中国**身份证** ID](../../wiki/正则抽取与解析-说明文档#user-content-抽取身份证号) |extract_id_card|抽取身份证 ID，配合 **jio.parse_id_card** 返回身份证的<br>详细信息(**省市县**、**出生日期**、**性别**、**校验码**)| |
|[抽取 **QQ** 号](../../wiki/正则抽取与解析-说明文档#user-content-抽取-qq) |extract_qq|抽取 QQ 号，分为严格规则和宽松规则 | |
|[抽取 **URL**](../../wiki/正则抽取与解析-说明文档#user-content-抽取-url-超链接) |extract_url|抽取 URL 超链接 | |
|[抽取 **IP**地址](../../wiki/正则抽取与解析-说明文档#user-content-抽取-ip-地址) |extract_ip_address|抽取 IP 地址| |
|[抽取**括号**中的内容](../../wiki/正则抽取与解析-说明文档#user-content-抽取文本括号信息) |extract_parentheses|抽取括号内容，包括 **{}「」[]【】()（）<>《》** |⭐ |
|[删除 **E-mail**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-e-mail) |remove_email|删除文本中的 E-mail 信息 | |
|[删除 **URL**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-url) |remove_url |删除文本中的 URL 信息| |
|[删除 **电话号码**](../../wiki/正则抽取与解析-说明文档#user-content-删除电话号码) |remove_phone_number|删除文本中的电话号码 | |
|[删除 **IP地址**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-ip-地址)|remove_ip_address|删除文本中的 IP 地址 | |
|[删除 **身份证号**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的身份证号) |remove_id_card|删除文本中的身份证信息 | |
|[删除 **QQ**](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-qq-号) |remove_qq|删除文本中的 qq 号| |
|[删除 **HTML**标签](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的-html-标签) |remove_html_tag|删除文本中残留的 HTML 标签 | |
|[删除**括号**中的内容](../../wiki/正则抽取与解析-说明文档#user-content-删除文本括号信息) |remove_parentheses|删除括号内容，包括 **{}「」[]【】()（）<>《》** | |
|[删除异常字符](../../wiki/正则抽取与解析-说明文档#user-content-删除文本中的异常字符) |remove_exception_char|删除文本中异常字符，主要保留汉字、常用的标点，<br>单位计算符号，字母数字等 | |

### 4.文件读写工具

| 功能   | 函数   |描述   |星级   |
|--------|--------|-------|-------|
|[**按行读取文件**](../../wiki/文件读写-说明文档#user-content-文件读取iter) |read_file_by_iter |以迭代器形式方便按行读取文件，节省内存，<br>支持指定**行数**，**跳过空行** ||
|[**按行读取文件**](../../wiki/文件读写-说明文档#user-content-文件读取list) |read_file_by_line |按行读取文件，支持指定**行数**，**跳过空行** |⭐ |
|[将 list 中元素按行写入文件](../../wiki/文件读写-说明文档#user-content-文件写入) |write_file_by_line| 将 list 中元素按行写入文件 |⭐ |
|[计时工具](../../wiki/文件读写-说明文档#user-content-计时器) |TimeIt| 统计某一代码段的耗时 | |

### 5.词典加载与使用

| 功能 | 函数 | 描述 |星级  |
|-----|-----|------|------|
|[**成语**词典](../../wiki/词典加载-说明文档#user-content-加载成语词典) |chinese_idiom_loader|加载成语词典 |⭐|
|[**歇后语**词典](../../wiki/词典加载-说明文档#user-content-加载歇后语词典) |xiehouyu_loader|加载歇后语词典 |⭐|
|[**中国地名**词典](../../wiki/词典加载-说明文档#user-content-加载中国省市县地名词典) |china_location_loader|加载中国**省、市、县**三级词典 |⭐|
|[**中国区划调整**词典](../../wiki/词典加载-说明文档#user-content-加载中国区划调整词典) |china_location_change_loader|加载 2018 年以来中国**县级**以上区划调整更名记录 |⭐|
|[**世界地名**词典](../../wiki/词典加载-说明文档#user-content-加载世界国家城市地名词典) |world_location_loader|加载世界**大洲、国家、城市**词典 | |
|[新华**字**典](../../wiki/词典加载-说明文档#user-content-加载新华字典) |chinese_char_dictionary_loader|加载新华字典 | |
|[新华**词**典](../../wiki/词典加载-说明文档#user-content-加载新华词典) |chinese_word_dictionary_loader|加载新华词典 | |

### 6.实体识别(NER)算法辅助工具集

- [工具包 NER 数据规定说明](../../wiki/NER-说明文档#user-content-前言)

| 功能   | 函数   |描述   |星级   |
|--------|--------|-------|-------|
|[抽取**货币金额实体**](../../wiki/NER-说明文档#user-content-货币金额实体抽取) |extract_money |从文本中抽取出货币金额实体 |⭐ |
|[抽取**时间实体**](../../wiki/NER-说明文档#user-content-时间实体抽取) |extract_time |从文本中抽取出时间实体 |⭐ |
|[基于**词典NER**](../../wiki/NER-说明文档#user-content-基于词典-ner) |LexiconNER|依据指定的实体词典，前向最大匹配实体 |⭐ |
|[**entity 转 tag**](../../wiki/NER-说明文档#user-content-entity-转-tag) |entity2tag|将 json 格式实体转换为模型处理的 tag 序列 | |
|[**tag 转 entity**](../../wiki/NER-说明文档#user-content-tag-转-entity) |tag2entity|将模型处理的 tag 序列转换为 json 格式实体 | |
|[**字** token 转**词** token](../../wiki/NER-说明文档#user-content-字-token-转词-token) |char2word|将字符级别 token 转换为词汇级别 token | |
|[**词** token 转**字** token](../../wiki/NER-说明文档#user-content-词-token-转字-token) |word2char|将词汇级别 token 转换为字符级别 token | |
|[比较标注与模型预测的**实体差异**](../../wiki/NER-说明文档#user-content-比较-ner-标注实体与模型预测实体之间的差异) |entity_compare|针对人工标注的实体，与模型预测出的实体结果<br>，做差异比对 |⭐ |
|[NER模型**预测加速**](../../wiki/NER-说明文档#user-content-ner-模型预测加速) |TokenSplitSentence<br>TokenBreakLongSentence<br>TokenBatchBucket|对 NER 模型预测并行加速的方法  |⭐ |
|[**分割数据集**](../../wiki/NER-说明文档#user-content-分割数据集) |analyse_dataset|对 NER 标注语料，分为训练集、验证集、测试集，并给出各个子集的实体类型分布统计 |⭐ |
|[实体**收集**](../../wiki/NER-说明文档#user-content-实体收集) |collect_dataset_entities|将标注语料中的实体收集起来，形成词典 | |


### 7.文本分类

| 功能   | 函数   |描述   |星级   |
|--------|--------|-------|------|
|[朴素贝叶斯**分析类别词汇**](../../wiki/文本分类-说明文档#user-content-朴素贝叶斯分析类别词汇) |analyse_freq_words|对文本分类的标注语料，做朴素贝叶斯词频分析，返回各类<br>文本的高条件概率词汇 |⭐ |
|[**分割数据集**](../../wiki/文本分类-说明文档#user-content-分割数据集) |analyse_dataset|对文本分类的标注语料，切分为训练集、验证集、测试集，<br>并给出各个子集的分类分布统计 |⭐ |


### 8.情感分析

| 功能   | 函数   |描述   |星级   |
|--------|--------|-------|-------|
|[基于**词典情感分析**](../../wiki/情感分析-说明文档#user-content-基于词典的情感分析) |LexiconSentiment|依据人工构建的情感词典，计算文本的情感值，介于0~1之间 | |


### 初衷

- NLP 预处理至关重要，且非常耗时。本 lib 能快速辅助完成各种琐碎的预处理操作，加速开发进度，把有限的精力用在思考而非 code 上。
- 如有功能建议、bug，可通过 issue 按模板提出。
- 如感兴趣合作完善本工具包，请参考 **TODO.txt** 文件进行功能添加。

### 做 NLP不易，欢迎加入自然语言处理 Wechat 交流群
### 如以下码失效，请先添加 vx：dongrixinyu89
![image](../../blob/master/image/qr_code_for_collection.png)
### 如本工具对您有帮助，可以扫码请作者喝杯咖啡 (●'◡'●)
![image](../../blob/master/image/payment_code.png)

