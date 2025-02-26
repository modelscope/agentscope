# AgentScope Documentation

## Build Documentation

Please use the following commands to build sphinx doc of AgentScope.

> Note: Building AgentScope tutorial requires `DASHSCOPE_API_KEY` in your environment variables.

```shell
# step 1: Install dependencies
pip install sphinx sphinx_rtd_theme sphinx-gallery sphinx-autobuild myst-parser sphinxcontrib-mermaid

# step 2: go into the sphinx_doc dir
cd en # or `cd zh` for Chinese version

# step 3: build the sphinx doc
./build.sh

# step 4: view tutorial/en/build/html/index.html using your browser
```
