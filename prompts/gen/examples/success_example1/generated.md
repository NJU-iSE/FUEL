```python
class Model(nn.Module):
    def __init__(self):
        super(Model, self).__init__()
        self.fc1 = nn.Linear(in_features=28 * 28, out_features=128)
        self.fc2 = nn.Linear(in_features=128 // 4, out_features=10)  # Adjusted for pooling

    def forward(self, x):
        # Flatten the input if necessary
        x = x.view(x.size(0), -1)
        out = self.fc1(x)
        out = F.relu(out)
        # Reshape for max_pool2d
        out = out.view(out.size(0), 1, 16, 8)
        out = F.max_pool2d(out, kernel_size=2, stride=2)
        # Flatten again before fc2
        out = out.view(out.size(0), -1)
        out = self.fc2(out)
        return F.log_softmax(out, dim=-1)

m = Model()
x = torch.randn(1, 1, 28, 28)
```

