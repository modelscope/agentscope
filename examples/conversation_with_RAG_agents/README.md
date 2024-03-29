# AgentScope Consultants: a Multi-Agent RAG Application

* **What is this example about?**
With the provided implementation and configuration,
you will obtain three different agents who can help you answer different questions about AgentScope.

* **What is this example for?** By this example, we want to show how the agent with retrieval augmented generation (RAG)
capability can be used to build easily.

## Prerequisites
* **Cloning repo:** This example requires cloning the whole AgentScope repo to local.
* **Packages:** This example is built on the LlamaIndex package. Thus, some packages need to be installed before running the example.
    ```bash
    pip install llama-index tree_sitter tree-sitter-languages
    ```
* **Model APIs:** This example uses Dashscope APIs. Thus, we also need an API key for DashScope.
  ```bash
  export DASH_SCOPE_API='YOUR_API_KEY'
  ```
  However, you are welcome to replace the Dashscope language and embedding models with other models you like.

## Start AgentScope Consultants
* **Terminal:** The most simple way to execute the AgentScope Consultants is running in terminal.
  ```bash
  python ./rag_example.py
  ```
  Setting `log_retrieval` to `false` in `agent_config.json` can hide the retrieved information and provide only answers of agents.

* **AS studio:** If you want to have more organized, clean UI, you can also run with our `as_studio`.
  ```bash
  as_studio ./rag_example.py
  ```

### Customize AgentScope Consultants to other consultants
After you run the example, you may notice that this example consists of three RAG agents:
* `AgentScope Tutorial Assistant`: responsible for answering questions based on AgentScope tutorials (markdown files).
* `AgentScope Framework Code Assistant`: responsible for answering questions based on AgentScope code base (python files).
* `Summarize Assistant`: responsible for summarize the questions from the above two agents.

These agents can be configured to answering questions based on other GitHub repo, by simply modifying the `input_dir` fields in the `agent_config.json`.