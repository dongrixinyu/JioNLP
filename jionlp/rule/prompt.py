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

# 这个 prompt 最好用 GPT-4 来调用，效果拔群
NORMALIZE_GRADING_CHINESE_PROMPT_SCORING = """我将给你一段文字，是一个评委老师对一个考生所回答问题的评价：

```
{grading_result}
```

该问题的满分是 {score} 分，结合上述评价，请告诉我，评委老师给考生最终给出了多少分？
注意事项：
- 若文中没有明说分数，则告诉我评委老师最可能给出了多少分？
- 若该段评价内容和给出的分数不太相符，如回答错误，却给了较高分数；回答有瑕疵，却给了满分等，则告诉我依据评价内容的正确打分。
- 若该段评价拒绝评价，或打分前言不搭后语，逻辑很差，则给出分数为 -1 分。

分数请以 json 格式告诉我，字段名为 `score`，不要返回除 json 以外的其它信息。

"""


NORMALIZE_GRADING_ENGLISH_PROMPT_SCORING = """I will give you a piece of text which is an evaluation by an evaluator on a test taker's answer:

```
{grading_result}
```

The full score for this question is {score} points. Based on the above evaluation, please tell me how many points the evaluator gave to the result?

Note:
- If the text does not explicitly state the score, then tell me what score the evaluator is most likely to have given.
- If the content of the evaluation does not match the score given, such as giving a high score for a wrong answer or a highest score despite flaws, then tell me the correct score based on the content of the evaluation.
- If the evaluation refuses to rate or the scoring preamble is inconsistent with the postscript and the logic is poor, then score -1 point.
- Please tell me the score in JSON format, with the only field name being `score`, and do not return redundant information except JSON.

"""
