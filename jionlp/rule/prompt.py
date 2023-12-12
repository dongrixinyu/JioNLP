# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com/

# prompt for mellm
GRADING_CHINESE_PROMPT_WITH_CORRECT_ANSWER = """我将给你一个问题和一个对应的答案，这是一个答题者回答的，请对这个答题者的答案正确与否，以及回答质量给出打分。

【问题】：
```
{question}
```

【该问题的标准答案】：
```
{correct_answer}
```

【答题者给出的回答】：
```
{response}
```

请根据以上问题，正确答案，对答题者的回答正误与质量给出一个综合打分，满分 {score} 分，分值粒度 0.5 分：

"""

GRADING_CHINESE_PROMPT_WITHOUT_CORRECT_ANSWER = """我将给你一个问题和一个对应的答案，这是一个答题者回答的，请对这个答题者的答案正确与否，以及回答质量给出打分。

【问题】：
```
{question}
```

【答题者给出的回答】：
```
{response}
```

请根据以上问题，对答题者的回答正误与质量给出一个综合打分，满分 {score} 分，分值粒度 0.5 分：

"""

GRADING_ENGLISH_PROMPT_WITH_CORRECT_ANSWER = """
I will give you a question and a corresponding answer which is provided by a person.
Please give me a score measuring if this answer is correct and its quality. 

【Question】: 
```
{question}
```

【Correct Answer】: 
```
{correct_answer}
```

【Answer of this person】: 
```
{response}
```

According to the above, please give me a score measuring if this answer is correct and its quality.
The highest score is {score}, grading granularity is 0.5:

"""

GRADING_ENGLISH_PROMPT_WITHOUT_CORRECT_ANSWER = """
I will give you a question and a corresponding answer which is provided by a person.
Please give me a score measuring if this answer is correct and its quality. 

【Question】:
```
{question}
```

【Answer of this person】: 
```
{response}
```

According to the above, please give me a score measuring if this answer is correct and its quality.
The highest score is {score}, grading granularity is 0.5:

"""

NORMALIZE_GRADING_CHINESE_PROMPT_SCORING = """我将给你一段文字，是一个评委老师对一个考生所回答问题的评价：

```
{grading_result}
```

该问题的满分是 {score} 分，结合上述评价，请告诉我，评委老师给考生最终给出了多少分？若文中没有明说，则告诉我评委老师最可能给出了多少分？

分数请以 json 格式告诉我，字段名为 `score`，不要返回除 json 以外的其它信息。

"""
