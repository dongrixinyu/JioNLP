# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP
# website: http://www.jionlp.com/

# This file is an example for how to use MELLM to evaluate LLMs.
import os
import json
import numpy as np
import jionlp as jio


# NOTICE: denote norm score file path to the following variable.
# You can download test sample from
# download like: https://pan.baidu.com/s/18Ufx51v05gyVkBoCo8fupw
# secret code: jmbo

# Or if you wanna evaluate more LLMs, just try to get your custom norm_score.json
# Or if you wanna evaluate on other datasets, just try to get your custom max_score.json
NORM_SCORE_FILE_PATH = '/path/to/your/norm_score.json'
MAX_SCORE_FILE_PATH = '/path/to/your/max_score.json'

with open(NORM_SCORE_FILE_PATH, 'r', encoding='utf-8') as fr:
    score_json = json.load(fr)

llm_names = list(score_json.keys())

with open(MAX_SCORE_FILE_PATH, 'r', encoding='utf-8') as fr:
    max_json = json.load(fr)


# get the grading_matrix numpy
grading_matrix = np.zeros((len(llm_names), len(llm_names), len(max_json)))

# get errors when grading, some LLM may refuse to give a score for an answer, which is
# recorded as -1 in the `norm_score.json`. The more times -1 exists, the worse LLM is.
llm_grading_error_json = {}

for llm_idx, llm in enumerate(llm_names):
    _llm_grading_json = {}  # storing scores
    error_count = 0

    for _llm_idx, _llm in enumerate(llm_names):
        max_score_sum = 0
        total_score_sum = 0

        for idx, (key, value) in enumerate(score_json[llm][_llm].items()):
            # print(key, value)
            if 0 <= value <= max_json[key]:
                # it means the score is rational, otherwise it gets a mistake when grading.
                total_score_sum += value
                max_score_sum += max_json[key]

            else:
                error_count += 1
        # print('{} => {}: {}'.format(llm, _llm, total_score_sum / max_score_sum))
        _llm_grading_json.update(
            {_llm: [total_score_sum / max_score_sum, error_count]})

        # put the score into the grading_matrix
        for idx, (key, value) in enumerate(score_json[llm][_llm].items()):
            # print(key, value)
            if 0 <= value <= max_json[key]:
                grading_matrix[llm_idx][_llm_idx][idx] = value

            else:
                # if LLM gives a mistake, then use the average score.
                # This may cause the variation to be less than the real situation,
                # which has been considered in MELLM.
                grading_matrix[llm_idx][_llm_idx][idx] = total_score_sum / max_score_sum

    _llm_grading_json = dict(sorted(
        _llm_grading_json.items(), key=lambda i: i[1][0], reverse=True))

    llm_grading_error_json.update({llm: error_count})

    print('Model grading others: ', llm)
    print('\tModel to be graded: ')
    for k, v in _llm_grading_json.items():
        print('\t{:<20} {:.3f}'.format(k, v[0] * 100))

    print()

llm_error_count = list(llm_grading_error_json.values())
mellm = jio.mellm.MELLM(llm_names, llm_names, max_json)

# jionlp offers two methods to approximation.
# run_whole and run_singular, there methods are a little bit different from each other.
# You can choose either to test.
if False:
    mellm.run_whole(grading_matrix, llm_error_count)
else:
    mellm.run_singular(grading_matrix, llm_error_count)
