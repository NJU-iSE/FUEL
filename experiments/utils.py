import json
import os
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import torch
import matplotlib

# print(plt.style.available)
# plt.style.use("seaborn-v0_8-white")

# matplotlib.rcParams["font.family"] = "Times New Roman"
# matplotlib.rcParams["mathtext.fontset"] = "stix"


def list_all_files(folder_path):
    file_list = []
    for file in Path(folder_path).rglob("*.py"):
        if file.is_file():
            file_list.append(str(file))
    return file_list


def get_all_pyfiles(folder_path: str) -> List[str]:
    file_list = []
    for file in Path(folder_path).rglob("*.py"):
        if file.is_file():
            file_list.append(str(file))
    return sorted(file_list)


def read_pyfile(filename: str) -> str:
    py_code: str
    with open(filename) as f:
        py_code = f.read()
    return py_code


def write_pyfile(filename: str, py_code: str) -> None:
    with open(filename, "w") as f:
        f.write(py_code)


def remove_pyfile(filename: str) -> None:
    if os.path.isfile(filename):
        os.remove(filename)


def merge_json(filename_list: List[str], save_path: str):
    merge_data = {}
    for filename in filename_list:
        with open(filename, "r") as f:
            data = json.load(f)
        merge_data = {**merge_data, **data}
    json.dump(merge_data, open(save_path, "w"))


class Draw:
    def __init__(self):
        self.colors = ("red", "blue", "green", "cyan", "yellow", "magenta")
        self.linestyles = ("-.", "--", "-.", ":")
        self.markers = ("d", "^", "*", "v", "^", "o", "s", "<", ">")

    @staticmethod
    def set_layout(figsize=(16, 9), fontsize=18):
        plt.figure(figsize=figsize)
        plt.rcParams["font.size"] = fontsize

    @staticmethod
    def set_label(title="Title", x_label="x", y_label="y"):
        plt.title(title)
        plt.xlabel(x_label)
        plt.ylabel(y_label)

    @staticmethod
    def set_legend(
        loc="best",
        title=None,
        fontsize="medium",
        frameon=True,
        franealpha=0.8,
        edgecolor="black",
    ):
        plt.legend(
            title=title,
            loc=loc,
            fontsize=fontsize,
            frameon=frameon,
            framealpha=franealpha,
            edgecolor=edgecolor,
        )

    @staticmethod
    def show(save_path=None):
        if save_path is not None:
            plt.savefig(save_path)
        plt.show()


class DrawPlot(Draw):
    def __init__(self, data, title="PyTorch"):
        super().__init__()
        self.data = data
        self.fig, self.axs = plt.subplots(1, 1, sharex=True)
        self.fig.text(0.44, 0.93, title, va="center", fontsize=18, family="serif")
        self.fig.text(0.5, 0.02, "Iteration", ha="center", fontsize=16, family="serif")
        self.fig.text(
            0.01,
            0.5,
            "Line Coverage",
            va="center",
            rotation="vertical",
            fontsize=16,
            family="serif",
        )
        self.style_kw = {
            "ls": "--",  # line style
            "lw": 1,  # line width
            "marker": "v",  # marker symbol
            "ms": 10,  # marker size
            "color": "blue",  # line color
            "markeredgecolor": "#FF5733",
            "markeredgewidth": 1,
        }

    def draw_plot(self):
        for i, (label, y) in enumerate(self.data.items()):
            ax = self.axs
            self.style_kw["markeredgecolor"] = self.colors[i % len(self.colors)]
            self.style_kw["color"] = self.colors[i % len(self.colors)]
            self.style_kw["marker"] = self.markers[i % len(self.markers)]
            y = y[: min(len(y), 1000) : 15]
            x = [j * 15 for j in range(1, len(y) + 1)]
            # x, y = x[: min(len(x), 1000)][::10], y[: min(len(x), 1000)]
            if i == 2:
                self.style_kw["ms"] = "12"
            lst0 = [0, 90 // 15, 300 // 15, 500 // 15, 750 // 15, 999 // 15]
            lst1 = [0, 90 // 15, 300 // 15, 500 // 15, 750 // 15, 999 // 15]
            lst2 = [0, 90 // 15, 300 // 15, 500 // 15, 750 // 15, 999 // 15]
            if i == 0:
                lst = lst0
            elif i == 1:
                lst = lst1
            else:
                lst = lst2
            ax.plot(x, y, label=label, **self.style_kw, markevery=lst, clip_on=False)

        self.fig.legend(
            # bbox_to_anchor=(0.42, 0.88),
            bbox_to_anchor=(0.90, 0.35),
            ncol=1,
            prop={
                "family": "Serif",
                "size": 14,
                "weight": "light",
            },
        )


def draw_from_json(filename: str, lib: str):
    with open(filename, "r") as f:
        data = json.load(f)
    plot = DrawPlot(data, title=lib)
    plot.draw_plot()
    # plt.grid(axis="x")
    plt.grid(axis="y")
    plt.savefig(f"{lib}_1000.png", dpi=1200)
    plot.show()


class ExtractFromFile:
    @staticmethod
    def extract_coverage_data(file_path):
        """extract coverage data from fuel output log file"""
        coverage_data = []
        
        with open(file_path, "r") as f:
            lines = f.readlines()
        
        for line in lines:
            if "Total coverage rate is" in line:
                # Extract percentage value
                percentage_str = line.split("Total coverage rate is")[1].split("%")[0].strip()
                percentage = float(percentage_str)
                coverage_data.append(percentage)
        
        return coverage_data


if __name__ == "__main__":
    # filename_list = [
    #     "fuel_pytorch_coverage.json",
    #     "titanfuzz_pytorch_coverage.json",
    #     "whitefox_pytorch_coverage.json",
    # ]
    # filename_list = [
    #     "fuel_tensorflow_coverage.json",
    #     "titanfuzz_tensorflow_coverage.json",
    #     "whitefox_tensorflow_coverage.json",
    # ]
    # merge_json(filename_list, "merge_tensorflow.json")
    # draw_from_json("merge_torch.json")
    draw_from_json("merge_torch.json", "PyTorch")
