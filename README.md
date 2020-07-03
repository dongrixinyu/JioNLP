# &emsp;&emsp; **JioNLP**



### &emsp;&emsp; ——全面简便的中文 NLP 工具包，做您的 NLP 任务的垫 jio 石
### &emsp;&emsp; ——A python library for chinese NLP


#### JioNLP 是一个提供常用 NLP 功能的工具包，宗旨是直接提供方便快捷的解析、词典类的面向中文的工具接口，并提供一步到位的查阅入口。

#### 功能主要包括：文本清洗，去除HTML标签、异常字符、冗余字符，抽取E-mail、电话号码、QQ号、括号内容、身份证号、IP地址、URL超链接，解析身份证号信息、手机号码归属地、座机区号归属地、E-mail域名，按行快速读写文件，（多功能）停用词过滤，（优化的）分句，地址解析，新闻地域识别，繁简体转换，汉字转拼音，汉字偏旁、字形、四角编码拆解，基于词典的情感分析，色情数据过滤，反动数据过滤，关键短语抽取，成语词典、歇后语词典、新华字典、新华词典。
#### 持续更新中...

## 安装 Installation

- python>=3.6
```
$ git clone https://github.com/dongrixinyu/JioNLP
$ cd ./JioNLP
$ pip install .
```

## 使用 Features

- 导入工具包，查看工具包的主要功能
```
>>> import jionlp as jio
>>> dir(jio)
```

### 1、正则抽取与解析

| 功能   | 函数   |描述   |
|--------|--------|-------|
|<div style="width: 150pt">[抽取 **E-mail**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取-e-mail)|extract_email |抽取文本中的 E-mail，返回**位置**与**域名** |
|[抽取 **金额**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取金额字符串)|extract_money |抽取文本中的金额，并将其以**数字 + 单位**标准形式输出 |
|[抽取**电话号码**](https://github.com/dongrixinyu/JioNLP/wiki/正则抽取与解析-说明文档#user-content-抽取电话号码) | extract_phone_number | 抽取电话号码(含**手机**、**座机**)，返回**域名**、**类型**与**位置**
|[抽取中国**身份证** ID](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取身份证号)|extract_id_card     |抽取身份证 ID，配合 **jio.parse_id_card** 返回身份证的详细信息(**省市县**、**出生日期**、**性别**、**校验码**) |
|[抽取 **QQ** 号](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-qq)       |extract_qq  |抽取 QQ 号，分为严格规则和宽松规则 |
|[抽取 **URL**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-url-超链接)         |extract_url         |抽取 URL 超链接  |
|[抽取 **IP**地址](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取-ip-地址)      |extract_ip_address  |抽取 IP 地址|
|[抽取**括号**中的内容](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-抽取文本括号信息) |extract_parentheses |抽取括号内容，包括 **{}「」[]【】()（）<>《》** |
|[**清洗文本**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-清洗文本)      |clean_text |去除文本中的**异常字符、冗余字符、HTML标签、括号信息、URL、E-mail、电话号码，全角字母数字转换为半角**|
|[删除 **E-mail**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-e-mail) |remove_email  |删除文本中的 E-mail 信息 |
|[删除 **URL**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-url)     |remove_url          |删除文本中的 URL 信息|
|[删除 **电话号码**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除电话号码)    |remove_phone_number |删除文本中的电话号码 |
|[删除 **IP地址**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-ip-地址)|remove_ip_address |删除文本中的 IP 地址 |
|[删除 **身份证号**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的身份证号)|remove_id_card |删除文本中的身份证信息 |
|[删除 **QQ**](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-qq-号)       |remove_qq           |删除文本中的 qq 号|
|[删除 **HTML**标签](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的-html-标签)    |remove_html_tag     |删除文本中残留的 HTML 标签 |
|[删除异常字符](https://github.com/dongrixinyu/jionlp/wiki/正则抽取与解析-说明文档#user-content-删除文本中的异常字符)    |remove_exception_char     |删除文本中异常字符，主要保留常用的标点符号，单位计算符号，字母数字等。 |

### 2. 文件读写工具

| 功能   | 函数   |描述   |
|--------|--------|-------|
|<div style="width: 150pt">[按行读取文件](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件读取iter)     |read_file_by_iter    |以迭代器形式方便按行读取文件，节省内存，支持指定**行数**，**跳过空行**  |
|[按行读取文件](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件读取list)     |read_file_by_line |按行读取文件，支持指定**行数**，**跳过空行** |
|[将 list 中元素按行写入文件](https://github.com/dongrixinyu/jionlp/wiki/文件读写-说明文档#user-content-文件写入) | write_file_by_line | 将 list 中元素按行写入文件 |

### 3.小工具集 Gadgets

| 功能   | 函数   |描述   |
|--------|--------|-------|
|<div style="width: 150pt">[**停用词过滤**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-去除停用词)       |remove_stopwords|给定一个文本被分词后的词 list，去除其中的停用词            |
|[**分句**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-文本分句)             |split_sentence    |对文本按标点分句。  |
|[**地址解析**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-地址解析)         |parse_location    |给定一个包含国内地址字符串，识别其中的**省、市、县**等信息     |
|[新闻**地名识别**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-新闻地名识别) |recognize_location|给定新闻文本，识别其中的**国内省、市、县，国外国家、城市**等信息     |
|[**身份证号**解析](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-身份证号码解析) |parse_id_card   |给定一个身份证号，识别对应的**省、市、县、出生年月、性别、校验码**等信息 |
|[色情数据过滤]()     |
|[反动数据过滤]()     |
|[繁体转简体](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-繁体转简体字) |tra2sim |繁体转简体，支持**逐字转**与**最大匹配**两种模式 |
|[简体转繁体](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-简体转繁体字) |sim2tra |简体转繁体，支持**逐字转**与**最大匹配**两种模式 |
|[汉字转**拼音**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-汉字转拼音)    | pinyin | 找出中文文本对应的汉语拼音，并可返回**声母**、**韵母**、**声调**   |
|[汉字转**偏旁与字形**](https://github.com/dongrixinyu/JioNLP/wiki/Gadget-说明文档#user-content-汉字转偏旁与字形)    | char_radical | 找出中文文本对应的汉字字形结构信息，包括**偏旁部首**(“河”氵)、**字形结构**(“河”左右结构)、**四角编码**(“河”31120)、**汉字拆解**(“河”水可) |

### 4.词典加载与使用

| 功能   | 函数   |描述   |
|--------|--------|-------|
|<div style="width: 150pt">[**成语**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载成语词典) | chinese_idiom_loader |加载成语词典 |
|[**歇后语**词典](https://github.com/dongrixinyu/JioNLP/wiki/词典加载-说明文档#user-content-加载歇后语词典) | xiehouyu_loader |加载歇后语词典 |




### 开源不易，欢迎自由投食 (#^.^#)

![image](https://github.com/dongrixinyu/JioNLP/blob/master/qr_code_for_collection.jpg)


