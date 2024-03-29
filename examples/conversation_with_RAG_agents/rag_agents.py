# -*- coding: utf-8 -*-
"""
This example shows how to build an agent with RAG
with LlamaIndex.

Notice, this is a Beta version of RAG agent.
"""

from abc import ABC, abstractmethod
from typing import Optional, Any
import importlib
from loguru import logger

from rag import RAGBase, LlamaIndexRAG

from agentscope.agents.agent import AgentBase
from agentscope.message import Msg
from agentscope.models import load_model_by_config_name


class RAGAgentBase(AgentBase, ABC):
    """
    Base class for RAG agents
    """

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        emb_model_config_name: str,
        memory_config: Optional[dict] = None,
        rag_config: Optional[dict] = None,
    ) -> None:
        """
        Initialize the RAG base agent
        Args:
            name (str):
                the name for the agent.
            sys_prompt (str):
                system prompt for the RAG agent.
            model_config_name (str):
                language model for the agent.
            emb_model_config_name (str):
                embedding model for the agent.
            memory_config (dict):
                memory configuration.
            rag_config (dict):
                config for RAG. It contains most of the
                important parameters for RAG modules. If not provided,
                the default setting will be used.
                Examples can refer to children classes.
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            use_memory=True,
            memory_config=memory_config,
        )
        # setup embedding model used in RAG
        self.emb_model = load_model_by_config_name(emb_model_config_name)

        self.rag_config = rag_config or {}
        if "log_retrieval" not in self.rag_config:
            self.rag_config["log_retrieval"] = True

        # use LlamaIndexAgent OR LangChainAgent
        self.rag = self.init_rag()

    @abstractmethod
    def init_rag(self) -> RAGBase:
        """initialize RAG with configuration"""

    def _prepare_args_from_config(
        self,
        config: dict,
    ) -> Any:
        """
        Helper function to build args for the two functions:
        rag.load_data(...) and rag.store_and_index(docs, ...)
        in RAG classes.
        Args:
            config (dict): a dictionary containing configurations

        Returns:
            Any: an object that is parsed/built to be an element
                of input to the function of RAG module.
        """
        if not isinstance(config, dict):
            return config

        if "create_object" in config:
            # if a term in args is a object,
            # recursively create object with args from config
            module_name = config.get("module", "")
            class_name = config.get("class", "")
            init_args = config.get("init_args", {})
            try:
                cur_module = importlib.import_module(module_name)
                cur_class = getattr(cur_module, class_name)
                init_args = self._prepare_args_from_config(init_args)
                logger.info(
                    f"load and build object{cur_module, cur_class, init_args}",
                )
                return cur_class(**init_args)
            except ImportError as exc_inner:
                logger.error(
                    f"Fail to load class {class_name} "
                    f"from module {module_name}",
                )
                raise ImportError(
                    f"Fail to load class {class_name} "
                    f"from module {module_name}",
                ) from exc_inner
        else:
            prepared_args = {}
            for key, value in config.items():
                if isinstance(value, list):
                    prepared_args[key] = []
                    for c in value:
                        prepared_args[key].append(
                            self._prepare_args_from_config(c),
                        )
                elif isinstance(value, dict):
                    prepared_args[key] = self._prepare_args_from_config(value)
                else:
                    prepared_args[key] = value
            return prepared_args

    def reply(
        self,
        x: dict = None,
    ) -> dict:
        """
        Reply function of the RAG agent.
        Processes the input data,
        1) use the input data to retrieve with RAG function;
        2) generates a prompt using the current memory and system
        prompt;
        3) invokes the language model to produce a response. The
        response is then formatted and added to the dialogue memory.

        Args:
            x (`dict`, defaults to `None`):
                A dictionary representing the user's input to the agent. This
                input is added to the memory if provided. Defaults to
                None.
        Returns:
            A dictionary representing the message generated by the agent in
            response to the user's input.
        """
        retrieved_docs_to_string = ""
        # record the input if needed
        if self.memory:
            self.memory.add(x)
            # in case no input is provided (e.g., in msghub),
            # use the memory as query
            history = self.memory.get_memory(
                recent_n=self.rag_config.get("recent_n_mem", 1),
            )
            query = (
                "/n".join(
                    [msg["content"] for msg in history],
                )
                if isinstance(history, list)
                else str(history)
            )
        elif x is not None:
            query = x["content"]
        else:
            query = ""

        if len(query) > 0:
            # when content has information, do retrieval
            retrieved_docs = self.rag.retrieve(query, to_list_strs=True)
            for content in retrieved_docs:
                retrieved_docs_to_string += "\n>>>> " + content

            if self.rag_config["log_retrieval"]:
                self.speak("[retrieved]:" + retrieved_docs_to_string)

        # prepare prompt
        prompt = self.model.format(
            Msg(
                name="system",
                role="system",
                content=self.sys_prompt,
            ),
            # {"role": "system", "content": retrieved_docs_to_string},
            self.memory.get_memory(
                recent_n=self.rag_config.get("recent_n_mem", 1),
            ),
            Msg(
                name="user",
                role="user",
                content="Context: " + retrieved_docs_to_string,
            ),
        )

        # call llm and generate response
        response = self.model(prompt).text
        msg = Msg(self.name, response)

        # Print/speak the message in this agent's voice
        self.speak(msg)

        if self.memory:
            # Record the message in memory
            self.memory.add(msg)

        return msg


class LlamaIndexAgent(RAGAgentBase):
    """
    A LlamaIndex agent build on LlamaIndex.
    """

    def __init__(
        self,
        name: str,
        sys_prompt: str,
        model_config_name: str,
        emb_model_config_name: str = None,
        memory_config: Optional[dict] = None,
        rag_config: Optional[dict] = None,
    ) -> None:
        """
        Initialize the RAG LlamaIndexAgent
        Args:
            name (str):
                the name for the agent
            sys_prompt (str):
                system prompt for the RAG agent
            model_config_name (str):
                language model for the agent
            emb_model_config_name (str):
                embedding model for the agent
            memory_config (dict):
                memory configuration
            rag_config (dict):
                config for RAG. It contains the parameters for
                RAG modules functions:
                rag.load_data(...) and rag.store_and_index(docs, ...)
                 If not provided, the default setting will be used.
                An example of the config for retrieving code files
                is as following:

                "rag_config": {
                    "load_data": {
                      "loader": {
                        "create_object": true,
                        "module": "llama_index.core",
                        "class": "SimpleDirectoryReader",
                        "init_args": {
                          "input_dir": "path/to/data",
                          "recursive": true
                          ...
                        }
                      }
                    },
                    "store_and_index": {
                      "transformations": [
                        {
                          "create_object": true,
                          "module": "llama_index.core.node_parser",
                          "class": "CodeSplitter",
                          "init_args": {
                            "language": "python",
                            "chunk_lines": 100
                          }
                        }
                      ]
                    },
                    "chunk_size": 2048,
                    "chunk_overlap": 40,
                    "similarity_top_k": 10,
                    "log_retrieval": true,
                    "recent_n_mem": 1
               }
        """
        super().__init__(
            name=name,
            sys_prompt=sys_prompt,
            model_config_name=model_config_name,
            emb_model_config_name=emb_model_config_name,
            memory_config=memory_config,
            rag_config=rag_config,
        )

    def init_rag(self) -> LlamaIndexRAG:
        # dynamic loading loader
        # init rag related attributes
        rag = LlamaIndexRAG(
            model=self.model,
            emb_model=self.emb_model,
            config=self.rag_config,
        )
        # load the document to memory
        # Feed the AgentScope tutorial documents, so that
        # the agent can answer questions related to AgentScope!
        if "load_data" in self.rag_config:
            load_data_args = self._prepare_args_from_config(
                self.rag_config["load_data"],
            )
        else:
            try:
                from llama_index.core import SimpleDirectoryReader
            except ImportError as exc_inner:
                raise ImportError(
                    " LlamaIndexAgent requires llama-index to be install."
                    "Please run `pip install llama-index`",
                ) from exc_inner
            load_data_args = {
                "loader": SimpleDirectoryReader(self.config["data_path"]),
            }
        logger.info(f"rag.load_data args: {load_data_args}")
        docs = rag.load_data(**load_data_args)

        # store and indexing
        if "store_and_index" in self.rag_config:
            store_and_index_args = self._prepare_args_from_config(
                self.rag_config["store_and_index"],
            )
        else:
            store_and_index_args = {}

        logger.info(f"store_and_index_args args: {store_and_index_args}")
        rag.store_and_index(docs, **store_and_index_args)

        return rag
