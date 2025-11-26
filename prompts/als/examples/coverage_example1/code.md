```python
class Model(nn.Module):
    def __init__(self, input_size, hidden_size, num_classes):
        super(Model, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.relu = nn.ReLU()
        self.fc2 = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        out = self.fc1(x)
        out = self.relu(out)
        out = self.fc2(out)
        return F.log_softmax(out, dim=-1)

input_size = 28 * 28
hidden_size = 128
num_classes = 10
m = Model(input_size, hidden_size, num_classes)
x = torch.randn(1, input_size)
```

