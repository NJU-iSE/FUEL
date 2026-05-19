# Prompt: Generate Triton Code After Successful Execution

## Context

The previous Triton test executed successfully in both interpreter and JIT modes. Based on the coverage feedback and analysis, generate a new kernel to explore different Triton code paths.

{{examples}}

---

## Current Test Case

```python
{{code}}
```

{{als_res}}

## Suggested APIs to Use

{{new_ops}}

## Recent Triton Kernels

{{recent_kernels}}

## Diversity Rules

{{diversity_rules}}

## Task

Generate a new complete Triton test case with `triton_impl(*inputs)` and `inputs`.
Prefer a single kernel test case.
Use the coverage feedback to explore a different code path than the recent kernels, not just a small mutation of the previous test.
Vary at least two structural dimensions relative to the current test, such as kernel family, dimensionality, reduction axis, mask pattern, dtype mix, arithmetic composition, or input stride pattern.

**Constraint**: Use at most {{op_nums}} major Triton operations inside the kernel body.

## Output

```python
# Your generated Triton code here
```
