# News

- **[2024-07-18]** AgentScopeはストリーミングモードをサポートしています。詳細については、[チュートリアル](https://modelscope.github.io/agentscope/en/tutorial/203-stream.html)および[ストリーミングモードでの会話の例](https://github.com/modelscope/agentscope/tree/main/examples/conversation_in_stream_mode)を参照してください。

<h5 align="left">
<img src="https://github.com/user-attachments/assets/b14d9b2f-ce02-4f40-8c1a-950f4022c0cc" width="45%" alt="agentscope-logo">
<img src="https://github.com/user-attachments/assets/dfffbd1e-1fe7-49ee-ac11-902415b2b0d6" width="45%" alt="agentscope-logo">
</h5>

- **[2024-07-15]** AgentScopeはMixture-of-Agentsアルゴリズムを実装しました。詳細については、[MoAの例](https://github.com/modelscope/agentscope/blob/main/examples/conversation_mixture_of_agents)を参照してください。

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