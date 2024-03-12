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
# For distributed multi-agent applications
pip install agentscope[distribute]  # On Mac use `pip install agentscope\[distribute\]`
```

### Install from Source

For users who prefer to install AgentScope directly from the source code, follow these steps to clone the repository and install the platform in editable mode:

**_Note: This project is under active development, it's recommended to install AgentScope from source._**

```bash
# Pull the source code from Github
git clone https://github.com/modelscope/agentscope.git
cd AgentScope

# For centralized multi-agent applications
pip install -e .
# For distributed multi-agent applications
pip install -e .[distribute]  # On Mac use `pip install -e .\[distribute\]`
```

**Note**: The `[distribute]` option installs additional dependencies required for distributed applications. Remember to activate your virtual environment before running these commands.

[[Return to the top]](#102-installation-en)
