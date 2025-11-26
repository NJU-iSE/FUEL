```python
class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(10, 10)

    def forward(self, x):
        v1 = self.linear(x)
        v2 = v1 - 9.32925237729762
        v3 = F.relu(v2)
        return v3

m = Model()
x = torch.randn(1, 10)
```

