# TODO@SHAOYU: Evaluation process is so slow which makes me annoying. Can we execute concurrently in the future?
#  Bc our CPU has 20 cores and we have 4 GPUs.
import argparse
import json
import os
import re
import subprocess as sp

import matplotlib.pyplot as plt
from tqdm import tqdm

from fuel.exec.render_code import get_rendered_code
from fuel.utils.util import hour_to_second, second_to_hour

from .utils import get_all_pyfiles, read_pyfile, write_pyfile

CPU_EXEC = """
model(*inputs)
c_model = torch.compile(model, dynamic=True)
c_model(*inputs)
"""

CUDA_EXEC = """
from experiments.torch_utils import model_to_cuda

model, inputs = model_to_cuda(model, inputs)
model(*inputs)
c_model = torch.compile(model, dynamic=True)
c_model(*inputs)
"""

ACC_COV_LINES = []


def get_exec_code(device_backend: str) -> str:
    if device_backend == "cpu":
        return CPU_EXEC
    elif device_backend == "cuda":
        return CUDA_EXEC
    elif device_backend == "both":
        return CPU_EXEC + CUDA_EXEC
    else:
        raise ValueError(f"not support this device backend: {device_backend}")


# Please use python experiments/run_coverage.py to run this script!
def collect_cov(tech, lib):
    process1 = sp.Popen(
        [
            "coverage",
            "report",
            "--data-file",
            f"experiments/.{tech}_{lib}_coverage",
        ],
        stdout=sp.PIPE,
        stderr=sp.PIPE,
        text=True,
    )

    stdout, _ = process1.communicate()

    for cov_line in stdout.split("\n")[::-1]:
        if cov_line.startswith("TOTAL"):
            cov_line = [x for x in cov_line.split(" ") if x != ""]
            total_lines = int(cov_line[1]) - int(cov_line[2])
            ACC_COV_LINES.append(total_lines)
            # print(ACC_COV_LINES)
            break


def coverage_report(
    tech: str,
    lib: str,
    folder_path: str,
    samples: int,
    time_stamp: str,
    device_backend: str,
):
    if os.path.exists(f"experiments/.{tech}_{lib}_coverage"):
        os.remove(f"experiments/.{tech}_{lib}_coverage")
    exec_code = get_exec_code(device_backend)

    if lib == "pytorch":
        import torch

        os.environ["TESTED_LIB_PATH"] = os.path.dirname(torch.__file__)
    elif lib == "tensorflow":
        import tensorflow as tf

        os.environ["TESTED_LIB_PATH"] = os.path.dirname(tf.__file__)

    valid_number = 0
    all_pyfiles = get_all_pyfiles(folder_path)

    if tech.startswith("fuel"):
        all_pyfiles = sorted(
            (f for f in all_pyfiles if f.endswith(".py")),
            key=lambda x: int(x.split("/")[-1].split(".")[0]),
        )
    else:
        all_pyfiles = sorted(all_pyfiles)

    # time process
    if time_stamp is not None:
        second_time = (
            hour_to_second(time_stamp) if ("h" or "hour") in time_stamp else time_stamp
        )
        hour_time = (
            second_to_hour(time_stamp)
            if ("s" or "second") in time_stamp
            else time_stamp
        )
        all_pyfiles = [
            f
            for f in all_pyfiles
            if int(os.path.basename(f).split(".")[0]) <= int(second_time)
        ]
        print(
            f"[time budget] running coverage collection on {hour_time} fuzzing budget"
        )
        print(f"[number of tests] {len(all_pyfiles)}")

    if samples != 0 and samples < len(all_pyfiles):
        sampled_pyfiles = all_pyfiles[:samples]
    else:
        sampled_pyfiles = all_pyfiles

    for py_file in tqdm(sampled_pyfiles):
        py_code = read_pyfile(py_file)
        try:
            py_code = get_rendered_code(lib, py_code)
        except Exception:
            print("invalid test case!")
            collect_cov(tech, lib)
            continue
        if lib == "pytorch":
            py_code = py_code + "\n" + exec_code
        elif lib == "tensorflow":
            idx = py_code.find("def call")
            code_to_compile = (
                py_code[:idx]
                + "@tf.function(jit_compile=True)"
                + "\n    "
                + py_code[idx:]
            )
            py_code = py_code + "\n" + code_to_compile
        tmp_pyfile = "tmp.py"
        write_pyfile(tmp_pyfile, py_code)
        process = sp.Popen(
            [
                "python",
                "-m",
                "coverage",
                "run",
                "-a",
                "--rcfile=experiments/.coveragerc",
                f"--data-file=experiments/.{tech}_{lib}_coverage",
                f"{tmp_pyfile}",
            ],
            stdout=sp.PIPE,
            stderr=sp.PIPE,
        )
        try:  # @SHAOYU: I add this exception processing to avoid the timeout (bc some test case are too slow to make the process lock)
            process.communicate(timeout=90)
            if process.returncode == 0:
                valid_number += 1
            else:
                # print(process.stderr)
                print(f"[exception] return code is {process.returncode}")
        except sp.TimeoutExpired:
            print("[timeout]: kill this test case")
            process.terminate()

        collect_cov(tech, lib)

    dt = {f"{tech}": ACC_COV_LINES}
    print(f"Total number is {len(sampled_pyfiles)}. Valid number is {valid_number}")
    # print(accumulate_coverage_lines)
    json.dump(dt, open(f"experiments/{tech}_{lib}_coverage.json", "w"))

    x = [i for i in range(1, len(ACC_COV_LINES) + 1)]
    y = ACC_COV_LINES
    plt.plot(x, y)
    plt.savefig(f"experiments/{tech}_{lib}_coverage.png")

    # remove_pyfile("tmp.py")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get total coverage of fuel")
    parser.add_argument(
        "--tech",
        type=str,
        default="fuel",
        required=False,
        help="fuel or whitefox",
    )
    parser.add_argument(
        "--lib",
        type=str,
        default="pytorch",
        required=False,
        help="pytorch or tensorflow",
    )
    parser.add_argument(
        "--folder",
        type=str,
        default="results/fuel/pytorch",
        required=False,
        help="folder path of fuel",
    )
    parser.add_argument(
        "--samples", type=int, default=1000, required=False, help="number of samples"
    )
    parser.add_argument(
        "--time_stamp",
        type=str,
        default=None,
        required=False,
        help="collect code coverage based on time stamps",
    )
    parser.add_argument(
        "--device_backend",
        type=str,
        default="both",
        required=False,
        help="device backend: cpu or cuda (note that we can run these both on cpu and cuda if set `both`)",
    )
    args = parser.parse_args()

    assert re.fullmatch(r"^fuel.*|whitefox", args.tech), (
        f"not support this tech: {args.tech}"
    )
    assert args.lib in ["pytorch", "tensorflow"], f"not support this lib: {args.lib}"
    assert args.device_backend in ["cpu", "cuda", "both"], (
        f"not support this device backend: {args.device_backend}"
    )

    coverage_report(
        args.tech,
        args.lib,
        args.folder,
        args.samples,
        args.time_stamp,
        args.device_backend,
    )
