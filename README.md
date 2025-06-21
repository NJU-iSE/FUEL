<div align='center'>
  <img src=assets/FUEL-logo.png width=250px >
</div>
<div align='center'>
  <a href="https://arxiv.org"><img src="https://img.shields.io/badge/arXiv-xxxxx-b31b1b?style=for-the-badge"></a>
  <a href="https://docs.google.com/spreadsheets/d/1qVoSdLj_SvfDHrtKMFkR6xVsCj99ABE8Rm9SgljcdGY/edit?gid=959752128#gid=959752128"><img src=https://img.shields.io/badge/Bug_List-Google_Table-green?style=for-the-badge></a>
  <a href="./LICENSE"><img src=https://img.shields.io/badge/License-Apache_2.0-turquoise?style=for-the-badge ></a>
 </div>

# May the Feedback Be with You! Unlocking the Power of Feedback-Driven Deep Learning Framework Fuzzing via LLMs

## 📋 Introduction

**FUEL** (FeedBack-driven deep learning framework fUzzing via LLMs) is an advanced deep learning framework fuzzing tool designed to detect vulnerabilities and inconsistencies in mainstream deep learning frameworks such as PyTorch and TensorFlow. FUEL combines the intelligent generation capabilities of Large Language Models (LLMs) with feedback-driven heuristic search algorithms to efficiently generate high-quality test cases and discover potential issues in deep learning frameworks.

## 🎯 Why FUEL?

### 🔥 Core Advantages

- **🤖 Intelligent Code Generation**: Leverages Large Language Models to generate complex and effective deep learning model test cases
- **🔄 Feedback-Driven**: Smart feedback mechanism based on execution results and code coverage to continuously optimize test generation strategies
- **📊 Heuristic Search**: Integrates heuristic algorithms like Simulated Annealing (SA) for intelligent API operator selection
- **🔍 Differential Testing**: Supports multiple differential testing modes (hardware differences, compiler differences, etc.)
- **📈 Efficient Detection**: Successfully discovered 104 new bugs, with 93 confirmed and 47 fixed

### 🛠️ Key Features

- ✅ Support for PyTorch and TensorFlow framework testing
- ✅ Multiple differential testing modes (CPU/CUDA hardware differences, compiler differences)
- ✅ Intelligent operator selection and combination
- ✅ Real-time code coverage feedback
- ✅ Exception detection and bug report generation
- ✅ Configurable LLM backends (local models/API services)

## 🏗️ Project Structure

```
FUEL/
├── 📁 config/           # Configuration files
│   ├── als_prompt/      # Analysis prompt configurations
│   ├── gen_prompt/      # Generation prompt configurations
│   ├── heuristic.yaml   # Heuristic algorithm configuration
│   └── model.yaml       # LLM model configuration
├── 📁 data/             # Data files
│   ├── pytorch_apis.txt # PyTorch API list
│   └── tensorflow_apis.txt # TensorFlow API list
├── 📁 fuel/             # Core source code
│   ├── difftesting/     # Differential testing module
│   ├── exec/            # Code execution module
│   ├── feedback/        # Feedback mechanism module
│   ├── guidance/        # Heuristic search module
│   └── utils/           # Utility classes
├── 📁 experiments/      # Experiment and evaluation scripts
└── 📁 results/          # Test result outputs
```

## ⚙️ Experiment Setup

### 💻 Hardware environment

> [!IMPORTANT]
> 
> **General test-bed requirements**
> - **OS**: Ubuntu >= 20.04;
> - **CPU**: X86/X64 CPU;
> - **GPU**: CUDA architecture (V100, A6000, A100, etc.);
> - **Memory**: 128GB GPU Memory available (if you use 72B local model with vLLM);
> - **Storage**: at least 100GB Storage available;
> - **Network**: Good Network to GitHub and LLM API service;

### 📦 Software requirement
You need a DeepSeek API key to invoke the DeepSeek API service (of course you can modify configuration in [./config/model.yaml](./config/model.yaml))

## 🚀 Quick Start

#### 📥 clone the repository
```bash
git clone https://github.com/NJU-iSE/FUEL.git
cd FUEL
```

#### 🔧 Install dependencies

Firstly, we should install some necessary python dependencies.
We strongly recommend users use `conda` to manage the python environments.
Please follow the below commands.

```shell
conda create -n fuel python=3.12
conda activate fuel
pip install -r requirements.txt
```

#### ⚡ Install PyTorch nightly version
When fuzzing the systems under tests (SUTs), we use the nightly version, in order to detect new bugs.

Here we use CUDA 12.6 as an example. Please install the nightly version based on your CUDA version. You can get the corresponding commands from https://pytorch.org/
```shell
pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu126
```

#### 🔑 create API key
In our experiment, we use DeepSeek API to invoke the LLM service. DeepSeek API service is compatible with openai interfaces.

For the below command, you should replace `[YOUR_API_KEY]` with your own DeepSeek API key.
```shell
key="[YOUR_API_KEY]"
echo "$key" > ./config/llm-key.txt
```

#### 🏃 Start fuzzing
> [!WARNING]
> The fuzzing process is time-consuming and may run for many hours to discover meaningful bugs.

```shell
python -m fuel.fuzz --lib pytorch run_fuzz \
                    --max_round 1000 \
                    --heuristic SA \
                    --diff_type cpu_compiler
```

**🎛️ Parameter Description:**
- `--lib`: Target deep learning library (`pytorch` or `tensorflow`)
- `--max_round`: Maximum number of testing rounds
- `--heuristic`: Heuristic algorithm (`SA`, `Random`, or `None`)
- `--diff_type`: Differential testing type (`hardware`, `cpu_compiler`, `cuda_compiler`)

Note that the fuzzing experiment is really time-consuming. Maybe you should check the results after about ~20hours.

#### 📊 Check results
Please check the generated models in [results/fuel/pytorch](results/fuel/pytorch).
If you want to get the detected bugs, please check [outputs/bug_reports.txt](outputs/bug_reports.txt).

### 🔧 Advanced Usage
> [!WARNING]
> These advanced features are not fully tested and are prone to instability. We will continue improving our artifact. 

#### 🎮 Using Local LLM Models
```shell
python -m fuel.fuzz --lib pytorch run_fuzz \
                    --use_local_gen \
                    --max_round 1000 \
                    --heuristic SA
```

#### 🎯 Custom Operator Selection
```shell
python -m fuel.fuzz --lib pytorch run_fuzz \
                    --op_set data/custom_operators.txt \
                    --op_nums 8 \
                    --max_round 1000
```

#### 📈 Code Coverage Analysis
```shell
bash coverage.sh
```

## 🚨 Bug finding (Real-world Contribution)

So far, FUEL has detected **104** previously unknown new bugs, with **93** already confirmed and **47** already fixed. **14** detected bugs were labeled as *high-priority*, and **one** was labeled as 🤯*utmost priority*. **5** detected bugs has been assigned with 🐞*CVE IDs*. The evidence can be viwed in [Google Table](https://docs.google.com/spreadsheets/d/1qVoSdLj_SvfDHrtKMFkR6xVsCj99ABE8Rm9SgljcdGY/edit?gid=959752128#gid=959752128).

## 🙏 Acknowledgement
We thank [NNSmith](https://github.com/ise-uiuc/nnsmith), [TitanFuzz](https://github.com/ise-uiuc/TitanFuzz), and [WhiteFox](https://github.com/ise-uiuc/WhiteFox) for their admirable open-source spirit, which has largely inspired this project.

