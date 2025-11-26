```python
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = nn.Conv2d(in_channels=3, out_channels=16, kernel_size=3, stride=1, padding=1)
        self.gn1 = nn.GroupNorm(num_groups=4, num_channels=16)
        self.conv2 = nn.ConvTranspose2d(in_channels=16, out_channels=8, kernel_size=2, stride=2, padding=0)
        self.gn2 = nn.GroupNorm(num_groups=2, num_channels=8)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.conv1(x)
        x = self.gn1(x)
        x = self.relu(x)
        x = self.conv2(x)
        x = self.gn2(x)
        x = self.relu(x)
        return x

m = Model()
x = torch.randn(1, 3, 256, 256)
```

