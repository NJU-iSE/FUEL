import math
import random
from collections import defaultdict as df
from typing import List

from ..feedback.feedback import FeedBack
from ..utils.Filer import File


class Operator:
    def __init__(self, op_name: str):
        self.op_name = op_name
        self.used_times = 0  # Number of uses
        self.exception_count = 0  # The potential number of exceptions.
        self.cov_count = 0  # Potential lines triggered for coverage.
        self.value = 0  # The current operator's value.
        self.flag = True  # Whether it is the first use.


class FASA:
    """
    FASA: Feedback-Aware Simulated Annealing
    T0: Initial temperature
    Tmin: Termination temperature
    alpha: Cooling rate
    """

    def __init__(self, T0, Tmin, alpha, filename):
        self.ops = df(lambda: Operator("None"))
        self.T0 = T0
        self.Tmin = Tmin
        self.alpha = alpha
        self.select_numbers = 1
        # The number of times the same ops encountered errors and bugs consecutively.
        self.cnt = 0
        with open(filename) as f:
            for op in f.readlines():
                op = op.strip("\n")
                self.ops[op] = Operator(op)

    def get_ops(self) -> List[str]:
        if FeedBack.cur_ops:
            # update the value of last ops!
            content = ""
            for op in FeedBack.cur_ops:
                self.ops[op].used_times += 1
                if self.ops[op].exception_count < 100:
                    self.ops[op].exception_count += FeedBack.has_exception
                # Since the number of covered lines in the first calculation is large, it is skipped directly.
                if FeedBack.success_times > 1:
                    self.ops[op].cov_count += FeedBack.delta_lines
                if self.ops[op].flag:
                    self.ops[op].flag = False
                content += f"{op}:{self.ops[op].value}   "
            File.write_file(
                File.ops_file,
                f"----Fuzzing Iteration.{FeedBack.cur_round}----\n{content}\n",
            )
        # init the parameter
        self.select_numbers = random.randint(1, 3)
        T = self.T0
        Tmin = self.Tmin
        select_list = list(self.ops.keys())
        ops = [self.ops[x] for x in random.sample(select_list, self.select_numbers)]
        value = self.cal_total_avg_value(ops)
        # Outer loop iteration
        while T > Tmin:
            # Inner loop iteration
            for _ in range(10):
                ops_new = [
                    self.ops[x] for x in random.sample(select_list, self.select_numbers)
                ]
                value_new = self.cal_total_avg_value(ops_new)
                value_delta = value_new - value
                # If value_delta < 0, accept it according to the Metropolis criterion.
                # [The higher the temperature, the greater the probability of acceptance!]
                if value_delta >= 0 or random.uniform(0, 1) < math.exp(value_delta / T):
                    value = value_new
                    ops = ops_new
                # if value_cur > value_best:
                #     value_best = value_new
                #     ops_best = ops_new
            T *= self.alpha
        selected_ops = [op.op_name for op in ops]
        return selected_ops

    def cal_value(self, op):
        value = (
            FASA.cal_used_times(op.used_times)
            + FASA.cal_exception_count(op.exception_count)
            + FASA.cal_cov_count(op.cov_count)
        )
        if self.ops[op.op_name].flag:
            value += 1
        self.ops[op.op_name].value = value / 3
        return value

    def cal_total_avg_value(self, selected_lst):
        ans = 0
        for op in selected_lst:
            ans += self.cal_value(op)
        return ans / len(selected_lst)

    @staticmethod
    def cal_used_times(x):
        return 1 / (1 + x)

    @staticmethod
    def cal_exception_count(x):
        return 1 / math.exp(x)

    @staticmethod
    def cal_cov_count(x):
        return 1 - math.exp(-x * 0.001)
