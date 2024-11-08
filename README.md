English | [**中文**](https://github.com/modelscope/agentscope/blob/main/README_ZH.md) | [**日本語**](https://github.com/modelscope/agentscope/blob/main/README_JA.md)

# AgentScope

<h1 align="left">
<img src="https://img.alicdn.com/imgextra/i2/O1CN01cdjhVE1wwt5Auv7bY_!!6000000006373-0-tps-1792-1024.jpg" width="600" alt="agentscope-logo">
</h1>

Start building LLM-empowered multi-agent applications in an easier way.

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.1.1-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/ModelScope-Demos-4e29ff.svg?logo=data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjI0IDEyMS4zMyIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KCTxwYXRoIGQ9Im0wIDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtOTkuMTQgNzMuNDloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xNzYuMDkgOTkuMTRoLTI1LjY1djIyLjE5aDQ3Ljg0di00Ny44NGgtMjIuMTl6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTEyNC43OSA0Ny44NGgyNS42NXYyNS42NWgtMjUuNjV6IiBmaWxsPSIjMzZjZmQxIiAvPgoJPHBhdGggZD0ibTAgMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xOTguMjggNDcuODRoMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xOTguMjggMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xNTAuNDQgMHYyMi4xOWgyNS42NXYyNS42NWgyMi4xOXYtNDcuODR6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTczLjQ5IDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiMzNmNmZDEiIC8+Cgk8cGF0aCBkPSJtNDcuODQgMjIuMTloMjUuNjV2LTIyLjE5aC00Ny44NHY0Ny44NGgyMi4xOXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtNDcuODQgNzMuNDloLTIyLjE5djQ3Ljg0aDQ3Ljg0di0yMi4xOWgtMjUuNjV6IiBmaWxsPSIjNjI0YWZmIiAvPgo8L3N2Zz4K)](https://modelscope.cn/studios?name=agentscope&page=1&sort=latest)

[![](https://img.shields.io/badge/Drag_and_drop_UI-WorkStation-blue?logo=html5&logoColor=green&color=dark-green)](https://agentscope.io/)
[![](https://img.shields.io/badge/license-Apache--2.0-black)](./LICENSE)
[![](https://img.shields.io/badge/Contribute-Welcome-green)](https://modelscope.github.io/agentscope/tutorial/contribute.html)

- If you find our work helpful, please kindly cite [our paper](https://arxiv.org/abs/2402.14034).

- Visit our [workstation](https://agentscope.io/) to build multi-agent applications with dragging-and-dropping.

<h5 align="left">
  <a href="https://agentscope.io" target="_blank">
    <img src="https://img.alicdn.com/imgextra/i1/O1CN01RXAVVn1zUtjXVvuqS_!!6000000006718-1-tps-3116-1852.gif" width="500" alt="agentscope-workstation" style="box-shadow: 5px 10px 18px #888888;">
  </a>
</h5>

- Welcome to join our community on

| [Discord](https://discord.gg/eYMpfnkG8h)                                                                                         | DingTalk                                                                                                                          |
|----------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i2/O1CN01tuJ5971OmAqNg9cOw_!!6000000001747-0-tps-444-460.jpg" width="100" height="100"> |

----

## News

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-09-06]** AgentScope version 0.1.0 is released now.

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-09-03]** AgentScope supports **Web Browser Control** now! Refer to our [example](https://github.com/modelscope/agentscope/tree/main/examples/conversation_with_web_browser_agent) for more details.

<h5 align="left">
<video src="https://github.com/user-attachments/assets/6d03caab-6193-4ac6-8b1c-36f152ec02ec" width="45%" alt="web browser control" controls></video>
</h5>

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-07-18]** AgentScope supports streaming mode now! Refer to our [tutorial](https://modelscope.github.io/agentscope/en/tutorial/203-stream.html) and example [conversation in stream mode](https://github.com/modelscope/agentscope/tree/main/examples/conversation_in_stream_mode) for more details.

<h5 align="left">
<img src="https://github.com/user-attachments/assets/b14d9b2f-ce02-4f40-8c1a-950f4022c0cc" width="45%" alt="agentscope-logo">
<img src="https://github.com/user-attachments/assets/dfffbd1e-1fe7-49ee-ac11-902415b2b0d6" width="45%" alt="agentscope-logo">
</h5>

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-07-15]** AgentScope has implemented the Mixture-of-Agents algorithm. Refer to our [MoA example](https://github.com/modelscope/agentscope/blob/main/examples/conversation_mixture_of_agents) for more details.

- **[2024-06-14]** A new prompt tuning module is available in AgentScope to help developers generate and optimize the agents' system prompts! Refer to our [tutorial](https://modelscope.github.io/agentscope/en/tutorial/209-prompt_opt.html) for more details!

- **[2024-06-11]** The RAG functionality is available for agents in **AgentScope** now! [**A quick introduction to RAG in AgentScope**](https://modelscope.github.io/agentscope/en/tutorial/210-rag.html) can help you equip your agent with external knowledge!

- **[2024-06-09]** We release **AgentScope** v0.0.5 now! In this new version, [**AgentScope Workstation**](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html) (the online version is running on [agentscope.io](https://agentscope.io)) is open-sourced with the refactored [**AgentScope Studio**](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html)!

<details>
<summary>Full News</summary>

- **[2024-05-24]** We are pleased to announce that features related to the **AgentScope Workstation** will soon be open-sourced! The online website services are temporarily offline. The online website service will be upgraded and back online shortly. Stay tuned...

- **[2024-05-15]** A new **Parser Module** for **formatted response** is added in AgentScope! Refer to our [tutorial](https://modelscope.github.io/agentscope/en/tutorial/203-parser.html) for more details. The [`DictDialogAgent`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/agents/dict_dialog_agent.py) and [werewolf game](https://github.com/modelscope/agentscope/tree/main/examples/game_werewolf) example are updated simultaneously.

<https://github.com/qbc2016/AgentScope/assets/22984042/22d45aee-3470-4923-850f-348a5b0faaa7>

- **[2024-05-14]** Dear AgentScope users, we are conducting a survey on **AgentScope Workstation & Copilot** user experience. We currently need your valuable feedback to help us improve the experience of AgentScope's Drag & Drop multi-agent application development and Copilot. Your feedback is valuable and the survey will take about 3~5 minutes. Please click [URL](https://survey.aliyun.com/apps/zhiliao/vgpTppn22) to participate in questionnaire surveys. Thank you very much for your support and contribution!

- **[2024-05-14]** AgentScope supports **gpt-4o** as well as other OpenAI vision models now! Try gpt-4o with its [model configuration](./examples/model_configs_template/openai_chat_template.json) and new example [Conversation with gpt-4o](./examples/conversation_with_gpt-4o)!

- **[2024-04-30]** We release **AgentScope** v0.0.4 now!

- **[2024-04-27]** [AgentScope Workstation](https://agentscope.io/) is now online! You are welcome to try building your multi-agent application simply with our *drag-and-drop platform* and ask our *copilot* questions about AgentScope!

- **[2024-04-19]** AgentScope supports Llama3 now! We provide [scripts](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3) and example [model configuration](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3) for quick set-up. Feel free to try llama3 in our examples!

- **[2024-04-06]** We release **AgentScope** v0.0.3 now!

- **[2024-04-06]** New examples [Gomoku](https://github.com/modelscope/agentscope/blob/main/examples/game_gomoku), [Conversation with ReAct Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_react_agent), [Conversation with RAG Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_RAG_agents) and [Distributed Parallel Optimization](https://github.com/modelscope/agentscope/blob/main/examples/distributed_parallel_optimization) are available now!

- **[2024-03-19]** We release **AgentScope** v0.0.2 now! In this new version,
AgentScope supports [ollama](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models)(A local CPU inference engine), [DashScope](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models) and Google [Gemini](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models) APIs.

- **[2024-03-19]** New examples ["Autonomous Conversation with Mentions"](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_mentions) and ["Basic Conversation with LangChain library"](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_langchain) are available now!

- **[2024-03-19]** The [Chinese tutorial](https://modelscope.github.io/agentscope/zh_CN/index.html) of AgentScope is online now!

- **[2024-02-27]** We release **AgentScope v0.0.1** now, which is also
available in [PyPI](https://pypi.org/project/agentscope/)!
- **[2024-02-14]** We release our paper "AgentScope: A Flexible yet Robust
Multi-Agent Platform" in [arXiv](https://arxiv.org/abs/2402.14034) now!

</details>

---

## What's AgentScope?

AgentScope is an innovative multi-agent platform designed to empower developers
to build multi-agent applications with large-scale models.
It features three high-level capabilities:

- 🤝 **Easy-to-Use**: Designed for developers, with [fruitful components](https://modelscope.github.io/agentscope/en/tutorial/204-service.html#),
[comprehensive documentation](https://modelscope.github.io/agentscope/en/index.html), and broad compatibility. Besides, [AgentScope Workstation](https://agentscope.io/) provides a *drag-and-drop programming platform* and a *copilot* for beginners of AgentScope!

- ✅ **High Robustness**: Supporting customized fault-tolerance controls and
retry mechanisms to enhance application stability.

- 🚀 **Actor-Based Distribution**: Building distributed multi-agent
applications in a centralized programming manner for streamlined development.

**Supported Model Libraries**

AgentScope provides a list of `ModelWrapper` to support both local model
services and third-party model APIs.

| API                    | Task            | Model Wrapper                                                                                                                   | Configuration                                                                                                                                                                                                                            | Some Supported Models                                           |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| OpenAI API             | Chat            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api)  <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_chat_template.json)                 | gpt-4o, gpt-4, gpt-3.5-turbo, ...                               |
|                        | Embedding       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_embedding_template.json)             | text-embedding-ada-002, ...                                     |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_dall_e_template.json)                | dall-e-2, dall-e-3                                              |
| DashScope API          | Chat            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_chat_template.json)            | qwen-plus, qwen-max, ...                                        |
|                        | Image Synthesis | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api)  <br>[template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_image_synthesis_template.json) | wanx-v1                                                         |
|                        | Text Embedding  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_text_embedding_template.json)  | text-embedding-v1, text-embedding-v2, ...                       |
|                        | Multimodal      | [`DashScopeMultiModalWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)     | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_multimodal_template.json)      | qwen-vl-max, qwen-vl-chat-v1, qwen-audio-chat                   |
| Gemini API             | Chat            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#gemini-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_chat_template.json)                  | gemini-pro, ...                                                 |
|                        | Embedding       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#gemini-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_embedding_template.json)             | models/embedding-001, ...                                       |
| ZhipuAI API            | Chat            | [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#zhipu-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_chat_template.json)                    | glm-4, ...                                                      |
|                        | Embedding       | [`ZhipuAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)            | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#zhipu-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_embedding_template.json)               | embedding-2, ...                                                |
| ollama                 | Chat            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_chat_template.json)                  | llama3, llama2, Mistral, ...                                    |
|                        | Embedding       | [`OllamaEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)            | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_embedding_template.json)             | llama2, Mistral, ...                                            |
|                        | Generation      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_generate_template.json)              | llama2, Mistral, ...                                            |
| LiteLLM API            | Chat            | [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)               | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#litellm-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/litellm_chat_template.json)                | [models supported by litellm](https://docs.litellm.ai/docs/)... |
| Yi API                 | Chat            | [`YiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/yi_model.py)                         | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/yi_chat_template.json)                | yi-large, yi-medium, ...                                        |
| Post Request based API | -               | [`PostAPIModelWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 | [guidance](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#post-request-api) <br> [template](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/postapi_model_config_template.json)   | -                                                               |

**Supported Local Model Deployment**

AgentScope enables developers to rapidly deploy local model services using
the following libraries.

- [ollama (CPU inference)](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#ollama)
- [Flask + Transformers](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-transformers-library)
- [Flask + ModelScope](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-modelscope-library)
- [FastChat](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#fastchat)
- [vllm](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#vllm)

**Supported Services**

- Web Search
- Data Query
- Retrieval
- Code Execution
- File Operation
- Text Processing
- Multi Modality
- Wikipedia Search and Retrieval
- TripAdvisor Search
- Web Browser Control

**Example Applications**

- Model
  - [Using Llama3 in AgentScope](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3)

- Conversation
  - [Basic Conversation](https://github.com/modelscope/agentscope/blob/main/examples/conversation_basic)
  - [Autonomous Conversation with Mentions](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_mentions)
  - [Self-Organizing Conversation](https://github.com/modelscope/agentscope/blob/main/examples/conversation_self_organizing)
  - [Basic Conversation with LangChain library](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_langchain)
  - [Conversation with ReAct Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_react_agent)
  - [Conversation in Natural Language to Query SQL](https://github.com/modelscope/agentscope/blob/main/examples/conversation_nl2sql/)
  - [Conversation with RAG Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_RAG_agents)
  - [Conversation with gpt-4o](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_gpt-4o)
  - [Conversation with Software Engineering Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_swe-agent/)
  - [Conversation with Customized Tools](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_customized_services/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Mixture of Agents Algorithm](https://github.com/modelscope/agentscope/blob/main/examples/conversation_mixture_of_agents/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Conversation in Stream Mode](https://github.com/modelscope/agentscope/blob/main/examples/conversation_in_stream_mode/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Conversation with CodeAct Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_codeact_agent/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Conversation with Router Agent](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_router_agent/)

- Game
  - [Gomoku](https://github.com/modelscope/agentscope/blob/main/examples/game_gomoku)
  - [Werewolf](https://github.com/modelscope/agentscope/blob/main/examples/game_werewolf)

- Distribution
  - [Distributed Conversation](https://github.com/modelscope/agentscope/blob/main/examples/distributed_conversation)
  - [Distributed Debate](https://github.com/modelscope/agentscope/blob/main/examples/distributed_debate)
  - [Distributed Parallel Optimization](https://github.com/modelscope/agentscope/blob/main/examples/distributed_parallel_optimization)
  - [Distributed Large Scale Simulation](https://github.com/modelscope/agentscope/blob/main/examples/distributed_simulation)

More models, services and examples are coming soon!

## Installation

AgentScope requires **Python 3.9** or higher.

***Note: This project is currently in active development, it's recommended to
install AgentScope from source.***

### From source

- Install AgentScope in editable mode:

```bash
# Pull the source code from GitHub
git clone https://github.com/modelscope/agentscope.git

# Install the package in editable mode
cd agentscope
pip install -e .
```

### Using pip

- Install AgentScope from pip:

```bash
pip install agentscope
```

### Extra Dependencies

To support different deployment scenarios, AgentScope provides several
optional dependencies. Full list of optional dependencies refers to
[tutorial](https://doc.agentscope.io/en/tutorial/102-installation.html)
Taking distribution mode as an example, you can install its dependencies
as follows:

#### On Windows

```bash
# From source
pip install -e .[distribute]
# From pypi
pip install agentscope[distribute]
```

#### On Mac & Linux

```bash
# From source
pip install -e .\[distribute\]
# From pypi
pip install agentscope\[distribute\]
```

## Quick Start

### Configuration

In AgentScope, the model deployment and invocation are decoupled by
`ModelWrapper`.

To use these model wrappers, you need to prepare a model config file as
follows.

```python
model_config = {
    # The identifies of your config and used model wrapper
    "config_name": "{your_config_name}",          # The name to identify the config
    "model_type": "{model_type}",                 # The type to identify the model wrapper

    # Detailed parameters into initialize the model wrapper
    # ...
}
```

Taking OpenAI Chat API as an example, the model configuration is as follows:

```python
openai_model_config = {
    "config_name": "my_openai_config",             # The name to identify the config
    "model_type": "openai_chat",                   # The type to identify the model wrapper

    # Detailed parameters into initialize the model wrapper
    "model_name": "gpt-4",                         # The used model in openai API, e.g. gpt-4, gpt-3.5-turbo, etc.
    "api_key": "xxx",                              # The API key for OpenAI API. If not set, env
                                                   # variable OPENAI_API_KEY will be used.
    "organization": "xxx",                         # The organization for OpenAI API. If not set, env
                                                   # variable OPENAI_ORGANIZATION will be used.
}
```

More details about how to set up local model services and prepare model
configurations is in our
[tutorial](https://modelscope.github.io/agentscope/index.html#welcome-to-agentscope-tutorial-hub).

### Create Agents

Create built-in user and assistant agents as follows.

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# Load model configs
agentscope.init(model_configs="./model_configs.json")

# Create a dialog agent and a user agent
dialog_agent = DialogAgent(name="assistant",
                           model_config_name="my_openai_config")
user_agent = UserAgent()
```

### Construct Conversation

In AgentScope, **message** is the bridge among agents, which is a
**dict** that contains two necessary fields `name` and `content` and an
optional field `url` to local files (image, video or audio) or website.

```python
from agentscope.message import Msg

x = Msg(name="Alice", content="Hi!")
x = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

Start a conversation between two agents (e.g. dialog_agent and user_agent)
with the following code:

```python
x = None
while True:
    x = dialog_agent(x)
    x = user_agent(x)
    if x.content == "exit":  # user input "exit" to exit the conversation_basic
        break
```

### AgentScope Studio

AgentScope provides an easy-to-use runtime user interface capable of
displaying multimodal output on the front end, including text, images,
audio and video.

Refer to our [tutorial](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html) for more details.

<h5 align="center">
<img src="https://img.alicdn.com/imgextra/i4/O1CN015kjnkd1xdwJoNxqLZ_!!6000000006467-0-tps-3452-1984.jpg" width="600" alt="agentscope-logo">
</h5>

## Tutorial

- [About AgentScope](https://modelscope.github.io/agentscope/zh_CN/tutorial/101-agentscope.html)
- [Installation](https://modelscope.github.io/agentscope/zh_CN/tutorial/102-installation.html)
- [Quick Start](https://modelscope.github.io/agentscope/zh_CN/tutorial/103-example.html)
- [Model](https://modelscope.github.io/agentscope/zh_CN/tutorial/203-model.html)
- [Prompt Engineering](https://modelscope.github.io/agentscope/zh_CN/tutorial/206-prompt.html)
- [Agent](https://modelscope.github.io/agentscope/zh_CN/tutorial/201-agent.html)
- [Memory](https://modelscope.github.io/agentscope/zh_CN/tutorial/205-memory.html)
- [Response Parser](https://modelscope.github.io/agentscope/zh_CN/tutorial/203-parser.html)
- [Tool](https://modelscope.github.io/agentscope/zh_CN/tutorial/204-service.html)
- [Pipeline and MsgHub](https://modelscope.github.io/agentscope/zh_CN/tutorial/202-pipeline.html)
- [Distribution](https://modelscope.github.io/agentscope/zh_CN/tutorial/208-distribute.html)
- [AgentScope Studio](https://modelscope.github.io/agentscope/zh_CN/tutorial/209-gui.html)
- [Logging](https://modelscope.github.io/agentscope/zh_CN/tutorial/105-logging.html)
- [Monitor](https://modelscope.github.io/agentscope/zh_CN/tutorial/207-monitor.html)
- [Example: Werewolf Game](https://modelscope.github.io/agentscope/zh_CN/tutorial/104-usecase.html)

## License

AgentScope is released under Apache License 2.0.

## Contributing

Contributions are always welcomed!

We provide a developer version with additional pre-commit hooks to perform
checks compared to the official version:

```bash
# For windows
pip install -e .[dev]
# For mac
pip install -e .\[dev\]

# Install pre-commit hooks
pre-commit install
```

Please refer to our [Contribution Guide](https://modelscope.github.io/agentscope/en/tutorial/302-contribute.html) for more details.

## Publications

If you find our work helpful for your research or application, please cite our papers.

1. [AgentScope: A Flexible yet Robust Multi-Agent Platform](https://arxiv.org/abs/2402.14034)

    ```
    @article{agentscope,
        author  = {Dawei Gao and
                   Zitao Li and
                   Xuchen Pan and
                   Weirui Kuang and
                   Zhijian Ma and
                   Bingchen Qian and
                   Fei Wei and
                   Wenhao Zhang and
                   Yuexiang Xie and
                   Daoyuan Chen and
                   Liuyi Yao and
                   Hongyi Peng and
                   Ze Yu Zhang and
                   Lin Zhu and
                   Chen Cheng and
                   Hongzhu Shi and
                   Yaliang Li and
                   Bolin Ding and
                   Jingren Zhou}
        title   = {AgentScope: A Flexible yet Robust Multi-Agent Platform},
        journal = {CoRR},
        volume  = {abs/2402.14034},
        year    = {2024},
    }
    ```
