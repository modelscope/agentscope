[English](https://github.com/modelscope/agentscope/blob/main/README.md) | [中文](https://github.com/modelscope/agentscope/blob/main/README_ZH.md) | 日本語

# AgentScope

<h1 align="left">
<img src="https://img.alicdn.com/imgextra/i2/O1CN01cdjhVE1wwt5Auv7bY_!!6000000006373-0-tps-1792-1024.jpg" width="600" alt="agentscope-logo">
</h1>

LLMを活用したマルチエージェントアプリケーションをより簡単に構築する。

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.1.1-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/ModelScope-Demos-4e29ff.svg?logo=data:image/svg+xml;base64,PHN2ZyB2aWV3Qm94PSIwIDAgMjI0IDEyMS4zMyIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KCTxwYXRoIGQ9Im0wIDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtOTkuMTQgNzMuNDloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xNzYuMDkgOTkuMTRoLTI1LjY1djIyLjE5aDQ3Ljg0di00Ny44NGgtMjIuMTl6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTEyNC43OSA0Ny44NGgyNS42NXYyNS42NWgtMjUuNjV6IiBmaWxsPSIjMzZjZmQxIiAvPgoJPHBhdGggZD0ibTAgMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xOTguMjggNDcuODRoMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzYyNGFmZiIgLz4KCTxwYXRoIGQ9Im0xOTguMjggMjIuMTloMjUuNjV2MjUuNjVoLTI1LjY1eiIgZmlsbD0iIzM2Y2ZkMSIgLz4KCTxwYXRoIGQ9Im0xNTAuNDQgMHYyMi4xOWgyNS42NXYyNS42NWgyMi4xOXYtNDcuODR6IiBmaWxsPSIjNjI0YWZmIiAvPgoJPHBhdGggZD0ibTczLjQ5IDQ3Ljg0aDI1LjY1djI1LjY1aC0yNS42NXoiIGZpbGw9IiMzNmNmZDEiIC8+Cgk8cGF0aCBkPSJtNDcuODQgMjIuMTloMjUuNjV2LTIyLjE5aC00Ny44NHY0Ny44NGgyMi4xOXoiIGZpbGw9IiM2MjRhZmYiIC8+Cgk8cGF0aCBkPSJtNDcuODQgNzMuNDloLTIyLjE5djQ3Ljg0aDQ3Ljg0di0yMi4xOWgtMjUuNjV6IiBmaWxsPSIjNjI0YWZmIiAvPgo8L3N2Zz4K)](https://modelscope.cn/studios?name=agentscope&page=1&sort=latest)

[![](https://img.shields.io/badge/Drag_and_drop_UI-WorkStation-blue?logo=html5&logoColor=green&color=dark-green)](https://agentscope.io/)
[![](https://img.shields.io/badge/license-Apache--2.0-black)](./LICENSE)
[![](://img.shields.io/badge/Contribute-Welcome-green)](https://modelscope.github.io/agentscope/tutorial/contribute.html)

- 私たちの仕事が役に立った場合は、[論文](https://arxiv.org/abs/2402.14034)を引用してください。

- [agentscope.io](https://agentscope.io/)にアクセスして、ドラッグアンドドロップでマルチエージェントアプリケーションを構築してください。

<h5 align="left">
  <a href="https://agentscope.io" target="_blank">
    <img src="https://img.alicdn.com/imgextra/i1/O1CN01RXAVVn1zUtjXVvuqS_!!6000000006718-1-tps-3116-1852.gif" width="500" alt="agentscope-workstation" style="box-shadow: 5px 10px 18px #888888;">
  </a>
</h5>

- 私たちのコミュニティに参加してください

| [Discord](https://discord.gg/eYMpfnkG8h) | DingTalk |
|---------|----------|
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i2/O1CN01tuJ5971OmAqNg9cOw_!!6000000001747-0-tps-444-460.jpg" width="100" height="100"> |

----

## ニュース

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-09-06]** AgentScopeバージョン0.1.0がリリースされました。

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-09-03]** AgentScopeは**Webブラウザ制御**をサポートしています。詳細については、[例](https://github.com/modelscope/agentscope/tree/main/examples/conversation_with_web_browser_agent)を参照してください。

<h5 align="left">
<video src="https://github.com/user-attachments/assets/6d03caab-6193-4ac6-8b1c-36f152ec02ec" width="45%" alt="web browser control" controls></video>
</h5>

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-07-18]** AgentScopeはストリーミングモードをサポートしています。詳細については、[チュートリアル](https://modelscope.github.io/agentscope/en/tutorial/203-stream.html)および[ストリーミングモードでの会話の例](https://github.com/modelscope/agentscope/tree/main/examples/conversation_in_stream_mode)を参照してください。

<h5 align="left">
<img src="https://github.com/user-attachments/assets/b14d9b2f-ce02-4f40-8c1a-950f4022c0cc" width="45%" alt="agentscope-logo">
<img src="https://github.com/user-attachments/assets/dfffbd1e-1fe7-49ee-ac11-902415b2b0d6" width="45%" alt="agentscope-logo">
</h5>

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2024-07-15]** AgentScopeはMixture-of-Agentsアルゴリズムを実装しました。詳細については、[MoAの例](https://github.com/modelscope/agentscope/blob/main/examples/conversation_mixture_of_agents)を参照してください。

- **[2024-06-14]** 新しいプロンプトチューニングモジュールがAgentScopeに追加され、開発者がエージェントのシステムプロンプトを生成および最適化するのに役立ちます。詳細については、[チュートリアル](https://modelscope.github.io/agentscope/en/tutorial/209-prompt_opt.html)を参照してください。

- **[2024-06-11]** RAG機能が**AgentScope**に追加されました。エージェントに外部知識を装備するための[**AgentScopeのRAGの簡単な紹介**](https://modelscope.github.io/agentscope/en/tutorial/210-rag.html)を参照してください。

- **[2024-06-09]** **AgentScope** v0.0.5がリリースされました。この新しいバージョンでは、[**AgentScope Workstation**](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html)（オンラインバージョンは[agentscope.io](https://agentscope.io)で実行されています）がリファクタリングされた[**AgentScope Studio**](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html)とともにオープンソース化されました。

<details>
<summary>完全なニュース</summary>

- **[2024-05-24]** **AgentScope Workstation**に関連する機能がまもなくオープンソース化されることをお知らせします。オンラインウェブサイトサービスは一時的にオフラインになっています。オンラインウェブサイトサービスはアップグレードされ、まもなく再開されます。お楽しみに...

- **[2024-05-15]** **フォーマットされた応答**のための新しい**パーサーモジュール**がAgentScopeに追加されました。詳細については、[チュートリアル](https://modelscope.github.io/agentscope/en/tutorial/203-parser.html)を参照してください。[`DictDialogAgent`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/agents/dict_dialog_agent.py)および[人狼ゲーム](https://github.com/modelscope/agentscope/tree/main/examples/game_werewolf)の例も同時に更新されました。

- **[2024-05-14]** 親愛なるAgentScopeユーザーの皆様、**AgentScope Workstation & Copilot**のユーザーエクスペリエンスに関するアンケートを実施しています。現在、AgentScopeのドラッグアンドドロップマルチエージェントアプリケーション開発とCopilotのエクスペリエンスを改善するために、貴重なフィードバックが必要です。フィードバックは貴重であり、アンケートには約3〜5分かかります。アンケート調査に参加するには、[URL](https://survey.aliyun.com/apps/zhiliao/vgpTppn22)をクリックしてください。ご支援とご協力に感謝します。

- **[2024-05-14]** AgentScopeは**gpt-4o**および他のOpenAIビジョンモデルをサポートしています。gpt-4oを[モデル構成](./examples/model_configs_template/openai_chat_template.json)と新しい例[Conversation with gpt-4o](./examples/conversation_with_gpt-4o)で試してください。

- **[2024-04-30]** **AgentScope** v0.0.4がリリースされました。

- **[2024-04-27]** [AgentScope Workstation](https://agentscope.io/)がオンラインになりました。*ドラッグアンドドロッププラットフォーム*を使用してマルチエージェントアプリケーションを構築し、*copilot*にAgentScopeに関する質問をすることができます。

- **[2024-04-19]** AgentScopeはLlama3をサポートしています。クイックセットアップのための[スクリプト](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3)と[モデル構成](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3)を提供しています。例でllama3を試してみてください。

- **[2024-04-06]** **AgentScope** v0.0.3がリリースされました。

- **[2024-04-06]** 新しい例[五目並べ](https://github.com/modelscope/agentscope/blob/main/examples/game_gomoku)、[ReActエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_react_agent)、[RAGエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_RAG_agents)、および[分散並列最適化](https://github.com/modelscope/agentscope/blob/main/examples/distributed_parallel_optimization)が利用可能になりました。

- **[2024-03-19]** **AgentScope** v0.0.2がリリースされました。この新しいバージョンでは、AgentScopeは[ollama](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models)（ローカルCPU推論エンジン）、[DashScope](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models)およびGoogle[Gemini](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#supported-models)APIをサポートしています。

- **[2024-03-19]** 新しい例「[メンション付きの自律会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_mentions)」および「[LangChainライブラリを使用した基本的な会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_langchain)」が利用可能になりました。

- **[2024-03-19]** AgentScopeの[中国語チュートリアル](https://modelscope.github.io/agentscope/zh_CN/index.html)がオンラインになりました。

- **[2024-02-27]** **AgentScope v0.0.1**がリリースされました。これは[PyPI](https://pypi.org/project/agentscope/)でも利用可能です。

- **[2024-02-14]** 私たちは論文「[AgentScope: A Flexible yet Robust Multi-Agent Platform](https://arxiv.org/abs/2402.14034)」を[arXiv](https://arxiv.org/abs/2402.14034)に発表しました。

</details>

---

## AgentScopeとは？

AgentScopeは、開発者が大規模モデルを使用してマルチエージェントアプリケーションを構築する能力を提供する革新的なマルチエージェントプラットフォームです。
それは3つの高レベルの機能を備えています：

- 🤝 **使いやすさ**：開発者向けに設計されており、[豊富なコンポーネント](https://modelscope.github.io/agentscope/en/tutorial/204-service.html#)、[包括的なドキュメント](https://modelscope.github.io/agentscope/en/index.html)、および広範な互換性を提供します。さらに、[AgentScope Workstation](https://agentscope.io/)は、初心者向けの*ドラッグアンドドロッププログラミングプラットフォーム*と*copilot*を提供します。

- ✅ **高い堅牢性**：カスタマイズ可能なフォールトトレランス制御と再試行メカニズムをサポートし、アプリケーションの安定性を向上させます。

- 🚀 **アクターベースの分散**：集中型プログラミング方式で分散マルチエージェントアプリケーションを構築し、開発を簡素化します。

**サポートされているモデルライブラリ**

AgentScopeは、ローカルモデルサービスとサードパーティのモデルAPIの両方をサポートするための`ModelWrapper`のリストを提供します。

| API                    | タスク            | モデルラッパー                                                                                                                   | 構成                                                                                                                                                                                                                            | サポートされているモデルの一部                                           |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| OpenAI API             | チャット            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api)  <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_chat_template.json)                 | gpt-4o, gpt-4, gpt-3.5-turbo, ...                               |
|                        | 埋め込み       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_embedding_template.json)             | text-embedding-ada-002, ...                                     |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#openai-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_dall_e_template.json)                | dall-e-2, dall-e-3                                              |
| DashScope API          | チャット            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_chat_template.json)            | qwen-plus, qwen-max, ...                                        |
|                        | 画像生成 | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api)  <br>[テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_image_synthesis_template.json) | wanx-v1                                                         |
|                        | テキスト埋め込み  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_text_embedding_template.json)  | text-embedding-v1, text-embedding-v2, ...                       |
|                        | マルチモーダル      | [`DashScopeMultiModalWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)     | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#dashscope-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_multimodal_template.json)      | qwen-vl-max, qwen-vl-chat-v1, qwen-audio-chat                   |
| Gemini API             | チャット            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#gemini-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_chat_template.json)                  | gemini-pro, ...                                                 |
|                        | 埋め込み       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#gemini-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_embedding_template.json)             | models/embedding-001, ...                                       |
| ZhipuAI API            | チャット            | [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#zhipu-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_chat_template.json)                    | glm-4, ...                                                      |
|                        | 埋め込み       | [`ZhipuAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)            | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#zhipu-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_embedding_template.json)               | embedding-2, ...                                                |
| ollama                 | チャット            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_chat_template.json)                  | llama3, llama2, Mistral, ...                                    |
|                        | 埋め込み       | [`OllamaEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)            | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_embedding_template.json)             | llama2, Mistral, ...                                            |
|                        | 生成      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#ollama-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_generate_template.json)              | llama2, Mistral, ...                                            |
| LiteLLM API            | チャット            | [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)               | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#litellm-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/litellm_chat_template.json)                | [litellmがサポートするモデル](https://docs.litellm.ai/docs/)... |
| Yi API                 | チャット            | [`YiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/yi_model.py)                         | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/yi_chat_template.json)                | yi-large, yi-medium, ...                                        |
| Post Request based API | -               | [`PostAPIModelWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 | [ガイダンス](https://modelscope.github.io/agentscope/en/tutorial/203-model.html#post-request-api) <br> [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/postapi_model_config_template.json)   | -                                                               |

**サポートされているローカルモデルのデプロイ**

AgentScopeは、次のライブラリを使用してローカルモデルサービスを迅速にデプロイするためのサポートを提供します。

- [ollama (CPU推論)](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#ollama)
- [Flask + Transformers](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-transformers-library)
- [Flask + ModelScope](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#with-modelscope-library)
- [FastChat](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#fastchat)
- [vllm](https://github.com/modelscope/agentscope/blob/main/scripts/README.md#vllm)

**サポートされているサービス**

- ウェブ検索
- データクエリ
- 検索
- コード実行
- ファイル操作
- テキスト処理
- マルチモーダル生成
- Wikipedia検索と検索
- TripAdvisor検索
- ウェブブラウザ制御

**例のアプリケーション**

- モデル
  - [AgentScopeでLlama3を使用する](https://github.com/modelscope/agentscope/blob/main/examples/model_llama3)

- 会話
  - [基本的な会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_basic)
  - [メンション付きの自律会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_mentions)
  - [自己組織化会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_self_organizing)
  - [LangChainライブラリを使用した基本的な会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_langchain)
  - [ReActエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_react_agent)
  - [自然言語でSQLをクエリする会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_nl2sql/)
  - [RAGエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_RAG_agents)
  - [gpt-4oとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_gpt-4o)
  - [ソフトウェアエンジニアリングエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_swe-agent/)
  - [カスタマイズされたツールとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_customized_services/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Mixture of Agentsアルゴリズム](https://github.com/modelscope/agentscope/blob/main/examples/conversation_mixture_of_agents/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[ストリーミングモードでの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_in_stream_mode/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[CodeActエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_codeact_agent/)
  - <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>[Routerエージェントとの会話](https://github.com/modelscope/agentscope/blob/main/examples/conversation_with_router_agent/)

- ゲーム
  - [五目並べ](https://github.com/modelscope/agentscope/blob/main/examples/game_gomoku)
  - [人狼](https://github.com/modelscope/agentscope/blob/main/examples/game_werewolf)

- 分散
  - [分散会話](https://github.com/modelscope/agentscope/blob/main/examples/distributed_conversation)
  - [分散ディベート](https://github.com/modelscope/agentscope/blob/main/examples/distributed_debate)
  - [分散並列最適化](https://github.com/modelscope/agentscope/blob/main/examples/distributed_parallel_optimization)
  - [分散大規模シミュレーション](https://github.com/modelscope/agentscope/blob/main/examples/distributed_simulation)

さらに多くのモデル、サービス、および例が近日公開予定です。

## インストール

AgentScopeは**Python 3.9**以上が必要です。

***注：このプロジェクトは現在アクティブに開発中であり、AgentScopeをソースからインストールすることをお勧めします。***

### ソースから

- AgentScopeを編集モードでインストールします：

```bash
# GitHubからソースコードを取得
git clone https://github.com/modelscope/agentscope.git

# パッケージを編集モードでインストール
cd agentscope
pip install -e .
```

### pipを使用

- pipからAgentScopeをインストールします：

```bash
pip install agentscope
```

### 追加の依存関係

さまざまなデプロイメントシナリオをサポートするために、AgentScopeはいくつかのオプションの依存関係を提供します。オプションの依存関係の完全なリストは、[チュートリアル](https://doc.agentscope.io/en/tutorial/102-installation.html)を参照してください。分散モードを例にとると、次のように依存関係をインストールできます：

#### Windowsの場合

```bash
# ソースから
pip install -e .[distribute]
# pypiから
pip install agentscope[distribute]
```

#### Mac & Linuxの場合

```bash
# ソースから
pip install -e .\[distribute\]
# pypiから
pip install agentscope\[distribute\]
```

## クイックスタート

### 構成

AgentScopeでは、モデルのデプロイメントと呼び出しは`ModelWrapper`によってデカップリングされています。

これらのモデルラッパーを使用するには、次のようなモデル構成ファイルを準備する必要があります。

```python
model_config = {
    # 構成の識別子と使用されるモデルラッパー
    "config_name": "{your_config_name}",          # 構成を識別する名前
    "model_type": "{model_type}",                 # モデルラッパーを識別するタイプ

    # モデルラッパーを初期化するための詳細なパラメータ
    # ...
}
```

OpenAI Chat APIを例にとると、モデル構成は次のようになります：

```python
openai_model_config = {
    "config_name": "my_openai_config",             # 構成を識別する名前
    "model_type": "openai_chat",                   # モデルラッパーを識別するタイプ

    # モデルラッパーを初期化するための詳細なパラメータ
    "model_name": "gpt-4",                         # OpenAI APIで使用されるモデル名（例：gpt-4、gpt-3.5-turboなど）
    "api_key": "xxx",                              # OpenAI APIのAPIキー。設定されていない場合、環境変数OPENAI_API_KEYが使用されます。
    "organization": "xxx",                         # OpenAI APIの組織。設定されていない場合、環境変数OPENAI_ORGANIZATIONが使用されます。
}
```

ローカルモデルサービスのセットアップ方法やモデル構成の準備方法の詳細については、[チュートリアル](https://modelscope.github.io/agentscope/index.html#welcome-to-agentscope-tutorial-hub)を参照してください。

### エージェントの作成

次のように組み込みのユーザーエージェントとアシスタントエージェントを作成します。

```python
from agentscope.agents import DialogAgent, UserAgent
import agentscope

# モデル構成を読み込む
agentscope.init(model_configs="./model_configs.json")

# ダイアログエージェントとユーザーエージェントを作成する
dialog_agent = DialogAgent(name="assistant",
                           model_config_name="my_openai_config")
user_agent = UserAgent()
```

### 会話の構築

AgentScopeでは、**メッセージ**はエージェント間の橋渡しであり、**dict**であり、2つの必要なフィールド`name`と`content`、およびローカルファイル（画像、ビデオ、またはオーディオ）またはウェブサイトへのオプションのフィールド`url`を含みます。

```python
from agentscope.message import Msg

x = Msg(name="Alice", content="Hi!")
x = Msg("Bob", "What about this picture I took?", url="/path/to/picture.jpg")
```

次のコードを使用して、2つのエージェント（例：dialog_agentとuser_agent）間の会話を開始します：

```python
x = None
while True:
    x = dialog_agent(x)
    x = user_agent(x)
    if x.content == "exit":  # ユーザーが"exit"と入力して会話を終了する
        break
```

### AgentScope Studio

AgentScopeは、テキスト、画像、オーディオ、ビデオなどのマルチモーダル出力をフロントエンドで表示できる使いやすいランタイムユーザーインターフェースを提供します。

詳細については、[チュートリアル](https://modelscope.github.io/agentscope/en/tutorial/209-gui.html)を参照してください。

<h5 align="center">
<img src="https://img.alicdn.com/imgextra/i4/O1CN015kjnkd1xdwJoNxqLZ_!!6000000006467-0-tps-3452-1984.jpg" width="600" alt="agentscope-logo">
</h5>

## チュートリアル

- [AgentScopeについて](https://modelscope.github.io/agentscope/zh_CN/tutorial/101-agentscope.html)
- [インストール](https://modelscope.github.io/agentscope/zh_CN/tutorial/102-installation.html)
- [クイックスタート](https://modelscope.github.io/agentscope/zh_CN/tutorial/103-example.html)
- [モデル](https://modelscope.github.io/agentscope/zh_CN/tutorial/203-model.html)
- [プロンプトエンジニアリング](https://modelscope.github.io/agentscope/zh_CN/tutorial/206-prompt.html)
- [エージェント](https://modelscope.github.io/agentscope/zh_CN/tutorial/201-agent.html)
- [メモリ](https://modelscope.github.io/agentscope/zh_CN/tutorial/205-memory.html)
- [応答パーサー](https://modelscope.github.io/agentscope/zh_CN/tutorial/203-parser.html)
- [ツール](https://modelscope.github.io/agentscope/zh_CN/tutorial/204-service.html)
- [パイプラインとMsgHub](https://modelscope.github.io/agentscope/zh_CN/tutorial/202-pipeline.html)
- [分散](https://modelscope.github.io/agentscope/zh_CN/tutorial/208-distribute.html)
- [AgentScope Studio](https://modelscope.github.io/agentscope/zh_CN/tutorial/209-gui.html)
- [ログ](https://modelscope.github.io/agentscope/zh_CN/tutorial/105-logging.html)
- [モニター](https://modelscope.github.io/agentscope/zh_CN/tutorial/207-monitor.html)
- [例：人狼ゲーム](https://modelscope.github.io/agentscope/zh_CN/tutorial/104-usecase.html)

## ライセンス

AgentScopeはApache License 2.0の下でリリースされています。

## 貢献

貢献は常に歓迎されます！

公式バージョンと比較して、追加のプリコミットフックを使用してチェックを実行する開発者バージョンを提供します：

```bash
# Windowsの場合
pip install -e .[dev]
# Macの場合
pip install -e .\[dev\]

# プリコミットフックをインストール
pre-commit install
```

詳細については、[貢献ガイド](https://modelscope.github.io/agentscope/en/tutorial/302-contribute.html)を参照してください。

## 出版物

私たちの仕事があなたの研究やアプリケーションに役立つ場合は、私たちの論文を引用してください。

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
