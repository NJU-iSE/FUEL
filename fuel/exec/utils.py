from __future__ import annotations

import copy
from math import inf
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    import tensorflow
    import torch


# Convert various attributes to CUDA
def to_cuda(model: torch.nn.Module, inputs: list[torch.Tensor]):
    import torch

    torch.manual_seed(0)
    model_cuda = copy.deepcopy(model)
    model_cuda.to("cuda")
    for attr in dir(model_cuda):
        if isinstance(getattr(model_cuda, attr), torch.Tensor):
            setattr(model_cuda, attr, getattr(model_cuda, attr).to("cuda"))

    new_inputs = []
    to_kwargs = {"device": "cuda"}
    for x in inputs:
        if not isinstance(x, torch.Tensor):
            new_inputs += [x]
            continue
        new_inputs.append(x.clone().to(**to_kwargs))

    return model_cuda, new_inputs


# Convert various attributes to MPS
def to_mps(model: torch.nn.Module, inputs: list[torch.Tensor]):
    import torch

    torch.manual_seed(0)
    model_mps = copy.deepcopy(model)
    model_mps.to("mps")
    for attr in dir(model_mps):
        if isinstance(getattr(model_mps, attr), torch.Tensor):
            setattr(model_mps, attr, getattr(model_mps, attr).to("mps"))

    new_inputs = []
    to_kwargs = {"device": "mps"}
    for x in inputs:
        if not isinstance(x, torch.Tensor):
            new_inputs += [x]
            continue
        new_inputs.append(x.clone().to(**to_kwargs))

    return model_mps, new_inputs


def is_equal_tensor(
    lib,
    x: Union[torch.Tensor, tensorflow.constant],
    y: Union[torch.Tensor, tensorflow.constant],
    atol=1e-4,
    rtol=1e-4,
):
    if lib == "pytorch":
        import torch

        if x.shape != y.shape:  # shape must match
            return False, inf

        if (
            x.numel() == 0 or y.numel() == 0
        ):  # if x and y are both empty tensor FIXME@SHAOYU: In the comment, we use `both` but why we use `or` in code?
            return True, 0

        try:
            x = x.cpu()
            y = y.cpu()
            return (
                torch.allclose(x, y, atol=atol, rtol=rtol, equal_nan=True),
                torch.max(torch.abs(x - y)).item(),
            )
        except Exception:
            return False, inf

    elif lib == "tensorflow":
        import tensorflow as tf

        if x.shape != y.shape:
            return False, inf

        value = tf.experimental.numpy.allclose(
            x, y, atol=atol, rtol=rtol, equal_nan=True
        )
        try:
            return tf.get_static_value(value), tf.get_static_value(
                tf.reduce_max(tf.abs(tf.subtract(x, y)))
            )
        except Exception:
            return False, inf
    return None


def inductor_numerical_verification(
    eager_output: torch.Tensor, inductor_output: torch.Tensor, fp64: torch.Tensor
):
    import torch

    if eager_output.shape != inductor_output.shape:  # shape must match
        return False, inf

    if eager_output.numel() == 0 and inductor_output.numel() == 0 and fp64.numel() == 0:
        return True, 0

    if eager_output.numel() == 0 or inductor_output.numel() == 0 or fp64.numel() == 0:
        return (
            True,
            0,
        )  # TODO@SHAOYU: Add the judgement on one of the output tensors is empty

    try:
        return (
            torch._dynamo.utils.same(eager_output, inductor_output, fp64),
            torch.max(torch.abs(eager_output - inductor_output)).item(),
        )
    except Exception:
        return False, inf
