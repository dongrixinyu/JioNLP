<p align="center">
    <a alt="jionlp logo">
        <img src="https://github.com/dongrixinyu/JioNLP/blob/master/jionlp_logo.jpg" / style="width: 100px;height: 100px"></a>
</p>
<p align="center">
    <a alt="Downloads">
        <img src="https://img.shields.io/badge/size-35.6m-yellow" /></a>
    <a alt="Downloads">
        <img src="https://img.shields.io/badge/downloads-2k-brightgreen" /></a>
    <a alt="Version">
        <img src="https://img.shields.io/badge/version-1.3.6-green" /></a>
    <a href="https://github.com/dongrixinyu/JioNLP/pulse" alt="Activity">
        <img src="https://img.shields.io/github/commit-activity/m/dongrixinyu/JioNLP" /></a>
</p>

### &emsp;&emsp; ——JioNLP：中文 NLP 预处理工具包 A python library for chinese NLP preprocessing
### &emsp;&emsp; ```pip install -i https://test.pypi.org/simple/ jionlp```

#### 做 NLP 任务，需要清洗、过滤语料？用 JioNLP
#### 做 NLP 任务，需要做信息抽取？用 JioNLP
#### 做 NLP 任务，需要做数据增强？用 JioNLP
#### 做 NLP 任务，需要给模型添加偏旁、拼音、繁体转换？用 JioNLP
#### 总之，JioNLP 提供 NLP 任务预处理功能，准确、高效、零使用门槛，并提供一步到位的查阅入口。

#### 功能主要包括：文本清洗，去除HTML标签、异常字符、冗余字符，转换全角字母、数字、空格为半角，抽取及删除E-mail及域名、电话号码、QQ号、括号内容、身份证号、IP地址、URL超链接、货币金额与单位，解析身份证号信息、手机号码归属地、座机区号归属地，按行快速读写文件，（多功能）停用词过滤，（优化的）分句，地址解析，新闻地域识别，繁简体转换，汉字转拼音，汉字偏旁、字形、四角编码拆解，基于词典的情感分析，色情数据过滤，反动数据过滤，关键短语抽取，抽取式文本摘要，成语词典、歇后语词典、新华字典、新华词典、停用词典、中国地名词典、世界地名词典，基于词典的NER，NER的字、词级别转换，NER的entity和tag格式转换，NER模型的预测阶段加速并行工具集，NER标注和模型预测的结果差异对比，NER标注数据集分割与统计，文本分类标注数据集的分割与统计，回译数据增强。


#### Update 2020-11-10
## 新增更新 [文本摘要](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-抽取式文本摘要)

#### jio.summary.extract_summary

给定一篇文本（尤指新闻），返回其抽取式摘要。

```
>>> import jionlp as jio
>>> text = '海外网11月10日电当地时间9日，美国总统特朗普在推特上发文表示，美国国防部长马克·埃斯珀已经被开除。...'
>>> res = jio.summary.extract_summary(text)
>>> print(res)

# 特朗普的推文写道：“马克 埃斯珀已经被开除。...
```

#### Update 2020-10-16
## 新增更新 [地址解析](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-地址解析)

#### parse_location

给定一个（地址）字符串，识别其中的**省、市、县三级地名**，指定参数```town_village(bool)```，可获取**乡镇、村、社区两级详细地名**。
使用了一份最新的[**2019年末国家统计局整理的全国行政区划**](http://www.stats.gov.cn/tjsj/tjbz/tjyqhdmhcxhfdm/2019)中国地名词典，词典位置：```jionlp/dictionary/china_location.txt```。

```
# 例 1
>>> import jionlp as jio
>>> text = '武侯区红牌楼街道19号红星大厦9楼2号'
>>> res = jio.parse_location(text, town_village=True)
>>> print(res)

# {'province': '四川省',
#  'city': '成都市',
#  'county': '武侯区',
#  'town': '红牌楼街道',
#  'village': None,
#  'detail': '红牌楼街道19号红星大厦9楼2号',
#  'full_location': '四川省成都市武侯区红牌楼街19号红星大厦9楼2号',
#  'orig_location': '武侯区红牌楼街19号红星大厦9楼2号'}
```


## 安装 Installation

- python>=3.6
```
$ git clone https://github.com/dongrixinyu/JioNLP
$ cd ./JioNLP
$ pip install .
```
- pip 安装
```
$ pip install -i https://test.pypi.org/simple/ jionlp
```

## 使用 Features

- 导入工具包，查看工具包的主要功能与函数注释
```
>>> import jionlp as jio
>>> dir(jio)
>>> dir(jio.ner)
>>> print(jio.extract_parentheses.__doc__)
```

### 1、正则抽取与解析

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[**清洗文本**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-清洗文本)      |clean_text |去除文本中的**异常字符、冗余字符、HTML标签、括号信息、**<br>**URL、E-mail、电话号码，全角字母数字转换为半角**|
|[抽取 **E-mail**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取-e-mail)|extract_email |抽取文本中的 E-mail，返回**位置**与**域名** |
|[抽取 **金额**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取金额字符串)|extract_money |抽取文本中的金额，并将其以**数字 + 单位**标准形式输出 |
|[抽取**电话号码**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取电话号码) | extract_phone_number | 抽取电话号码(含**手机**、**座机**)，返回**域名**、**类型**与**位置**
|[抽取中国**身份证** ID](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取身份证号)|extract_id_card     |抽取身份证 ID，配合 **jio.parse_id_card** 返回身份证的<br>详细信息(**省市县**、**出生日期**、**性别**、**校验码**) |
|[抽取 **QQ** 号](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-qq)       |extract_qq  |抽取 QQ 号，分为严格规则和宽松规则 |
|[抽取 **URL**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-url-超链接)         |extract_url         |抽取 URL 超链接  |
|[抽取 **IP**地址](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-ip-地址)      |extract_ip_address  |抽取 IP 地址|
|[抽取**括号**中的内容](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取文本括号信息) |extract_parentheses |抽取括号内容，包括 **{}「」[]【】()（）<>《》** |
|[删除 **E-mail**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-e-mail) |remove_email  |删除文本中的 E-mail 信息 |
|[删除 **URL**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-url)     |remove_url          |删除文本中的 URL 信息|
|[删除 **电话号码**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除电话号码)    |remove_phone_number |删除文本中的电话号码 |
|[删除 **IP地址**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-ip-地址)|remove_ip_address |删除文本中的 IP 地址 |
|[删除 **身份证号**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的身份证号)|remove_id_card |删除文本中的身份证信息 |
|[删除 **QQ**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-qq-号)       |remove_qq           |删除文本中的 qq 号|
|[删除 **HTML**标签](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-html-标签)    |remove_html_tag     |删除文本中残留的 HTML 标签 |
|[删除**括号**中的内容](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本括号信息) |remove_parentheses |删除括号内容，包括 **{}「」[]【】()（）<>《》** |
|[删除异常字符](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的异常字符)    |remove_exception_char     |删除文本中异常字符，主要保留汉字、常用的标点，<br>单位计算符号，字母数字等。 |

### 2. 文件读写工具

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[**按行读取文件**](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件读取iter)     |read_file_by_iter    |以迭代器形式方便按行读取文件，节省内存，支持指定**行数**，<br>**跳过空行**  |
|[**按行读取文件**](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件读取list)     |read_file_by_line |按行读取文件，支持指定**行数**，**跳过空行** |
|[将 list 中元素按行写入文件](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件写入) | write_file_by_line | 将 list 中元素按行写入文件 |
|[计时工具](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-计时器)                 |TimeIt             | 统计某一代码段的耗时    |

### 3.小工具集 Gadgets

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[**关键短语抽取**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-关键短语抽取)   |extract_keyphrase|给定一篇文本，抽取其对应关键短语    |
|[抽取式**文本摘要**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-抽取式文本摘要)   |extract_summary|给定一篇文本，抽取其对应文摘    |
|[**回译数据增强**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-回译数据增强)   |BackTranslation|给定一篇文本，采用各大厂云平台的机器翻译接口，实现数据增强    |
|[**停用词过滤**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-去除停用词)       |remove_stopwords|给定一个文本被分词后的词 list，去除其中的停用词            |
|[**分句**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-文本分句)             |split_sentence    |对文本按标点分句。  |
|[**地址解析**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-地址解析)         |parse_location    |给定一个包含国内地址字符串，识别其中的**省、市、县区、乡镇街道、村社**等信息     |
|[新闻**地名识别**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-新闻地名识别) |recognize_location|给定新闻文本，识别其中的**国内省、市、县，国外国家、城市**等信息     |
|[**身份证号**解析](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-身份证号码解析) |parse_id_card   |给定一个身份证号，识别对应的**省、市、县、出生年月、**<br>**性别、校验码**等信息 |
|[色情数据过滤]()     |
|[反动数据过滤]()     |
|[繁体转简体](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-繁体转简体字) |tra2sim |繁体转简体，支持**逐字转**与**最大匹配**两种模式 |
|[简体转繁体](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-简体转繁体字) |sim2tra |简体转繁体，支持**逐字转**与**最大匹配**两种模式 |
|[汉字转**拼音**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-汉字转拼音)    | pinyin | 找出中文文本对应的汉语拼音，并可返回**声母**、**韵母**、**声调**   |
|[汉字转**偏旁与字形**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-汉字转偏旁与字形)    | char_radical | 找出中文文本对应的汉字字形结构信息，包括**偏旁部首**(“河”氵)、<br>**字形结构**(“河”左右结构)、**四角编码**(“河”31120)、<br>**汉字拆解**(“河”水可) |

### 4.词典加载与使用

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[**成语**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载成语词典) | chinese_idiom_loader |加载成语词典 |
|[**歇后语**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载歇后语词典) | xiehouyu_loader |加载歇后语词典 |
|[**中国地名**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载中国省市县地名词典) | china_location_loader |加载中国**省、市、县**三级词典 |
|[**世界地名**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载世界国家城市地名词典) | world_location_loader |加载世界**大洲、国家、城市**词典 |
|[新华**字典**](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载新华字典) | chinese_char_dictionary_loader |加载新华字典 |
|[新华**词典**](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载新华词典) | chinese_word_dictionary_loader |加载新华词典 |

### 5.实体识别(NER)算法辅助工具集

- [工具包 NER 数据规定说明](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-前言)

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[基于**词典NER**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-基于词典-ner) | LexiconNER |依据指定的实体词典，前向最大匹配实体 |
|[**entity 转 tag**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-entity-转-tag) | entity2tag |将 json 格式实体转换为模型处理的 tag 序列 |
|[**tag 转 entity**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-tag-转-entity) | tag2entity |将模型处理的 tag 序列转换为 json 格式实体 |
|[**字 token 转词 token**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-字-token-转词-token) | char2word |将字符级别 token 转换为词汇级别 token |
|[**词 token 转字 token**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-词-token-转字-token) | word2char |将词汇级别 token 转换为字符级别 token |
|[比较标注与模型预测的**实体差异**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-比较-ner-标注实体与模型预测实体之间的差异) | entity_compare |针对人工标注的实体，与模型预测出的实体结果<br>，做差异比对 |
|[**NER模型预测加速**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-ner-模型预测加速)  |TokenSplitSentence<br>TokenBreakLongSentence<br>TokenBatchBucket   |对 NER 模型预测并行加速的方法  |
|[**分割数据集**](https://github.com/dongrixinyu/JioNLP/wiki/NER-说明文档#user-content-分割数据集) | analyse_dataset |对 NER 标注语料，分为训练集、验证集、测试集，并给出各个子集的实体类型分布统计  |


### 6.文本分类

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[**朴素贝叶斯分析类别词汇**](https://github.com/dongrixinyu/JioNLP/wiki/文本分类-说明文档#user-content-朴素贝叶斯分析类别词汇) | analyse_freq_words |对文本分类的标注语料，做朴素贝叶斯词频分析，返回各类<br>文本的高条件概率词汇  |
|[**分割数据集**](https://github.com/dongrixinyu/JioNLP/wiki/文本分类-说明文档#user-content-分割数据集) | analyse_dataset |对文本分类的标注语料，切分为训练集、验证集、测试集，<br>并给出各个子集的分类分布统计  |


### 7.情感分析

| 功能   | 函数   |描述   |
|--------|--------|-------|
|[基于**词典情感分析**](https://github.com/dongrixinyu/JioNLP/wiki/情感分析-说明文档#user-content-基于词典的情感分析) | LexiconSentiment | 依据人工构建的情感词典，计算文本的情感值，介于0~1之间 |


### 初衷

- 开发 NLP 模型，预处理至关重要，常常占到工程师大部分时间。本工具包能快速辅助工程师完成各种琐碎的预处理操作，加速开发进度，把有限的精力用在思考而非 code 上。

### 开源不易，欢迎自由投食 (#^.^#)

![image](https://github.com/dongrixinyu/JioNLP/blob/master/qr_code_for_collection.jpg)


