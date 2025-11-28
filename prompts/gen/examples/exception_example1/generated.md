```python
class Model(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.mm_layer = torch.nn.Linear(10, 10)

    def forward(self, x1, inp):
        v1 = torch.mm(x1, inp)
        v2 = v1 + inp
        return v2

m = Model()
x1 = torch.randn(2, 2)
inp = torch.randn(2, 10)
```

