```python
class Model(torch.nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.linear = torch.nn.Linear(15, 10)
        self.weight_matrix = torch.nn.Parameter(torch.randn(10, 7))
        self.dropout = torch.nn.Dropout(0.5)

    def forward(self, x):
        x = self.linear(x)
        x = torch.matmul(x, self.weight_matrix)
        x = F.relu(x)
        x = self.dropout(x)
        x = torch.sigmoid(x)
        return x

x = torch.randn(32, 15)

model = Model()
```

