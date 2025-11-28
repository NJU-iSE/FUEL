```python
class Model(nn.Module):
    def __init__(self):
        super().__init__()
        self.pool = nn.FractionalMaxPool3d(kernel_size=(1, 1, 1), output_ratio=(0.5, 0.5, 0.5))
        self.norm = nn.InstanceNorm2d(1)  # InstanceNorm2d for 2D input
        self.activation = nn.Sigmoid()   # Sigmoid activation

    def forward(self, x):
        torch.manual_seed(0)
        x = self.pool(x)  # Apply FractionalMaxPool3d
        x = x.squeeze(-1)  # Remove the last dimension to make it compatible with InstanceNorm2d
        x = self.norm(x)   # Apply InstanceNorm2d
        x = self.activation(x)
        return x

model = Model().eval()
x = torch.randn(1, 1, 10, 10, 10)
inputs = [x]
```

