(102-installation-en)=

# Installation

To install AgentScope, you need to have Python 3.9 or higher installed. We recommend setting up a new virtual environment specifically for AgentScope:

## Create a Virtual Environment

### Using Conda

If you're using Conda as your package and environment management tool, you can create a new virtual environment with Python 3.9 using the following commands:

```bash
# Create a new virtual environment named 'agentscope' with Python 3.9
conda create -n agentscope python=3.9

# Activate the virtual environment
conda activate agentscope
```

### Using Virtualenv

Alternatively, if you prefer `virtualenv`, you can install it first (if it's not already installed) and then create a new virtual environment as shown:

```bash
# Install virtualenv if it is not already installed
pip install virtualenv

# Create a new virtual environment named 'agentscope' with Python 3.9
virtualenv agentscope --python=python3.9

# Activate the virtual environment
source agentscope/bin/activate  # On Windows use `agentscope\Scripts\activate`
```

## Installing AgentScope

### Install with Pip

If you prefer to install AgentScope from Pypi, you can do so easily using `pip`:

```bash
# For centralized multi-agent applications
pip install agentscope
```

### Install from Source

For users who prefer to install AgentScope directly from the source code, follow these steps to clone the repository and install the platform in editable mode:

**_Note: This project is under active development, it's recommended to install AgentScope from source._**

```bash
# Pull the source code from Github
git clone https://github.com/modelscope/agentscope.git
cd agentscope

# For centralized multi-agent applications
pip install -e .
```

### Extra Dependencies

The supported optional dependencies for AgentScope are list as follows:

- ollama: Ollama API
- litellm: Litellm API
- zhipuai: Zhipuai API
- gemini: Gemini API
- service: The dependencies for different service functions
- distribute: The dependencies for distribution mode
- full: All the dependencies

You can install one or more of these dependencies by adding them to the installation command.

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

[[Return to the top]](#102-installation-en)
