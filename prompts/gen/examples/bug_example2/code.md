```python
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.pool = nn.FractionalMaxPool2d(kernel_size=(1, 1), output_ratio=(0.5, 0.5))

    def forward(self, x):
        torch.manual_seed(0)
        x = self.pool(x)
        return x

model = Model().eval()
x = torch.randn(1, 1, 10, 10)
inputs = [x]
```

