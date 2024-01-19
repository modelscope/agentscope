(205-memory)=

# Memory and Message Management

**Message** represents individual pieces of information or interactions flowing between/within agents. **Memory** refers to the storage and retrieval of historical information and serves as the storage and management system for the messages. This allows the agent to remember past interactions, maintain context, and provide more coherent and relevant responses.

## Understanding `MessageBase` and its subclasses

### `MessageBase`

`MessageBase` is designed to organize attributes of a message, like the agent's name, the content, and associated media URLs. It provides a structure that can be extended to create specific types of messages.

```python
class MessageBase(dict):
    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        self.id = uuid4().hex
        self.timestamp = timestamp or _get_timestamp()
        self.name = name
        self.content = content
        self.url = url
        self.update(kwargs)

    def to_str(self) -> str:
        raise NotImplementedError

    def serialize(self) -> str:
        raise NotImplementedError

    # ... [code omitted for brevity]
```

Here are the key attributes managed by the `MessageBase` class:

- **`name`**: This attribute denotes the originator of the message. It's a critical piece of metadata, useful in scenarios where distinguishing between different speakers is necessary.
- **`content`**: The substance of the message itself. It can include text, structured data, or any other form of content that is relevant to the interaction and requires processing by the agent.
- **`url`**: An optional attribute that allows the message to be linked to external resources. These can be direct links to files, multi-modal data, or web pages.
- **`timestamp`**: A timestamp indicating when the message was created.
- **`id`**: Each message is assigned a unique identifier (ID) upon creation.

### `Msg`

The `Msg` ("Message") subclass extends `MessageBase` and represents a standard *message*.  `Msg` provides concrete definitions for the `to_str` and `serialize` methods to enable string representation and serialization suitable for the agent's operational context.

```python
class Msg(MessageBase):
    # ... [code omitted for brevity]

    def to_str(self) -> str:
        return f"{self.name}: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Msg", **self})

# `Msg` logs
>> Someone: I should ...
```

### `Tht`

The `Tht` ("Thought") subclass is a specialized form of `MessageBase` used for encapsulating processes of an agent's internal thought. The thought is not sent outwardly but is instead used internally by the agent. As with `Msg`, specific implementations of `Tht` will define `to_str` and `serialize` methods to handle the unique requirements of representing and serializing an agent's thoughts.

```python
class Tht(MessageBase):
    # ... [code omitted for brevity]

    def to_str(self) -> str:
        return f"{self.name} thought: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Tht", **self})

>> Someone thought: I should ...
```

## Understanding `MemoryBase` and its subclasses

### `MemoryBase`

`MemoryBase` is an abstract class that handles an agent's memory in a structured way. It defines operations for storing, retrieving, deleting, and manipulating *message*'s content.

```python
class MemoryBase(ABC):
    # ... [code omitted for brevity]

    def get_memory(
        self,
        return_type: PromptType = PromptType.LIST,
        recent_n: Optional[int] = None,
        filter_func: Optional[Callable[[int, dict], bool]] = None,
    ) -> Union[list, str]:
        raise NotImplementedError

    def add(self, memories: Union[list[dict], dict]) -> None:
        raise NotImplementedError

    def delete(self, index: Union[Iterable, int]) -> None:
        raise NotImplementedError

    def load(
        self,
        memories: Union[str, dict, list],
        overwrite: bool = False,
    ) -> None:
        raise NotImplementedError

    def export(
        self,
        to_mem: bool = False,
        file_path: Optional[str] = None,
    ) -> Optional[list]:
        raise NotImplementedError

    def clear(self) -> None:
        raise NotImplementedError

    def size(self) -> int:
        raise NotImplementedError
```

Here are the key methods of `MemoryBase`:

- **`get_memory`**: This method is responsible for retrieving stored messages from the agent's memory. It can return these messages in different formats as specified by the `return_type`. The method can also retrieve a specific number of recent messages if `recent_n` is provided, and it can apply a filtering function (`filter_func`) to select messages based on custom criteria.
- **`add`**: This method is used to add a new *message* to the agent's memory. It can accept a single message or a list of messages. Each message is typically an instance of `MessageBase` or its subclasses.
- **`delete`**: This method enables the removal of messages from memory by their index (or indices if an iterable is provided).
- **`load`**: This method allows for the bulk loading of messages into the agent's memory from an external source. The `overwrite` parameter determines whether to clear the existing memory before loading the new set of messages.
- **`export`**: This method facilitates exporting the stored *message* from the agent's memory either to an external file (specified by `file_path`) or directly into the working memory of the program (if `to_mem` is set to `True`).
- **`clear`**: This method purges all *message* from the agent's memory, essentially resetting it.
- **`size`**: This method returns the number of messages currently stored in the agent's memory.

### `TemporaryMemory`

The `TemporaryMemory` class is a concrete implementation of `MemoryBase`, providing a memory store that exists during the runtime of an agent, which is used as the default memory type of agents. Besides all the behaviors from `MemoryBase`, the `TemporaryMemory` additionally provides methods for retrieval:

- **`retrieve_by_embedding`**: Retrieves `messages` that are most similar to a query, based on their embeddings. It uses a provided metric to determine the relevance and can return the top `k` most relevant messages.
- **`get_embeddings`**: Return the embeddings for all messages in memory. If a message does not have an embedding and an embedding model is provided, it will generate and store the embedding for the message.

For more details about the usage of `Memory` and `Msg`, please refer to the API references.

[[Return to the top]](#memory-and-message-management)
