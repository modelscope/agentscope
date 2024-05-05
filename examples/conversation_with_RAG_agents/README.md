# AgentScope Consultants: a Multi-Agent RAG Application

This example will show
- How to utilize three different agents to answer various questions about AgentScope.
- How to set up and run the agents using different configurations.

## Background

This example introduces a multi-agent system using retrieval augmented generation (RAG) capabilities to demonstrate how such systems can be built and used effectively.

## Tested Models

These models are tested in this example. For other models, some modifications may be needed.
### models
- dashscope_chat (qwen-max)
### embeddings
- dashscope_text_embedding(text-embedding-v2)

## Prerequisites

Fill the next cell to meet the following requirements
- Cloning the AgentScope repository to local.
- Installation of required packages:
    ```bash
    pip install llama-index tree_sitter tree-sitter-languages
    ```
- Setting environment variables for API keys:
    ```bash
    export DASH_SCOPE_API='YOUR_API_KEY'
    ```
- Running the application via terminal or AS studio:
    ```bash
    python ./rag_example.py
    # or
    as_studio ./rag_example.py
    ```
- [Optional] Optional settings to hide retrieved information by setting `log_retrieval` to `false` in `agent_config.json`.
