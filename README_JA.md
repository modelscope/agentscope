[English](https://github.com/modelscope/agentscope/blob/main/README.md) | [中文](https://github.com/modelscope/agentscope/blob/main/README_ZH.md) | 日本語

<a href="https://trendshift.io/repositories/10079" target="_blank"><img src="https://trendshift.io/api/badge/repositories/10079" alt="modelscope%2Fagentscope | Trendshift" style="width: 250px; height: 55px;" width="250" height="55"/></a>

# AgentScope

<h1 align="left">
<img src="https://img.alicdn.com/imgextra/i2/O1CN01cdjhVE1wwt5Auv7bY_!!6000000006373-0-tps-1792-1024.jpg" width="600" alt="agentscope-logo">
</h1>

LLMを活用したマルチエージェントアプリケーションをより簡単に構築する。

[![](https://img.shields.io/badge/cs.MA-2402.14034-B31C1C?logo=arxiv&logoColor=B31C1C)](https://arxiv.org/abs/2402.14034)
[![](https://img.shields.io/badge/python-3.9+-blue)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/pypi-v0.1.3-blue?logo=pypi)](https://pypi.org/project/agentscope/)
[![](https://img.shields.io/badge/Docs-English%7C%E4%B8%AD%E6%96%87-blue?logo=markdown)](https://modelscope.github.io/agentscope/#welcome-to-agentscope-tutorial-hub)
[![](https://img.shields.io/badge/Docs-API_Reference-blue?logo=markdown)](https://modelscope.github.io/agentscope/)
[![](https://img.shields.io/badge/Docs-Roadmap-blue?logo=markdown)](https://github.com/modelscope/agentscope/blob/main/docs/ROADMAP.md)

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
| <img src="https://gw.alicdn.com/imgextra/i1/O1CN01hhD1mu1Dd3BWVUvxN_!!6000000000238-2-tps-400-400.png" width="100" height="100"> | <img src="https://img.alicdn.com/imgextra/i1/O1CN01LxzZha1thpIN2cc2E_!!6000000005934-2-tps-497-477.png" width="100" height="100"> |

----

## ニュース
- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-04-27]** 新しいAgentScope Studioが公開されました。詳細については[こちら](https://doc.agentscope.io/build_tutorial/visual.html)をご参照ください。

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-21]** AgentScope はフック関数をサポートしています。詳細は[チュートリアル](https://doc.agentscope.io/build_tutorial/hook.html)を参照してください。

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-19]** AgentScopeは現在、ツールAPIをサポートしています。詳しくは[チュートリアル](https://doc.agentscope.io/build_tutorial/tool.html)をご参照ください。

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-20]** Agentscopeは[MCP Server](https://github.com/modelcontextprotocol/servers)をサポートしました！[このチュートリアル](https://doc.agentscope.io/build_tutorial/MCP.html)を参考にして使い方を学ぶことができます。

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-03-05]** 私たちの[多情報源RAGアプリケーション](applications/multisource_rag_app/README.md)（DingTalkのQ&Aグループで使用されているチャットボット）がオープンソースになりました！

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-24]** [中国語版チュートリアル](https://doc.agentscope.io/zh_CN)が公開されました！

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-13]** [SWE-Bench(Verified)](https://www.swebench.com/) における我々の解決策の[技術報告書](https://doc.agentscope.io/tutorial/swe.html)を公開しました！

- <img src="https://img.alicdn.com/imgextra/i3/O1CN01SFL0Gu26nrQBFKXFR_!!6000000007707-2-tps-500-500.png" alt="new" width="30" height="30"/>**[2025-02-07]**🎉 AgentScope が SWE-bench(Verified) で 63.4%の解決率を達成しました！私たちのソリューションについての詳細は近日公開予定です。

- **[2025-01-04]** AgentScopeが現在Anthropic APIをサポートしています。

- **[2024-12-12]** AgentScopeの[ロードマップ](https://github.com/modelscope/agentscope/blob/main/docs/ROADMAP.md)を更新しました。

- **[2024-09-06]** AgentScopeバージョン0.1.0がリリースされました。

- **[2024-09-03]** AgentScopeは**Webブラウザ制御**をサポートしています。詳細については、[例](https://github.com/modelscope/agentscope/tree/main/examples/conversation_with_web_browser_agent)を参照してください。

<h5 align="left">
<video src="https://github.com/user-attachments/assets/6d03caab-6193-4ac6-8b1c-36f152ec02ec" width="45%" alt="web browser control" controls></video>
</h5>

[詳細情報](https://github.com/modelscope/agentscope/blob/main/docs/news_ja.md)

---

## AgentScopeとは？

AgentScopeは、開発者が大規模モデルを使用してマルチエージェントアプリケーションを構築する能力を提供する革新的なマルチエージェントプラットフォームです。
それは3つの高レベルの機能を備えています：

- 🤝 **使いやすさ**：開発者向けに設計されており、[豊富なコンポーネント](https://doc.agentscope.io/build_tutorial/tool.html#)、[包括的なドキュメント](https://doc.agentscope.io/index.html)、および広範な互換性を提供します。さらに、[AgentScope Workstation](https://agentscope.io/)は、初心者向けの*ドラッグアンドドロッププログラミングプラットフォーム*と*copilot*を提供します。

- ✅ **高い堅牢性**：カスタマイズ可能なフォールトトレランス制御と再試行メカニズムをサポートし、アプリケーションの安定性を向上させます。

- 🚀 **アクターベースの分散**：集中型プログラミング方式で分散マルチエージェントアプリケーションを構築し、開発を簡素化します。

**サポートされているモデルライブラリ**

AgentScopeは、ローカルモデルサービスとサードパーティのモデルAPIの両方をサポートするための`ModelWrapper`のリストを提供します。

| API                    | タスク            | モデルラッパー                                                                                                                   | 構成                                                                                                                                                                                                                  | サポートされているモデルの一部                                           |
|------------------------|-----------------|---------------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------------------------|
| OpenAI API             | チャット            | [`OpenAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                 | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_chat_template.json)            | gpt-4o, gpt-4, gpt-3.5-turbo, ...                               |
|                        | 埋め込み       | [`OpenAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)            | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_embedding_template.json)       | text-embedding-ada-002, ...                                     |
|                        | DALL·E          | [`OpenAIDALLEWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/openai_model.py)                | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/openai_dall_e_template.json)          | dall-e-2, dall-e-3                                              |
| DashScope API          | チャット            | [`DashScopeChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)           | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_chat_template.json)       | qwen-plus, qwen-max, ...                                        |
|                        | 画像生成 | [`DashScopeImageSynthesisWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py) | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_image_synthesis_template.json) | wanx-v1                                                         |
|                        | テキスト埋め込み  | [`DashScopeTextEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)  | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_text_embedding_template.json) | text-embedding-v1, text-embedding-v2, ...                       |
|                        | マルチモーダル      | [`DashScopeMultiModalWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/dashscope_model.py)     | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/dashscope_multimodal_template.json) | qwen-vl-max, qwen-vl-chat-v1, qwen-audio-chat                   |
| Gemini API             | チャット            | [`GeminiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)                 | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_chat_template.json)            | gemini-pro, ...                                                 |
|                        | 埋め込み       | [`GeminiEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/gemini_model.py)            | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/gemini_embedding_template.json)       | models/embedding-001, ...                                       |
| ZhipuAI API            | チャット            | [`ZhipuAIChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)                 | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_chat_template.json)             | glm-4, ...                                                      |
|                        | 埋め込み       | [`ZhipuAIEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/zhipu_model.py)            | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/zhipu_embedding_template.json)        | embedding-2, ...                                                |
| ollama                 | チャット            | [`OllamaChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)                 |[テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_chat_template.json)             | llama3, llama2, Mistral, ...                                    |
|                        | 埋め込み       | [`OllamaEmbeddingWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)            | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_embedding_template.json)       | llama2, Mistral, ...                                            |
|                        | 生成      | [`OllamaGenerationWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/ollama_model.py)           | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/ollama_generate_template.json)      | llama2, Mistral, ...                                            |
| LiteLLM API            | チャット            | [`LiteLLMChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/litellm_model.py)               | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/litellm_chat_template.json)         | [litellmがサポートするモデル](https://docs.litellm.ai/docs/)... |
| Yi API                 | チャット            | [`YiChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/yi_model.py)                         | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/yi_chat_template.json)         | yi-large, yi-medium, ...                                        |
| Post Request based API | -               | [`PostAPIModelWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/post_model.py)                 | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/postapi_model_config_template.json) | -                                                               |
| Anthropic API          | Chat            | [`AnthropicChatWrapper`](https://github.com/modelscope/agentscope/blob/main/src/agentscope/models/anthropic_model.py)           | [テンプレート](https://github.com/modelscope/agentscope/blob/main/examples/model_configs_template/anthropic_chat_model_config_template.json) | claude-3-5-sonnet-20241022, ... |

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

さまざまなデプロイメントシナリオをサポートするために、AgentScopeはいくつかのオプションの依存関係を提供します。オプションの依存関係の完全なリストは、[チュートリアル](https://doc.agentscope.io/build_tutorial/quickstart.html)を参照してください。分散モードを例にとると、次のように依存関係をインストールできます：

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

詳細については、[チュートリアル](https://doc.agentscope.io/build_tutorial/visual.html)を参照してください。

<h5 align="center">
<img src="https://img.alicdn.com/imgextra/i4/O1CN015kjnkd1xdwJoNxqLZ_!!6000000006467-0-tps-3452-1984.jpg" width="600" alt="agentscope-logo">
</h5>

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

## 貢献者 ✨

貢献者の皆様、ありがとうございました:

<a href="https://github.com/modelscope/agentscope/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=modelscope/agentscope&max=999&columns=12&anon=1" />
</a>