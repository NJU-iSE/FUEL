import ast
import re
from os import PathLike
from typing import Union

import yaml


def load_config_file(filepath: Union[str, PathLike]):
    """Loads a YAML configuration file."""
    with open(filepath, "r", encoding="utf-8") as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config


def text_splice(filepath, a, b):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(a, a + b)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)


def extra_code_from_text(input_text):
    pattern = r"```python([\s\S]*?)```"

    match = re.search(pattern, input_text, re.DOTALL)

    if match:
        return match.group(1).strip()
    else:
        return input_text


def extract_model_code(code: str) -> str:
    # print(f"[debug] the code is \n{code}")
    match = re.search(r"class\s+\w+\s*\(.*?inputs\s*=\s*\[.*?\]", code, re.DOTALL)
    # print(f"[debug] after re match , the code is \n{match.group(0)}")
    if match:
        return match.group(0)
    else:
        print("[debug] somthing is wrong")
        return code


def summarize_triton_code(code: str) -> str:
    try:
        tree = ast.parse(code)
    except Exception:
        return "unparseable triton test"

    kernel_count = 0
    tl_ops = set()
    has_reduction = False
    has_dot = False
    has_where = False
    has_broadcast = False
    has_2d_indexing = False
    has_multiple_kernels = False
    uses_float64 = False
    input_count = 0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for deco in node.decorator_list:
                if (
                    isinstance(deco, ast.Attribute)
                    and isinstance(deco.value, ast.Name)
                    and deco.value.id == "triton"
                    and deco.attr == "jit"
                ):
                    kernel_count += 1
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == "tl":
                op_name = f"tl.{node.func.attr}"
                tl_ops.add(op_name)
                if node.func.attr in {"sum", "max", "min"}:
                    has_reduction = True
                if node.func.attr == "dot":
                    has_dot = True
                if node.func.attr == "where":
                    has_where = True
                if node.func.attr in {"broadcast_to", "full", "zeros"}:
                    has_broadcast = True
        elif isinstance(node, ast.Attribute):
            if (
                isinstance(node.value, ast.Name)
                and node.value.id == "tl"
                and node.attr == "float64"
            ):
                uses_float64 = True
        elif isinstance(node, ast.Subscript):
            if isinstance(node.slice, ast.Tuple):
                has_2d_indexing = True
        elif isinstance(node, ast.Assign):
            if any(
                isinstance(target, ast.Name) and target.id == "inputs"
                for target in node.targets
            ):
                if isinstance(node.value, ast.List):
                    input_count = len(node.value.elts)

    has_multiple_kernels = kernel_count > 1
    op_list = ", ".join(sorted(tl_ops)[:8]) if tl_ops else "no tl ops detected"

    features = []
    if has_reduction:
        features.append("reduction")
    if has_dot:
        features.append("dot")
    if has_where:
        features.append("predicate")
    if has_broadcast:
        features.append("broadcast")
    if has_2d_indexing:
        features.append("2d-tile")
    if uses_float64:
        features.append("fp64")
    if has_multiple_kernels:
        features.append("multi-kernel")
    if not features:
        features.append("elementwise")

    return (
        f"{kernel_count} kernel(s); inputs={input_count}; features={', '.join(features)}; "
        f"ops={op_list}"
    )


def hour_to_second(time: str):
    assert "h" or "hour" in time, "time should contain `h` or `hour`"
    s = time.split("h")[0]
    return int(s) * 3600


def second_to_hour(time: str):
    assert "s" or "second" in time, "time should contain `s` or `second`"
    s = time.split("s")[0]
    return int(s) / 3600


def fill_instructions(prompt, instructions):
    pass
