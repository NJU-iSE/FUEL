import argparse
import os
from typing import List

import torch

from ..exec.utils import to_cuda
from .common import record_exception, torch_save
from .oracle import OracleType

os.environ["PYTHONWARNINGS"] = "ignore"
model: torch.nn.Module
inputs: List[torch.tensor]


def main(diff_type, code, res_file, version, filename, err_file, total_errs_file, lib):
    global model, inputs
    torch.manual_seed(0)
    exec(code, globals())
    model.eval()
    if diff_type == "hardware":
        try:
            model, inputs = to_cuda(model, inputs)
            print(f"<-- {version} transfer successfully -->")
        except Exception as e:
            print(f"<-- {version} transfer failed -->")
            record_exception(e, version, filename, err_file, total_errs_file)
            exit(OracleType.TRANSFER_EXCEPTION)

    elif diff_type == "cpu_compiler":
        try:
            model = torch.compile(model, dynamic=True)
            print(f"<-- {version} transfer successfully -->")
        except Exception as e:
            print(f"<-- {version} transfer failed -->")
            record_exception(e, version, filename, err_file, total_errs_file)
            exit(OracleType.TRANSFER_EXCEPTION)
    elif diff_type == "cuda_compiler":
        model, inputs = to_cuda(model, inputs)
        try:
            model = torch.compile(model, dynamic=True)
            print(f"<-- {version} transfer successfully -->")
        except Exception as e:
            print(f"<-- {version} transfer failed -->")
            record_exception(e, version, filename, err_file, total_errs_file)
            exit(OracleType.TRANSFER_EXCEPTION)
    else:
        raise ValueError(
            f"diff_type: hardware, cpu_compiler or cuda_compiler. Currently, diff_type: <{diff_type}>"
        )
    try:
        res = model(*inputs)
        torch_save(res, res_file)
        print(f"<-- {version}:Succeed -->")
        exit(OracleType.TARGET_SUCCESS)
    except Exception as e:
        print(f"<-- {version}:Failed -->")
        record_exception(e, version, filename, err_file, total_errs_file)
        exit(OracleType.TARGET_EXCEPTION)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff_type", type=str, default="hardware")
    parser.add_argument("--code", type=str, default="import torch\n")
    parser.add_argument("--res_file", type=str, default="")
    parser.add_argument("--version", type=str, default="")
    parser.add_argument("--lib", type=str, default="")
    parser.add_argument("--filename", type=str, default="")
    parser.add_argument("--err_file", type=str, default="")
    parser.add_argument("--total_errs_file", type=str, default="")
    args = parser.parse_args()
    main(
        args.diff_type,
        args.code,
        args.res_file,
        args.version,
        args.filename,
        args.err_file,
        args.total_errs_file,
        args.lib,
    )
