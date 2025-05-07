# Roadmap

## Long-term Goals

Offering **agent-oriented programming (AOP)** as a new programming model to organize the design and implementation of next-generation LLM-empowered applications.

## Short-term Goals

1. Refine and improve the documentation for easier understanding.
2. Support tools API.
3. Refactor the current AgentScope studio, including Dashboard and Workstation.
4. Improve the current RAG module.
5. Re-factor the `AgentBase` class to support more flexible serialization.

## Task

1. Documentation

 - ✅ Re-write the tutorial.
 - 📝 Correct the typographical errors in API documents.
 - 🚧 Refine the README.md.

2. Tools Calling

 - ✅ Add Support for Anthropic API.

 - 🚧 Support tools calling in user-assistant conversations.
   - ✅ OpenAI API
   - ✅ DashScope API
   - ✅ Anthropic API
   - 📝 Gemini APi

 - 📝 Support tools calling in multi-agent conversations.
   - OpenAI API
   - DashScope API
   - Anthropic API
   - Gemini API

> 💡**Note:** The most difficult part of supporting tools calling in multi-agent conversations is most LLM APIs only support
> `"user"` and `"assistant"` in their role fields, and has special requirements (e.g. user and assistant messages must be alternated).
> We are working on a solution to be compatible with tools calling in
> multi-agent conversations. If you have any ideas, please let us know. Discord | Dingtalk | GitHub issue are all welcome 🤗! Thanks in advance!

 - 📝 Support tools calling in streaming mode.
   - OpenAI API
   - DashScope API
   - Anthropic API
   - Gemini API

3. AgentScope Studio

 - 🚧 Refactor the AgentScope Workstation with React.
 - 📝 Refactor the AgentScope Dashboard with React.
   - Support websocket re-connection.
   - Support displaying token usage.
   - Support displaying real-time memory of agents.

4. RAG

 - 🚧 Provide a set of query rewrite strategies for retrieval.
 - ✅ Support online search engine (Google/Bing search) based RAG.
 - 🚧 Support multi-RAG agent routing efficiently.

5. AgentBase

 - 🚧 Decouple the data and service layer of the `MemoryBase` class to support more customized implementations.
 - 📝 Provide a new base class `Serializable` to
   - support automatic serialization/deserialization of agents.
   - support state registration
