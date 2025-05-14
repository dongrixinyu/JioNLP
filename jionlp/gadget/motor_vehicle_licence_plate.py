# -*- coding=utf-8 -*-
# library: jionlp
# author: dongrixinyu
# license: Apache License 2.0
# email: dongrixinyu.89@163.com
# github: https://github.com/dongrixinyu/JioNLP
# description: Preprocessing & Parsing tool for Chinese NLP


import re
from jionlp import logging

from jionlp.rule.rule_pattern import MOTOR_VEHICLE_LICENCE_PLATE_PATTERN


class MotorVehicleLicencePlateParser(object):
    """ 车牌号码解析器，给定一个车牌号码，解析其对应的省、市、县。
    目前仅限于大陆车牌号。可正确解析普通 92 式车牌号，新能源车牌号。各种特殊用途如农机牌号、
    摩托牌号等，不在本工具考虑范围内。

    对于 京A、沪C 等字母不做解析，原因在于车牌定制十分复杂，难以面面俱到，也脱离文本解析本身。
    牌号指定规则和历史参考
        https://zh.wikipedia.org/wiki/中华人民共和国民用机动车号牌

    该工具配合 jio.extract_motor_vehicle_licence_plate 共同使用，先抽取，再识别

    Args:
        None

    Returns:
        dict: 车牌号解析结果字段

    Examples:
        >>> import jionlp as jio
        >>> text = '川A·23047B'
        >>> res = jio.parse_motor_vehicle_licence_plate(text)
        >>> print(res)

        # {'car_loc': '川A', 'car_type': 'PEV', 'car_size': 'big'}

    """

    def __init__(self):
        self.new_energy_vehicles_letter_map = None

    def _prepare(self):
        logging.info('`PEV`: 纯电动车；`NPEV`：非纯电动车。`GV`：普通燃油车。')

        pure_electric_vehicle = 'PEV'
        non_pure_electric_vehicle = 'NPEV'
        self.new_energy_vehicles_letter_map = {
            'A': pure_electric_vehicle,
            'B': pure_electric_vehicle,
            'C': pure_electric_vehicle,
            'D': pure_electric_vehicle,
            'E': pure_electric_vehicle,
            'F': non_pure_electric_vehicle,
            'G': non_pure_electric_vehicle,
            'H': non_pure_electric_vehicle,
            'J': non_pure_electric_vehicle,
            'K': non_pure_electric_vehicle,
        }
        self.motor_vehicle_licence_plate_check_pattern = re.compile(
            MOTOR_VEHICLE_LICENCE_PLATE_PATTERN)
        self.small_new_energy_pattern = re.compile(
            r'([ABCDEFGHJK][A-HJ-NP-Za-hj-np-z]\d{4}|[ABCDEFGHJK]\d{5})$')
        self.big_new_energy_pattern = re.compile(
            r'(\d{5}[ABCDEFGHJK])$')
        self.gap_chars = '·. 　'  # 内含全半角空格

    def __call__(self, motor_vehicle_licence_plate):
        if self.new_energy_vehicles_letter_map is None:
            self._prepare()

        # 检查是否符合车牌号规则
        match_flag = self.motor_vehicle_licence_plate_check_pattern.match(
            motor_vehicle_licence_plate)

        if match_flag is None:
            logging.error('the motor_vehicle_licence_plate `{}` is wrong.'.format(
                motor_vehicle_licence_plate))
            return None

        car_type = None
        car_size = None

        length = len(motor_vehicle_licence_plate)
        if length == 9:
            # 新能源车
            car_type, car_size = self._judge_new_energy_vehicle(motor_vehicle_licence_plate)

        elif length == 8:
            if motor_vehicle_licence_plate[2] in self.gap_chars:
                # 92式 普通油车
                car_type = 'GV'  # Gasoline Vehicle
            else:
                # 新能源车
                car_type, car_size = self._judge_new_energy_vehicle(
                    motor_vehicle_licence_plate)

        elif length == 7:
            # 92式 纯油车
            car_type = 'GV'  # Gasoline Vehicle

        else:
            # 不合规牌号
            logging.error('the motor_vehicle_licence_plate `{}` is wrong.'.format(
                motor_vehicle_licence_plate))
            return None

        return {'car_loc': motor_vehicle_licence_plate[:2],
                'car_type': car_type,
                'car_size': car_size}

    def _judge_new_energy_vehicle(self, new_energy_plate):
        # 判断新能源牌号，是否小型、是否纯电动车
        small_matched_res = self.small_new_energy_pattern.search(new_energy_plate)
        big_matched_res = self.big_new_energy_pattern.search(new_energy_plate)

        if small_matched_res and big_matched_res is None:
            car_type = self.new_energy_vehicles_letter_map[
                small_matched_res.group()[0]]
            return car_type, 'small'

        elif small_matched_res is None and big_matched_res:
            car_type = self.new_energy_vehicles_letter_map[
                big_matched_res.group()[-1]]
            return car_type, 'big'

        else:
            # 不合规牌号
            logging.error('the motor_vehicle_licence_plate `{}` is wrong.'.format(
                new_energy_plate))
            return None, None

