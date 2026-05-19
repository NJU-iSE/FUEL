# Prompt: Generate Triton Code After Oracle Violation

## Context

The previous Triton test produced different behavior between `TRITON_INTERPRET=1` interpreter mode and normal JIT mode.

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

Generate a new Triton test case that stresses related operations, masks, block sizes, boundary conditions, or dtype conversions.
The code must define `triton_impl(*inputs)` and `inputs`.
Prefer a single kernel test case.
Stay in the neighborhood of the suspicious behavior, but do not regenerate the same kernel skeleton. Change the composition pattern enough that it exercises a nearby but distinct path.

## Output

```python
# Your generated Triton code here
```
