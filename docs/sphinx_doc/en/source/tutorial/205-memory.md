(205-memory-en)=

# Memory

In AgentScope, memory is used to store historical information, allowing the
agent to provide more coherent and natural responses based on context.
This tutorial will first introduce the carrier of information in memory,
message, and then introduce the functions and usage of the memory module in
AgentScope.

## About Message

### `MessageBase` Class

In AgentScope, the message base class is a subclass of Python dictionary,
consisting of two required fields (`name` and `content`) and an optional
field (`url`).
Specifically, the `name` field represents the originator of the message,
the `content` field represents the content of the message, and the `url`
field represents the data link attached to the message, which can be a
local link to multi-modal data or a web link.
As a dictionary type, developers can also add other fields
as needed. When a message is created, a unique ID is automatically
generated to identify the message. The creation time of the message is also
automatically recorded in the form of a timestamp.

In the specific implementation, AgentScope first provides a `MessageBase`
base class to define the basic properties and usage of messages.
Unlike general dictionary types, the instantiated objects of `MessageBase`
can access attribute values through `object_name.{attribute_name}` or
`object_name['attribute_name']`.
The key attributes of the `MessageBase` class are as follows:

- **`name`**: This attribute denotes the originator of the message. It's a critical piece of metadata, useful in scenarios where distinguishing between different speakers is necessary.
- **`content`**: The substance of the message itself. It can include text, structured data, or any other form of content that is relevant to the interaction and requires processing by the agent.
- **`url`**: An optional attribute that allows the message to be linked to external resources. These can be direct links to files, multi-modal data, or web pages.
- **`timestamp`**: A timestamp indicating when the message was created.
- **`id`**: Each message is assigned a unique identifier (ID) upon creation.

```python
class MessageBase(dict):
    """Base Message class, which is used to maintain information for dialog,
    memory and used to construct prompt.
    """

    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the message object

        Args:
            name (`str`):
                The name of who send the message. It's often used in
                role-playing scenario to tell the name of the sender.
                However, you can also only use `role` when calling openai api.
                The usage of `name` refers to
                https://cookbook.openai.com/examples/how_to_format_inputs_to_chatgpt_models.
            content (`Any`):
                The content of the message.
            url (`Optional[Union[list[str], str]]`, defaults to None):
                A url to file, image, video, audio or website.
            timestamp (`Optional[str]`, defaults to None):
                The timestamp of the message, if None, it will be set to
                current time.
            **kwargs (`Any`):
                Other attributes of the message. For OpenAI API, you should
                add "role" from `["system", "user", "assistant", "function"]`.
                When calling OpenAI API, `"role": "assistant"` will be added
                to the messages that don't have "role" attribute.

        """
        # id and timestamp will be added to the object as its attributes
        # rather than items in dict
        self.id = uuid4().hex
        if timestamp is None:
            self.timestamp = _get_timestamp()
        else:
            self.timestamp = timestamp

        self.name = name
        self.content = content

        if url:
            self.url = url

        self.update(kwargs)

    def __getattr__(self, key: Any) -> Any:
        try:
            return self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def __setattr__(self, key: Any, value: Any) -> None:
        self[key] = value

    def __delattr__(self, key: Any) -> None:
        try:
            del self[key]
        except KeyError as e:
            raise AttributeError(f"no attribute '{key}'") from e

    def to_str(self) -> str:
        """Return the string representation of the message"""
        raise NotImplementedError

    def serialize(self) -> str:
        """Return the serialized message."""
        raise NotImplementedError

    # ... [省略代码以简化]
```

### `Msg` Class

`Msg` class extends `MessageBase` and represents a standard *message*.
`Msg` provides concrete definitions for the `to_str` and `serialize`
methods to enable string representation and serialization suitable for the
agent's operational context.
Within an `Agent` class, its `reply` function typically returns an instance of
`Msg` to facilitate message passing within AgentScope.

```python
class Msg(MessageBase):
    """The Message class."""

    def __init__(
        self,
        name: str,
        content: Any,
        url: Optional[Union[Sequence[str], str]] = None,
        timestamp: Optional[str] = None,
        echo: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            name=name,
            content=content,
            url=url,
            timestamp=timestamp,
            **kwargs,
        )
        if echo:
            logger.chat(self)

    def to_str(self) -> str:
        """Return the string representation of the message"""
        return f"{self.name}: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Msg", **self})
```

## About Memory

### `MemoryBase` Class

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

[[Return to the top]](#205-memory-en)
