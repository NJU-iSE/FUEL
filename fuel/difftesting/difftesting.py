import subprocess as sp
import sys
from typing import Tuple

from ..feedback.feedback import FeedBack
from ..utils.Filer import File


class DiffTesting:
    diff_type = ""

    @classmethod
    def testing(cls) -> Tuple[int, int]:
        base_process = sp.Popen(
            cls.build_cmd("base"), stdout=File.open_file(File.validate_file)
        )
        base_code = base_process.wait()
        target_process = sp.Popen(
            cls.build_cmd("target"), stdout=File.open_file(File.validate_file)
        )
        target_code = target_process.wait()
        return base_code, target_code

    @classmethod
    def build_cmd(cls, testing_type) -> list:
        cov_file = (
            File.cov_base_file if testing_type == "base" else File.cov_target_file
        )
        res_file = (
            File.res_base_file if testing_type == "base" else File.res_target_file
        )
        version = (
            FeedBack.base_version if testing_type == "base" else FeedBack.target_version
        )
        return [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--rcfile={File.cov_rc_file}",
            f"--data-file={cov_file}",
            "-m",
            f"fuel.difftesting.validate_{testing_type}",
            f"--res_file={res_file}",
            f"--version={version}",
            f"--diff_type={cls.diff_type}",
            f"--code={File.rendered_code}",
            f"--code_file={File.tmp_py if File.lib == 'triton' else ''}",  # TODO@SHAOYU: in future, we should support code_file for pytorch
            f"--lib={File.lib}",
            f"--filename={File.cur_filename}",
            f"--err_file={File.err_file}",
            f"--total_errs_file={File.total_errs_file}",
        ]
