---
name: bug反馈
about: 反馈jionlp代码本身的bug
title: "[BUG]"
labels: bug
assignees: ''

---
**提问题时，请尊重我！把必要的信息，什么环境，输入具体什么文本，运行什么函数讲清楚！**
**不要甩一句话，说的不清不楚，我无从定位，浪费时间。这样的提单我将直接close。**

- 如果是关于时间解析的 bug，由于bug单很多，我没时间及时更新。可以自行解决一下。
- 解决思路：绝大多数时间解析报错，包括两种错误，一种是时间抽取错误，这是time_parser.py 中的各种时间正则匹配有问题，函数是 `def _preprocessing `。另一种是时间解析有问题，这是 `def parse_time_point` 函数，里面对应了大量的时间正则解析函数，以 normalize 开头。你可以 debug 看看你的错误字符串对应在哪些正则小类里面，自行修改，提 PR 合在我的主线里。 

**描述(Description)**

> 描述你遇到了什么问题(Please describe your issue here)

1. 版本(Version):
- python 版本: (通过 `python` 可查)
- jionlp 版本: (通过 `jionlp.__version__` 可查)

2. jionlp的调用代码与输入文本(Code & Text):
```
xxxxxxxxxxxx
e.g.
import jionlp as jio
res = jio.parse_time('XXXX')
print(res)
```

3. 调用报错日志如下(Log):
```
xxxxxxxxxxxx
e.g.
trackback: XXXXXX
```


**期望行为(Expectation)**

> 若返回结果不理想，描述你期望发生的事情(Please describe your expectation)


**请顺手 star 一下右上角的⭐小星星**

