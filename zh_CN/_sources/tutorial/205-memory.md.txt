(205-memory-zh)=

# 记忆

AgentScope中，记忆（memory）用于存储历史消息，从而使智能体能够根据上下文提供更加连贯，更加
自然的响应。
本教程将首先介绍memory中信息的载体，消息（message），然后介绍AgentScope中记忆模块的功能
和使用方法。

## 关于消息（Message）

### 消息基类（`MessageBase`）

AgentScope中，消息基类是Python字典的子类，由`name`，`content`两个必选字段和一个可选的字段
`url`组成。由于是字典类型，开发者也可以根据需要增加其他字段。
其中，`name`字段代表消息的发起者，`content`字段代表消息的内容，`url
`则代表消息中附加的数据链接，可以是指向多模态数据的本地链接，也可以是网络链接。
当一个消息被创建时，将会自动创建一个唯一的ID，用于标识这条消息。同时，消息的创建时间也会以
时间戳的形式自动记录下来。

具体实现中，AgentScope首先提供了一个`MessageBase`基类，用于定义消息的基本属性和使用方法。
与一般的字典类型不同，`MessageBase`的实例化对象可以通过`对象名.{属性名}`的方式访问属性值，
也可以通过`对象名['属性名']`的方式访问属性值。
其中，`MessageBase` 类的关键属性如下：

- **`name`**：该属性表示信息的发起者。这是一项关键的元数据，在需要区分不同发言者的场景中非常有用。
- **`content`**：信息本身的内容。它可以包括文本、结构化数据或其他与交互相关且需要智能体处理的内容形式。
- **`url`**：可选属性，允许信息链接到外部资源。这些可以是指向文件的直接链接、多模态数据或网页。
- **`timestamp`**：时间戳，显示信息创建的时间。
- **`id`**：每条信息在创建时都会被分配一个唯一标识符（ID）。

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

### 消息类（`Msg`）

`Msg`类是AgentScope中最常用的消息类。它继承了 `MessageBase`类，并实现了`to_str` 和
`serialize` 抽象方法。
在一个Agent类中，其`reply`函数通常会返回一个`Msg`类的实例，以便在AgentScope中进行消息的
传递。

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

## 关于记忆（Memory）

### 关于记忆基类（`MemoryBase`）

`MemoryBase` 是一个抽象类，以结构化的方式处理智能体的记忆。它定义了存储、检索、删除和操作
*信息*内容的操作。

```python
class MemoryBase(ABC):
    # ... [省略代码以简化]

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

以下是 `MemoryBase` 的关键方法：

- **`get_memory`**：这个方法负责从智能体的记忆中检索存储的信息。它可以按照 `return_type` 指定的格式返回这些信息。该方法还可以在提供 `recent_n` 时检索特定数量的最近信息，并且可以应用过滤函数（ `filter_func` ）来根据自定义标准选择信息。
- **`add`**：这个方法用于将新的信息添加到智能体的记忆中。它可以接受单个信息或信息列表。每条信息通常是 `MessageBase` 或其子类的实例。
- **`delete`**：此方法允许通过信息的索引（如果提供可迭代对象，则为索引集合）从记忆中删除信息。
- **`load`**：这个方法允许从外部来源批量加载信息到智能体的内存中。`overwrite` 参数决定是否在加载新的信息集之前清除现有记忆。
- **`export`**：这个方法便于将存储的*信息*从智能体的记忆中导出，要么导出到一个外部文件（由 `file_path` 指定），要么直接导入到程序的运行内存中（如果 `to_mem` 设置为 `True` ）。
- **`clear`**：这个方法清除智能体记忆中的所有*信息*，本质上是重置。
- **`size`**：这个方法返回当前存储在智能体记忆中的信息数量。

### 关于`TemporaryMemory`

`TemporaryMemory` 类是 `MemoryBase` 类的一个具体实现，提供了一个智能体运行期间存在的记忆存储，被用作智能体的默认记忆类型。除了 `MemoryBase` 的所有行为外，`TemporaryMemory` 还提供了检索的方法：

- **`retrieve_by_embedding`**：基于它们的嵌入向量 (embeddings) 检索与查询最相似的 `messages`。它使用提供的度量标准来确定相关性，并可以返回前 `k` 个最相关的信息。
- **`get_embeddings`**：返回记忆中所有信息的嵌入向量。如果信息没有嵌入向量，并且提供了嵌入模型，它将生成并存储信息的嵌入向量。

有关 `Memory` 和 `Msg` 使用的更多细节，请参考 API 文档。

[[返回顶端]](#205-memory-zh)
