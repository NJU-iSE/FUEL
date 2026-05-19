```python
@triton.jit
def elementwise_exp_mask_kernel(x_ptr, out_ptr, n_elements, BLOCK: tl.constexpr):
    pid = tl.program_id(0)
    offsets = pid * BLOCK + tl.arange(0, BLOCK)
    mask = offsets < n_elements
    x = tl.load(x_ptr + offsets, mask=mask, other=0.0)
    y = tl.where(x > 0.0, tl.exp(x), x)
    tl.store(out_ptr + offsets, y, mask=mask)


def triton_impl(x):
    out = torch.empty_like(x)
    n_elements = x.numel()
    block = 64
    grid = (triton.cdiv(n_elements, block),)
    elementwise_exp_mask_kernel[grid](x, out, n_elements, BLOCK=block)
    return out


inputs = [
    torch.linspace(-2.0, 2.0, 129, device="cuda", dtype=torch.float32),
]
```
