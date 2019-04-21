#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import copy
import os
import random
from decimal import Decimal
from pathlib import Path


class Operations:
    """
    Класс математических операций
    """

    def __init__(self):
        pass

    Add = 1
    Sub = 2
    Mul = 3
    Div = 4

    @classmethod
    def get_random_operation(cls, allowed_operations):
        """
        Возвращает случайную математическую операцию
        """
        return random.choice(allowed_operations)

    @classmethod
    def get_operation_description(cls, operation):
        """
        Возвращает знак операции в виде строки
        """
        return {
            Operations.Add: u'+',
            Operations.Sub: u'-',
            Operations.Mul: u'\u2219',
            Operations.Div: u':'
        }[operation]

    @classmethod
    def execute_operation(cls, operation, left, right):
        """
        Выполняет операцию над переданными аргументами
        """

        def op_add():
            return left + right

        def op_sub():
            return left - right

        def op_mul():
            return left * right

        def op_div():
            return left / right

        return Decimal(
            {
                Operations.Add: op_add,
                Operations.Sub: op_sub,
                Operations.Mul: op_mul,
                Operations.Div: op_div
            }[operation]())

    @classmethod
    def get_operation_priority(cls, operation):
        """
        Возвращает приоритет операции
        """
        return Decimal(
            {
                Operations.Add: 1,
                Operations.Sub: 1,
                Operations.Mul: 2,
                Operations.Div: 2
            }[operation])


def generate_tasks(task_count, max_argument_count, min_argument_value, max_argument_value, max_digit_count,
                   allowed_operations):
    """
    Создает и возвращает список примеров
    :param task_count число примеров
    :param max_argument_count количество чисел в примере
    :param min_argument_value минимальное значение аргумента
    :param max_argument_value максимальное значение аргумента
    :param max_digit_count максимальное число знаков после запятой
    :param allowed_operations допустимые арифметические операции
    :type task_count: int
    :type max_argument_count: int
    :type min_argument_value: double
    :type max_argument_value: double
    :type max_digit_count: int
    :type allowed_operations: list of int
    """
    if not allowed_operations:
        allowed_operations = []

    def get_arguments(input_max_argument_count, input_min_argument_value, input_max_argument_value,
                      input_max_digit_count):
        """
        Возвращает указанное количество случайных чисел которые будут использоваться как аргументы в задании
        :param input_max_argument_count  максимальное количество чисел в примере
        :param input_min_argument_value минимальное значение аргумента
        :param input_max_argument_value максимальное значение аргумента
        :param input_max_digit_count максимальное число знаков после запятой
        :type input_max_argument_count: int
        :type input_min_argument_value: double
        :type input_max_argument_value: double
        :type input_max_digit_count: int
        """
        one = Decimal('1')

        while True:
            arguments = []
            for _ in range(random.randint(2, input_max_argument_count)):
                argument = Decimal(random.uniform(input_min_argument_value, input_max_argument_value))\
                    .quantize(Decimal('10') ** -random.randint(0, input_max_digit_count))

                arguments.append(argument)

            if input_max_digit_count == 0:
                return arguments

            if 1 >= [(argument % one).is_zero() for argument in arguments].count(True):
                return arguments

    def get_complete_expression(arguments, input_allowed_operations):
        """
        Возвращает список готовых выражений для задания и ответ
        :param arguments аргументы для которых составляется выражение
        :param input_allowed_operations допустимые арифметические операции
        """
        result_expression = []

        for i in range(len(arguments)):
            result_expression.append(arguments[i])
            result_expression.append(Operations.get_random_operation(input_allowed_operations))

        del result_expression[-1]
        return result_expression

    def get_expression_result(input_expression):
        """
        Рассчитывает результат выражения
        :param input_expression выражение
        """
        quantize = Decimal('10') ** -max_digit_count
        operations_stack = []
        out_expression = []

        # Используется алгоритм Дейкстры для расчета преобразования и расчета выражения

        # Преобразовываем выражение
        for lexeme in input_expression:
            if isinstance(lexeme, Decimal):
                out_expression.append(lexeme)

            elif isinstance(lexeme, int):
                priority = Operations.get_operation_priority(lexeme)

                while len(operations_stack) > 0 and Operations.get_operation_priority(
                        operations_stack[-1]) >= priority:
                    out_expression.append(operations_stack.pop())

                operations_stack.append(lexeme)

        out_expression.extend(operations_stack)

        #  Рассчитываем значение выражения
        argument_stack = []

        for lexeme in out_expression:
            if isinstance(lexeme, Decimal):
                argument_stack.append(lexeme)

            elif isinstance(lexeme, int):
                right = argument_stack.pop()
                left = argument_stack.pop()
                argument_stack.append(Operations.execute_operation(lexeme, left, right))

        return Decimal(argument_stack[0]).quantize(quantize)

    random.seed()
    result_tasks = []
    max_argument_count = max(max_argument_count, 2)

    while len(result_tasks) < task_count:
        expression = get_complete_expression(
            get_arguments(max_argument_count, min_argument_value, max_argument_value, max_digit_count),
            allowed_operations)
        result = get_expression_result(expression)

        if result > 0:
            expression.append(result)
            result_tasks.append(expression)

    return result_tasks


def get_expression_as_string(expression, with_answer):
    """
    Возвращает выражение в человекочитаемом виде в виде строки
    :param expression выражение
    :param with_answer добавить ответ
    """
    out_expression = copy.deepcopy(expression)
    del (out_expression[-1])
    result = ""

    for lexeme in out_expression:
        if isinstance(lexeme, Decimal):
            if lexeme < 0:
                result += " ({0})".format(lexeme)
            else:
                result += " {0}".format(lexeme)

        elif isinstance(lexeme, int):
            result += " " + Operations.get_operation_description(lexeme)

    result += " = "

    if with_answer:
        result += str(expression[-1])

    return result.strip(" ").replace(".", ",")


if '__main__' == __name__:
    out_folder = Path.joinpath(Path.home(), "Documents")
    tasksFilename = Path.joinpath(out_folder, "Задания.txt")
    tasksWithAnswersFilename = Path.joinpath(out_folder, "Задания с ответами.txt")

    tasks = generate_tasks(
        task_count=100,
        max_argument_count=3,
        min_argument_value=-100,
        max_argument_value=+100,
        max_digit_count=1,
        allowed_operations=[Operations.Sub])

    if tasksFilename.is_file():
        os.remove(tasksFilename.as_posix())

    if tasksWithAnswersFilename.is_file():
        os.remove(tasksWithAnswersFilename.as_posix())

    with tasksFilename.open("w") as outFile:
        for index, task in enumerate(tasks):
            outFile.write(u"{0}) {1}\n".format(index + 1, get_expression_as_string(task, False)))

    with tasksWithAnswersFilename.open("w") as outFile:
        for index, task in enumerate(tasks):
            outFile.write(u"{0}) {1}\n".format(index + 1, get_expression_as_string(task, True)))
