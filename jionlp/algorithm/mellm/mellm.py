# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing tool for Chinese NLP


import pdb
import numpy as np


from jionlp.rule.prompt import *


class MELLM(object):
    """ MELLM algorithm, short for Mutual Evaluation of Large Language Model,
    which is an auto method to evaluate several LLMs.

    This evaluation algorithm applies EM algorithm to achieve the final result.


    Args:
        llm_names(list[str]): all the names of llms,
            such as chatgpt-3.5, 文心一言, skywork, gpt4, llama-7B, etc.


    Returns:
        dict[str,float]: scores of all llms.

    Examples:
        >>> import jionlp as jio
        >>> text = '喀左旗覃家岗街道梨树湾村芭蕉沟村民小组临.222号'
        >>> res = jio.parse_location(text)
        >>> print(res)

    """
    def __init__(self, llm_names, llm_apis, exam_questions):
        """ preparation before applying mellm.

        Args:
            llm_names(list[str]): all the names of llms,
                such as chatgpt-3.5, 文心一言, skywork, gpt4, llama-7B, etc.
            llm_apis: all the apis for llms in accordence with the sequence of llm_names
            exam_questions(list[dict]): all the questions of the exam,
                you can get it from `jio. ...`

        """
        self.llm_names = llm_names
        self.llm_names_dict = dict([(i, idx) for idx, i in enumerate(self.llm_names)])

        self.llm_apis = llm_apis

        # responses from llms answering questions from the given exam.
        self.llm_answers_to_questions = dict([(i, {}) for i in self.llm_names])
        """an example of self.llm_answers_to_questions
        {
            'chatgpt3.5': {
                0: 'A,B,C',
                1: '英国是正确答案',
                2: '从前有一个小孩子...'
            },
            'llama': {
                0: 'A,B is correct',
                1: '英国才是正确答案',
                2: '从前，有两个小孩子...'
            },
            'ChatGLM': {
                0: 'A,D',
                1: 'Italy 是正确的',
                2: '很久很久以前...'
            }
        }
        """

        # responses from llms giving scores for other models.
        self.llm_answers_to_grades = dict([(i, dict([(j, {}) for j in self.llm_names if i != j]))
                                           for i in self.llm_names])
        """an example of self.llm_answers_to_grades
        {
            'chatgpt3.5': {
                'llama': {
                    0: '2分',
                    1: '1分',
                    2: '4.5 分'      
                },
                'ChatGLM': {
                    0: '1',
                    1: '1.5',
                    2: '4 分' 
                }
            },
            'llama': {
                'chatgpt3.5': {
                    0: '2 分',
                    1: '这个答案可以得2分',
                    2: '5分。'
                },
                'ChatGLM': {
                    0: '1分',
                    1: '1.5。',
                    2: '5分。' 
                }
            },
            'ChatGLM': {
                ...
            }
        }
        """

        # all the questions
        self.exam_questions = exam_questions

        # to store all the moves when calling llm-apis
        self.storage_info = {}

    def answer_questions(self):
        """let llm answer questions from the given exam.

        each question has 'score', 'question_type', 'question', 'correct_answer',
        'correct_answer' may not exist for some questions. So these questions
        should be mutually evaluated by mellm.

        Args:

        Returns:
            None
        """

        for llm, llm_api in zip(self.llm_names, self.llm_apis):
            for idx, question_item in enumerate(self.exam_questions):

                # call the api to get result
                # all exceptions which might occur should be handled by the api itself.
                result = llm_api(question_item['question'])
                self.llm_answers_to_questions[llm].update({idx: result})

        # save all the result into file.

        for llm, llm_api in zip(self.llm_names, self.llm_apis):
            for _llm in self.llm_names:
                # _llm means models to be graded
                for idx, question_item in enumerate(self.exam_questions):

                    # grade another llms' exam
                    result = self.llm_answers_to_questions[llm][idx]
                    if 'correct_answer' not in question_item:
                        score = question_item['score']
                        question = question_item['question']
                        _input = GRADING_CHINESE_PROMPT_WITHOUT_CORRECT_ANSWER.format(
                            question, result, score)
                    else:
                        score = question_item['score']
                        question = question_item['question']
                        correct_answer = question_item['correct_answer']
                        _input = GRADING_CHINESE_PROMPT_WITHOUT_CORRECT_ANSWER.format(
                            question, result, score)

                    result = llm_api(_input)
                    self.llm_answers_to_grades[llm].update({idx: result})



