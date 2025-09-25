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


def eliminate_imports(code: str) -> str:
    # print(f"[debug] the code is \n{code}")
    match = re.search(r"class\s+\w+\s*\(.*?inputs\s*=\s*\[.*?\]", code, re.DOTALL)
    # print(f"[debug] after re match , the code is \n{match.group(0)}")
    if match:
        return match.group(0)
    else:
        print("[debug] somthing is wrong")
        return code


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
