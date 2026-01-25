---
title: Ubuntu 24.04 强行部署 Detectron2 v0.3 全纪录
author: eelops
date: 2026-01-24 11:00:00 +0800
categories: [环境配置, 兼容问题]
tags: [环境配置]
---

## 1. 项目背景与核心冲突

*   **项目目标**：复现 CED-FOOD (基于 Detectron2 v0.3)。
    1. 项目论文链接：[Boosting Few-Shot Open-Set Object Detection via Prompt Learning and Robust Decision Boundary](https://arxiv.org/pdf/2406.18443)
    2. 项目代码仓库：[CED-FOOD](https://github.com/zjzwzw/CED-FOOD)
*   **依赖环境**：Python 3.8 + PyTorch 1.7.1 (2020年时代的配置)。
*   **当前系统**：Ubuntu 24.04 LTS (2024年发布，系统库极新)。
*   **硬件情况**：**集成显卡 (Integrated Graphics)**，无 NVIDIA 独立显卡。
*   **核心矛盾**：
    1.  **硬件限制**：集显不支持 CUDA，必须强制将代码“阉割”为 CPU 模式运行。
    2.  **软件代差**：2024年的操作系统（Ubuntu 24.04）与2020年的代码库（PyTorch 1.7）存在巨大的编译器和链接库冲突。


---

## 2. 报错取证与深度分析

在搭建过程中，我们主要解决了以下三个“拦路虎”：

### 错误一：构建隔离失效 (Python 层)
*   **现象**：`ModuleNotFoundError: No module named 'torch'`
*   **原因**：Pip 默认会在一个空的“隔离环境”中编译 Detectron2，但 Detectron2 的安装脚本必须依赖 PyTorch。
*   **对策**：使用 `--no-build-isolation` 强行在当前有 PyTorch 的环境中编译。

 Pip 为保证下载纯净环境，他会创建一个临时的虚拟环境。除了 Python 核心，什么都没有。如果没有文件`pyproject.toml`就会报错 `ModuleNotFoundError: No module named 'xxx'`

### 错误二：系统头文件缺失 (系统兼容层)
*   **现象**：`fatal error: crypt.h: No such file or directory`
*   **原因**：Ubuntu 24.04 废弃了旧版 `libcrypt`，导致 Python 3.8 找不到头文件。
*   **对策**：补装 `libxcrypt` 并手动注入 `CPATH`。

### 错误三：编译器代差 (最致命)
*   **现象**：`/libm.so.6: unknown type [0x13] section .relr.dyn`
*   **原因**：旧版 GCC (Conda 默认给的 7/8 版本) 看不懂 Ubuntu 24.04 新版系统库的压缩格式。
*   **对策**：打破常规，**升级编译器至 GCC 11**，让编译器能读懂新系统。

---

## 3. 硬件策略分析：集显现状与独显预案

### A. 当前策略：集显 (Integrated Graphics)
*   **现状判定**：Intel/AMD 的集成显卡**不支持** NVIDIA 的 CUDA 技术。
*   **操作要点**：
    1.  **安装时**：必须指定 `cpuonly` 包，防止 PyTorch 尝试加载 CUDA 驱动。
    2.  **编译时**：必须设置 `FORCE_CUDA=0`，明确告诉 Detectron2 编译脚本“不要去寻找显卡”，否则它可能会因为找不到 NVCC 编译器而报错退出。
    3.  **运行时**：所有推理代码需确保运行在 `device='cpu'` 上，速度会慢，但能跑通逻辑。

### B. 知识储备：如果未来换了 N 卡 (如 GTX/RTX)，该怎么办？

如果这台机器插上了一张 NVIDIA 显卡（如 GTX 1080），可能会遇到如下问题：
1.  **驱动冲突**：PyTorch 1.7 需要 CUDA 10.1。
2.  **系统不支持**：Ubuntu 24.04 原生不支持安装 CUDA 10.1（太老了，GCC 版本不匹配）。

**解决实际问题的方案：**
*   **方案：Docker 容器化**。拉取 `nvidia/cuda:10.1-cudnn7-devel-ubuntu18.04` 的镜像。在容器里，你可以拥有旧版的 Ubuntu 18.04 环境，完美兼容 PyTorch 1.7，同时利用宿主机的显卡驱动。

---

## 4. 最终实战操作流程

### 第一阶段：环境初始化与编译器修复

```bash
# 1. 创建环境
conda create -n CED-FOOD python=3.8 -y
conda activate CED-FOOD

# 2. 安装 PyTorch (CPU版，这是集显运行的基础)
# 重点：指定 cpuonly，版本锁定 1.7.1
conda install pytorch==1.7.1 torchvision==0.8.2 torchaudio==0.7.2 cpuonly -c pytorch -y

# 3. 修复系统兼容性 (安装 crypt 库)
conda install -c conda-forge libxcrypt ninja -y

# 4. 升级编译器 (解决 unknown type section .relr.dyn 报错)
# 先移除不兼容的旧版工具
conda remove gxx_linux-64 gcc_linux-64 binutils -y
# 安装兼容 Ubuntu 24.04 的 GCC 11
conda install -c conda-forge gxx_linux-64=11 gcc_linux-64=11 sysroot_linux-64 binutils -y
```



### 第二阶段：注入变量与核心编译
#### 1. 设置环境变量
```bash

# 关键：FORCE_CUDA=0 告诉 Detectron2 "我是集显，别找显卡"
export FORCE_CUDA=0
# 指定刚才装好的 GCC 11
export CC=x86_64-conda-linux-gnu-gcc
export CXX=x86_64-conda-linux-gnu-g++
# 解决 crypt.h 找不到的问题
export CPATH=$CONDA_PREFIX/include:$CPATH
```

> `$`:类似于解地址符号，他负责将对应路径的“东西”拿出来
> ':':分隔符;

所以设置环境变量当中的`CPATH=$CONDA_PREFIX/include:$CPATH`翻译成人话就是：先去我这个新环境里找头文件，找不到再去原来的地方找。

#### 2. 编译 Detectron2
```bash
cd detectron2-0.3
rm -rf build/ detectron2.egg-info/  # 确保清理干净
# 关键：--no-build-isolation 借用当前的 PyTorch 环境进行编译
python -m pip install -e . --no-build-isolation
```



### 第三阶段：依赖补全 (Requirements.txt)

最后安装剩余的工具包，这些包相对独立，安装风险较低。

```bash
pip install -r requirements.txt
```

---

## 5. 最终环境验证

在终端输入 `python`，运行以下代码确认“存活”：

```python
import torch
import detectron2
from detectron2.utils.env import print_env

print("\n=== 环境自检报告 ===")
# 1. 验证 PyTorch 版本
print(f"PyTorch 版本: {torch.__version__} (预期: 1.7.1)")
# 2. 验证硬件模式
cuda_status = torch.cuda.is_available()
print(f"CUDA 是否可用: {cuda_status} (预期: False, 因为是集显)")
# 3. 验证 Detectron2 编译情况
print(f"Detectron2 导入成功: 是")
print("====================")

if not cuda_status:
    print("提示：当前运行在 CPU 模式。推理速度会较慢，但功能完整。")
```

---

## 6. 避坑总结

1.  **集显认命，切勿强求**：在没有 N 卡的机器上，必须设置 `FORCE_CUDA=0`，否则编译脚本会因为试图调用 CUDA 编译器而报错，导致前功尽弃。
2.  **新瓶装旧酒，全靠 GCC 11**：在 Ubuntu 24.04 上跑旧代码，Conda 默认的 GCC 7/8 是完全不可用的。手动指定 GCC 11 是打通新旧系统的唯一桥梁。
3.  **构建隔离是关键**：对于像 Detectron2 这种“先有鸡还是先有蛋”（编译依赖 PyTorch）的库，`--no-build-isolation` 参数是必选的。


