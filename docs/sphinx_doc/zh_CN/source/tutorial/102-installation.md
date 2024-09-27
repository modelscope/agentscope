(102-installation-zh)=

# 安装

为了安装AgentScope，您需要安装Python 3.9或更高版本。我们建议专门为AgentScope设置一个新的虚拟环境：

## 创建虚拟环境

### 使用Conda

如果您使用Conda作为环境管理工具，您可以使用以下命令创建一个新的Python 3.9虚拟环境：

```bash
# 使用Python 3.9创建一个名为"agentscope"的新虚拟环境
conda create -n agentscope python=3.9

# 激活虚拟环境
conda activate agentscope
```

### 使用Virtualenv

如果您使用`virtualenv`，您可以首先安装它（如果尚未安装），然后按照以下步骤创建一个新的虚拟环境：

```bash
# 如果尚未安装virtualenv，请先安装它
pip install virtualenv

# 使用Python 3.9创建一个名为"agentscope"的新虚拟环境
virtualenv agentscope --python=python3.9

# 激活虚拟环境
source agentscope/bin/activate  # 在Windows上使用`agentscope\Scripts\activate`
```

## 安装AgentScope

### 从源码安装

按照以下步骤从源代码安装AgentScope，并以可编辑模式安装AgentScope：

**_注意：该项目正在积极开发中，建议从源码安装AgentScope！_**

```bash
# 从GitHub上拉取AgentScope的源代码
git clone https://github.com/modelscope/agentscope.git
cd agentscope

# 针对本地化的multi-agent应用
pip install -e .
```

### 使用Pip安装

如果您选择从Pypi安装AgentScope，可以使用`pip`轻松地完成：

```bash
# 针对本地化的multi-agent应用
pip install agentscope
```

### 额外依赖

AgentScope 支持可选依赖如下，用户可以根据自己的需求选择安装：

- ollama: Ollama API
- litellm: Litellm API
- zhipuai: Zhipuai API
- gemini: Gemini API
- service: 不同工具函数的依赖
- distribute: 分布式模式的依赖
- full: 一次性安装上述所有的依赖，可能耗时较长

可以通过将它们添加到安装命令中来安装这些依赖。

#### Windows

```bash
pip install agentscope[gemini]
# or
pip install agentscope[ollama,distribute]
```

#### Mac & Linux

```bash
pip install agentscope\[gemini\]
# or
pip install agentscope\[ollama,distribute\]
```

[[返回顶端]](#102-installation-zh)
