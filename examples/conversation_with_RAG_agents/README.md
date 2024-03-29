# AgentScope Consultants: a Multi-Agent RAG Application

* **What is this example about?**
With the provided implementation and configuration,
you will obtain three different agents who can help you answer different questions about AgentScope.

* **What is this example for?** By this example, we want to show how the agent with retrieval augmented generation (RAG)
capability can be used to build easily.

**Notice:** This example is a Beta version of the AgentScope RAG agent. A formal version will soon be added to `src/agentscope/agents`, but it may be subject to changes.

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

**Note:** This example has been tested with `dashscope_chat` and `dashscope_text_embedding` model wrapper, with `qwen-max` and `text-embedding-v2` models.
However, you are welcome to replace the Dashscope language and embedding model wrappers or models with other models you like to test.

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

For more advanced customization, we may need to learn a little bit from the following.

**RAG modules:** In AgentScope, RAG modules are abstract to provide three basic functions: `load_data`, `store_and_index` and `retrieve`. Refer to `src/agentscope/rag` for more details.

**RAG configs:** In the example configuration (the `rag_config` field), all parameters are optional. But if you want to customize them, you may want to learn the following:
*  `load_data`: contains all parameters for the the `rag.load_data` function.
Since the `load_data` accepts a dataloader object `loader`, the `loader` in the config need to have `"create_object": true` to let a internal parse create a LlamaIndex data loader object.
The loader object is an instance of `class` in module `module`, with initialization parameters in `init_args`.

* `store_and_index`: contains all parameters for the the `rag.store_and_index` function.
For example, you can pass `vector_store` and `retriever` configurations in a similar way as the `loader` mentioned above.
For the `transformations` parameter, you can pass a list of dicts, each of which corresponds to building a `NodeParser`-kind of preprocessor in Llamaindex.