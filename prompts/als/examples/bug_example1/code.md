```python
class Model(torch.nn.Module):
    def forward(self, x):
        x = x * 2
        x = torch.nn.functional.dropout(x, p=0.5)
        x = torch.relu(x)
        return x

func = Model()
inputs = torch.tensor([[1, 2, 3], [4, 5, 6]])
```

