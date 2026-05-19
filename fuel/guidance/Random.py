import random
from typing import List


class Random:
    def __init__(self, left, right, filename):
        with open(filename, "r") as f:
            lines = f.readlines()
        self.left, self.right = left, right
        self.ops = [line.strip() for line in lines]
        self.is_triton = any(
            op.startswith("tl.") or op.startswith("triton.") for op in self.ops
        )

    def get_ops(self) -> List[str]:
        if self.is_triton:
            length = random.randint(max(2, self.left), max(4, self.right))
        else:
            length = random.randint(self.left, self.right)
        return list(random.sample(self.ops, length))


if __name__ == "__main__":
    heuristic = Random(1, 3, "data/pytorch_operators.txt")
    print(heuristic.get_ops())
