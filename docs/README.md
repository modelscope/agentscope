# AgentScope Documentation

## Build Documentation

Please use the following commands to build sphinx doc of AgentScope.

```shell
# step 1: Install dependencies
pip install sphinx sphinx-autobuild sphinx_rtd_theme myst-parser sphinxcontrib-mermaid

# step 2: go into the sphinx_doc dir
cd sphinx_doc

# step 3: build the sphinx doc
make clean all

# step 4: view sphinx_doc/build/html/index.html using your browser
```

## Update Documentation (for developer)

### Add doc for new packages

```
src
└── agentscope
    ├── ...
    └── new_package
        ├── __init__.py
        └── new_module.py
```

If a new package (`agentscope/new_package`) is added , please add the corresponding documents as follows:

1. use the following script to generate template script (`sphinx_doc/{language}/source/agentscope.new_package.rst`) of new packages.

```shell
cd sphinx_doc
sphinx-apidoc -o {language}/source ../../src/agentscope
```

2. edit `sphinx_doc/{language}/source/agentscope.new_package.rst`, modify the content of the generated template script. For example, modify

```
agentscope.new\_package package
===============================

Submodules
----------

agentscope.new\_package.new\_module module
-------------------------------------------
...

Module contents
---------------
...
```

to

```
NewPackage package
==================

new\_module module
------------------
...
```

3. modify the `sphinx_doc/{language}/source/index.rst`, add the new package into the table of contents.

```
.. toctree::
   :maxdepth: 2
   :hidden:
   :glob:
   :caption: AgentScope API Reference

   agentscope.agents
   ...
   agentscope.new_package
   agentscope
```

4. rebuild the sphinx doc of AgentScope

```
make clean all
```

### Add doc for new modules

```
src
└── agentscope
    ├── ...
    └── existing_package
        ├── __init__.py
        ├── existing_module.py
        ├── ...
        └── new_module.py
```

If a new module (agentscope/existing_package/new_module.py) is added , please add the corresponding documents as follows:

1. edit `sphinx_doc/{language}/source/agentscope.existing_package.rst` and add the following content.

```
new\_module module
------------------

.. automodule:: agentscope.existing_package.new_module
   :members:
   :undoc-members:
   :show-inheritance:
```

2. rebuild the sphinx doc of AgentScope

```
make clean all
```
