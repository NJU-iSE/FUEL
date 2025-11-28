import os
import subprocess as sp
import warnings
from collections import defaultdict as df

from coverage import Coverage

from ..difftesting.oracle import OracleType
from ..utils.Filer import File
from .execution_status import ExecutionStatus

warnings.filterwarnings("ignore")


class FeedBack:
    cur_round = 0
    lib = "pytorch"
    feedback_code = OracleType.UNKNOWN
    # This is for our project in fuzzing loop!
    total_lines, cur_lines, delta_lines = 0, 0, 0
    total_coverage, cur_coverage, delta_coverage = df(set), df(set), df(set)
    # This is for the whole coverage in DL Framework!
    whole_lines, whole_coverage = 0, df(set)

    # True If has bug, it is deemed as True.
    has_bug, has_exception = False, False
    cur_ops, new_ops = [], []

    # This is for tesing effectiveness of our method!
    fix_total_times, fix_success_times, fix_fail_times, fix_failed = 0, 0, 0, False

    # record success times and unconsistent times!
    success_times, cons_fail = 0, 0
    base_version, target_version = None, None

    # Feedback init!
    @classmethod
    def init(cls, lib, diff_type):
        if diff_type == "hardware":
            cls.base_version = "CPU"
            cls.target_version = "CUDA"
        elif diff_type == "cpu_compiler":
            cls.base_version = "Eager(CPU)"
            cls.target_version = "Compiler(CPU)"
        elif diff_type == "cuda_compiler":
            cls.base_version = "Eager(CUDA)"
            cls.target_version = "Compiler(CUDA)"
        else:
            cls.base_version = "Base"
            cls.target_version = "Target"

        if lib == "pytorch":
            import torch

            cls.lib = "pytorch"
            source_path = os.path.dirname(torch.__file__)
        elif lib == "tensorflow":
            import tensorflow as tf

            cls.lib = "tensorflow"
            source_path = os.path.dirname(tf.__file__)
        else:
            source_path = ""
            pass
        # Initialize the whole lines!
        cov = Coverage(source=[source_path])
        cov.start()
        cov.stop()
        cov.save()

        process = sp.Popen("coverage lcov --data-file=.coverage", shell=True)
        process.wait()

        with open("coverage.lcov", "r") as f:
            for line in f.readlines():
                if line.startswith("SF:"):
                    if cls.lib == "pytorch":
                        filename = line.split("SF:")[1].strip().split("/torch/")[-1]
                    elif cls.lib == "tensorflow":
                        filename = (
                            line.split("SF:")[1].strip().split("/tensorflow/")[-1]
                        )
                elif line.startswith("DA:"):
                    data = line.strip("\n").split("DA:")[1].split(",")
                    try:
                        lineno, _ = data
                        cls.whole_coverage[filename].add(int(lineno))
                    except Exception as e:
                        print(e)

        for line in cls.whole_coverage.values():
            cls.whole_lines += len(line)
        os.remove(".coverage")
        os.remove("coverage.lcov")

    # Get delta coverage!
    @classmethod
    def get_delta_coverage(cls):
        text = ""
        cov_flag = False
        for pyfile, line_sets in cls.delta_coverage.items():
            # If set is empty, don't print, it's easier to observe!
            if len(line_sets) != 0:
                text += f"{pyfile}: {len(line_sets)} line(s) of code\n"  # Use code lines
                cov_flag = True
        if not cov_flag:
            text += "No new coverage is triggered.\n"
        return cov_flag, text

    # Get current coverage!
    @classmethod
    def get_cur_coverage(cls):
        ans = "The current coverage follows up:\n"
        for pyfile, line_sets in cls.cur_coverage.items():
            # If set is empty, don't print, it's easier to observe!
            if len(line_sets) != 0:
                ans += f"{pyfile}:{line_sets}\n"
        return ans

    @classmethod
    def cal_coverage(cls):
        cls.cur_coverage, cls.delta_coverage = df(set), df(set)

        cls.cur_lines = 0

        for cov_file in File.cov_base_file, File.cov_target_file:
            cov = Coverage(data_file=cov_file)
            cov.load()
            data = cov.get_data()
            for filename in data.measured_files():
                lines = data.lines(filename)
                if cls.lib == "pytorch":
                    pyfile = filename.split("/torch/")[-1]
                elif cls.lib == "tensorflow":
                    pyfile = filename.split("/tensorflow/")[-1]
                line_sets = set(lines)
                cls.cur_coverage[pyfile] = line_sets & cls.whole_coverage[pyfile]

        for pyfile, line_sets in cls.cur_coverage.items():
            cls.delta_coverage[pyfile] = line_sets - cls.total_coverage[pyfile]
            cls.delta_lines += len(cls.cur_coverage[pyfile])
            cls.total_lines += len(cls.delta_coverage[pyfile])
            cls.cur_lines += len(cls.cur_coverage[pyfile])
            cls.total_coverage[pyfile] = (
                cls.total_coverage[pyfile] | cls.delta_coverage[pyfile]
            )

        print("<-- Coverage calculation finished! -->")

    @classmethod
    def get_total_coverage(cls) -> str:
        """
        Get total coverage.
        """
        ans = "The total coverage follows up:\n"
        for pyfile, line_sets in FeedBack.total_coverage.items():
            ans += f"{pyfile}:{line_sets}\n"
        return ans

    # Get execution status
    @classmethod
    def get_status(cls) -> tuple[ExecutionStatus, str]:
        """
        Get execution status and detailed information
        
        Returns:
            tuple[ExecutionStatus, str]: 
                - ExecutionStatus: Execution status (SUCCESS/BUG/EXCEPTION)
                - str: Detailed message (success info/bug description/exception info)
        
        Status determination logic:
            - If err.log is empty, execution succeeded, return SUCCESS
            - If has_bug is True, oracle violation was triggered, return BUG
            - If has_exception is True, both backends threw exceptions (invalid test), return EXCEPTION
        """
        exception = File.read_file(File.err_file)
        
        if exception == "":
            # Execution succeeded without any errors
            return ExecutionStatus.SUCCESS, "Nothing Wrong"
        else:
            # Has error information, need to distinguish between bug and exception
            exception = exception.split('<string>", ')[-1]
            
            # Clear error file
            with open(File.err_file, "w") as f:
                f.write("")
            
            # Determine status based on has_bug and has_exception flags
            if cls.has_bug:
                # Oracle violation - different backends produce inconsistent results
                return ExecutionStatus.BUG, exception
            elif cls.has_exception:
                # Invalid test - both backends threw exceptions
                return ExecutionStatus.EXCEPTION, exception
            else:
                # Default case, treat as exception
                return ExecutionStatus.EXCEPTION, exception

    @classmethod
    def get_line_content(cls, filename: str, line_number_set: set) -> str:
        """
        According to the file name and line number, get the corresponding code line.
        """
        filename = File.get_library_path() + os.sep + filename
        with open(filename, "r") as f:
            content = f.read().split("\n")
            line_content = [content[i - 1] for i in sorted(line_number_set)]
        return "\n".join(line_content)

    @classmethod
    def get_validate_result(cls):
        """
        Get different backend tensor results.
        """
        if cls.lib == "pytorch":
            import torch

            if os.path.exists(File.res_base_file) and os.path.exists(
                File.res_target_file
            ):
                res_eager, res_compiler = (
                    torch.load(File.res_base_file, weights_only=False),
                    torch.load(File.res_target_file, weights_only=False),
                )
                return res_eager, res_compiler
            else:
                return torch.tensor([]), torch.tensor([])
        elif cls.lib == "tensorflow":
            import tensorflow as tf

            if os.path.exists(File.res_base_file) and os.path.exists(
                File.res_target_file
            ):
                res_eager, res_compiler = (
                    tf.io.parse_tensor(
                        tf.io.read_file(File.res_base_file), out_type=tf.float32
                    ),
                    tf.io.parse_tensor(
                        tf.io.read_file(File.res_target_file), out_type=tf.float32
                    ),
                )
                return res_eager, res_compiler
            else:
                return tf.constant([]), tf.constant([])
