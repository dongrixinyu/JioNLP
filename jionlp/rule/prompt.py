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

请根据以上问题，正确答案，对答题者的回答正确与否，以及回答质量打分，满分 {score} 分，分值粒度 0.5 分：

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

请根据以上问题，对答题者的回答正确与否，以及回答质量打分，满分 {score} 分，分值粒度 0.5 分：

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
