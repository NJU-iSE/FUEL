import os

os.environ["PYTHONWARNINGS"] = "ignore"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
import ast
from typing import List

import astunparse
from loguru import logger

class MultilineAssignTransformer(ast.NodeTransformer):
    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            if len(node.targets[0].elts) == len(node.value.elts):
                return [
                    ast.Assign(targets=[t], value=v)
                    for t, v in zip(node.targets[0].elts, node.value.elts)
                ]
        return node


class LibAssignRemover(ast.NodeTransformer):
    def __init__(self, lib_name: str = "pytorch") -> None:
        super().__init__()
        self.lib_name = lib_name

    def visit_Assign(self, node):
        if any(self.is_lib_attribute(target) for target in node.targets):
            return ast.Pass()
        return self.generic_visit(node)

    def is_lib_attribute(self, node):
        node_value_id = "torch" if self.lib_name == "pytorch" else "tf"
        if isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == node_value_id:
                return True
            return self.is_lib_attribute(node.value)
        return False


class CodeParser:
    def __init__(self, lib_name: str = "pytorch") -> None:
        self.transformers = [MultilineAssignTransformer(), LibAssignRemover(lib_name)]
        self.lib_name = lib_name
        if lib_name == "pytorch":
            import torch

            self.is_input = lambda x: torch.is_tensor(x)
            self.imports = (
                "import os\nimport torch\nimport torch.nn.functional as F\nimport torch.nn as nn\n"
                "import numpy as np\nfrom torch.autograd import Variable\nimport math\n"
                "import torch as th\nimport torch.linalg as la\n"
                "from torch.nn import Parameter\n"
                "import torch.linalg as linalg\n"
                "from torch._inductor import config\nconfig.fallback_random = True\n"  # ADD@SHAOYU: deterministic setting
                "torch.set_grad_enabled(False)\n"  # ADD@SHAOYU: disable the grad
            )
            self._init_code = "{} = torch.randn(1, 1, 1)\n"
        elif lib_name == "tensorflow":
            import tensorflow as tf

            self.is_input = lambda x: tf.is_tensor(x)
            self.imports = (
                "import os\nimport tensorflow\nimport tensorflow as tf\nimport numpy as np\n"
                'os.environ["CUDA_VISIBLE_DEVICES"] = "-1"\n'
            )
            self._init_code = "{} = tf.random.normal([1, 1, 1])\n"
        else:
            raise NotImplementedError(f"Not implemented for {lib_name}")

    def input_init_code(self, arg_name):
        return self._init_code.format(arg_name)

    def split_func_tensor(self, code):
        # get the code of model
        code = self.preprocessing(code)
        tree = ast.parse(code)

        class_init_args = []
        class_init_required_args = []
        class_init_code = ""

        class_code = ""
        class_name = ""

        class_forward_args = []
        class_forward_required_args = []

        inputs: List[str] = []
        input_init_code = ""

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                class_code += ast.unparse(node) + "\n\n"
                class_name = node.name
                # get the arguments the initiation of this class
                try:
                    init_method = next(
                        node
                        for node in ast.walk(node)
                        if isinstance(node, ast.FunctionDef) and node.name == "__init__"
                    )

                    class_init_args = [arg.arg for arg in init_method.args.args[1:]]
                    defaults = init_method.args.defaults
                    class_init_required_args = class_init_args[
                        : len(class_init_args) - len(defaults)
                    ]
                except Exception:
                    pass

                try:
                    call_function_name = (
                        "forward" if self.lib_name == "pytorch" else "call"
                    )
                    forward_method = next(
                        node
                        for node in ast.walk(node)
                        if isinstance(node, ast.FunctionDef)
                        and node.name == call_function_name
                    )
                    class_forward_args = [
                        arg.arg for arg in forward_method.args.args[1:]
                    ]
                    defaults = forward_method.args.defaults
                    class_forward_required_args = class_forward_args[
                        : len(class_forward_args) - len(defaults)
                    ]
                except Exception:
                    pass

            elif isinstance(node, ast.Assign):
                value = node.value
                if isinstance(value, ast.Call):
                    # first check whether is initialization of the class
                    if isinstance(value.func, ast.Name) and value.func.id == class_name:
                        # first split the tensor arguments and non-tensor arguments
                        # Fix: We should consider the keywords init of model class.
                        keywords = {kw.arg: kw.value for kw in value.keywords}
                        if (
                            len(class_init_required_args)
                            <= (len(value.args) + len(keywords))
                            <= len(class_init_args)
                        ):
                            class_init_code = "model = " + ast.unparse(value) + "\n"
                        else:
                            class_init_code = ""
                        continue

                    func = value.func  # noqa
                    args = value.args  # noqa

                    try:
                        tgt = node.targets[0].id
                    except Exception:
                        continue

                    init_code = ast.unparse(node)
                    if tgt not in inputs:
                        # we need the arg code
                        for arg in ast.walk(value):
                            if isinstance(arg, ast.Name):
                                init_code = (
                                    self.find_name_in_tree(tree, arg.id)
                                    + "\n"
                                    + init_code
                                )
                            elif isinstance(arg, ast.Starred):
                                if isinstance(arg.value, ast.Name):
                                    init_code = (
                                        self.find_name_in_tree(tree, arg.value.id)
                                        + "\n"
                                        + init_code
                                    )

                        # test whether is tensor
                        try:
                            namespace = globals().copy()
                            if self.lib_name == "tensorflow":
                                import tensorflow as tf  # noqa
                                namespace["tf"] = tf
                            elif self.lib_name == "pytorch":
                                import torch  # noqa
                                namespace["torch"] = torch
                            else:
                                raise Exception("Unsupported library")
                            # logger.debug(f"init_code: {init_code}")
                            exec(init_code,namespace)
                            if self.is_input(eval(tgt,namespace)):
                                inputs.append(tgt)
                                input_init_code += init_code + "\n"
                            elif tgt in class_forward_args:
                                inputs.append(tgt)
                                input_init_code += init_code + "\n"
                        except Exception as e:
                            logger.error(f"Error get input tensor: {e}")
                elif isinstance(value, ast.Constant) or isinstance(value, ast.UnaryOp):
                    # print(ast.unparse(node))
                    class_code += ast.unparse(node) + "\n"

        class_init_args_code = ""
        for arg_name in class_init_required_args:
            class_init_args_code += (
                self.find_name_in_tree(tree, arg_name, use_default=True) + "\n"
            )
        if class_init_code != "":
            class_init_code = class_init_args_code + class_init_code
        else:
            class_init_code = class_init_args_code
            class_init_code += f"\nmodel = {class_name}({', '.join(class_init_required_args)})\n"  # TODO@SHAOYU: if I want to add `.eval()`, is there the right place?
        class_code += "\n" + class_init_code

        if len(inputs) < len(class_forward_args):
            diff = len(class_forward_args) - len(inputs)
            for arg_name in class_forward_required_args:
                if arg_name not in inputs:
                    inputs.append(arg_name)
                    input_init_code += f"{arg_name} = 1\n"
                    diff -= 1
                    if diff == 0:
                        break

        return class_code, inputs, input_init_code

    def preprocessing(self, code: str):
        code = code.replace("\t", "    ")

        new_lines = []
        for line in code.splitlines():
            if line.strip().startswith("assert"):
                continue
            new_lines.append(line)
        code = "\n".join(new_lines)

        tree = ast.parse(code)
        for transformer in self.transformers:
            tree = transformer.visit(tree)
        code = astunparse.unparse(tree)
        code = code.replace("(:", ":").replace(":)", ":")
        return code

    @staticmethod
    def find_name_in_tree(tree, arg_name, use_default=False):
        for _n in tree.body:
            if isinstance(_n, ast.Assign):
                for _t in _n.targets:
                    if isinstance(_t, ast.Name) and _t.id == arg_name:
                        return ast.unparse(_n)
        if arg_name == "batch_size":
            return f"{arg_name} = 1"

        if use_default:
            return f"{arg_name} = 1"
        else:
            return ""


def get_rendered_code(lib: str, code: str) -> str:
    CODE_PARSER = CodeParser(lib_name=f"{lib}")
    code = code.replace(".to('cuda')", "").replace(".cuda()", "")
    render_code, inputs, input_init_code = CODE_PARSER.split_func_tensor(code)
    imports = CODE_PARSER.imports
    if len(inputs) == 0:
        inputs.append("input_tensor")
        input_init_code += CODE_PARSER.input_init_code("input_tensor")
    render_code = imports + "\n" + render_code + "\n" + input_init_code + "\n"
    render_code += f"inputs = [{', '.join(inputs)}]\n\n"
    return render_code
