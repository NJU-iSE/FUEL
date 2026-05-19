# Prompt: Generate Initial Triton Code

## Context

Generate a valid and diverse Triton kernel using the suggested APIs.

{{examples}}

---

## Suggested APIs to Use

{{new_ops}}

## Recent Triton Kernels

{{recent_kernels}}

## Diversity Rules

{{diversity_rules}}

## Task

Generate a complete Triton test case. The code must define `triton_impl(*inputs)` and `inputs`.
Prefer a single kernel test case.

Prefer simple, checkable kernels such as elementwise arithmetic, masked loads/stores, reductions, softmax-like row reductions, or small matrix operations.
The new test must not be a near-duplicate of the recent kernels. Choose a kernel family or composition pattern that is materially different.
For this initial generation, explicitly vary at least two of: reduction style, tile dimensionality, mask shape, dtype mix, input layout, scalar broadcasting, arithmetic composition, or boundary handling strategy.

**Constraint**: Use at most {{op_nums}} major Triton operations inside the kernel body.

## Output

```python
# Your generated Triton code here
```
