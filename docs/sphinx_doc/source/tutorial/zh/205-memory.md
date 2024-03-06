(205-memory)=

# 信息和记忆管理

**信息（message）**代表智能体之间或智能体内部传递的单个信息片段或交互。**记忆（memory）**指历史信息的存储和检索，是信息的存储和管理系统。这使智能体能够记住过去的互动信息，保持上下文关联，以提供更连贯、更相关的响应。

## 理解 `MessageBase` 及其子类

### `MessageBase`

`MessageBase ` 旨在组织信息的属性，如智能体名字、内容和相关媒体 URL，它提供了一种可扩展的结构，用于创建特定类型的信息。

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

    # ... [省略代码以简化]
```

 `MessageBase` 类的关键属性如下：

- **`name`**：该属性表示信息的发起者。这是一项关键的元数据，在需要区分不同发言者的场景中非常有用。
- **`content`**：信息本身的内容。它可以包括文本、结构化数据或其他与交互相关且需要智能体处理的内容形式。
- **`url`**：可选属性，允许信息链接到外部资源。这些可以是指向文件的直接链接、多模态数据或网页。
- **`timestamp`**：时间戳，显示信息创建的时间。
- **`id`**：每条信息在创建时都会被分配一个唯一标识符（ID）。

### `Msg`

 `Msg` （"Message"）子类扩展了 `MessageBase` ，代表了一个标准的*信息*。`Msg` 提供了对 `to_str` 和 `serialize` 方法的具体定义，以便于字符串表示和序列化，适合智能体对上下文的操作。

```python
class Msg(MessageBase):
    # ... [省略代码以简化]

    def to_str(self) -> str:
        return f"{self.name}: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Msg", **self})

# `Msg` 日志
>> Someone: I should ...
```

### `Tht`

`Tht`（"Thought"）子类是 `MessageBase` 的一种特殊形式，用于封装智能体内部思考的过程。思考不向外发送，而是智能体内部使用。与 `Msg` 一样，特定的 `Tht` 实现将定义 `to_str` 和 `serialize` 方法，来处理对智能体思考内容的字符串表示和序列化的独特需求。

```python
class Tht(MessageBase):
    # ... [省略代码以简化]

    def to_str(self) -> str:
        return f"{self.name} thought: {self.content}"

    def serialize(self) -> str:
        return json.dumps({"__type": "Tht", **self})

>> Someone thought: I should ...
```

## 理解 `MemoryBase` 及其子类

### `MemoryBase`

`MemoryBase` 是一个抽象类，以结构化的方式处理智能体的记忆。它定义了存储、检索、删除和操作*信息*内容的操作。

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
- **`load`**：这个方法允许从外部来源批量加载信息到智能体的内存中。`overwrite ` 参数决定是否在加载新的信息集之前清除现有记忆。
- **`export`**：这个方法便于将存储的*信息*从智能体的记忆中导出，要么导出到一个外部文件（由 `file_path` 指定），要么直接导入到程序的运行内存中（如果 `to_mem` 设置为 `True` ）。
- **`clear`**：这个方法清除智能体记忆中的所有*信息*，本质上是重置。
- **`size`**：这个方法返回当前存储在智能体记忆中的信息数量。

### `TemporaryMemory`

`TemporaryMemory ` 类是 `MemoryBase` 类的一个具体实现，提供了一个智能体运行期间存在的记忆存储，被用作智能体的默认记忆类型。除了 `MemoryBase` 的所有行为外，`TemporaryMemory ` 还提供了检索的方法：

- **`retrieve_by_embedding`**：基于它们的嵌入向量 (embeddings) 检索与查询最相似的 `messages`。它使用提供的度量标准来确定相关性，并可以返回前 `k` 个最相关的信息。
- **`get_embeddings`**：返回记忆中所有信息的嵌入向量。如果信息没有嵌入向量，并且提供了嵌入模型，它将生成并存储信息的嵌入向量。

有关 `Memory` 和 `Msg` 使用的更多细节，请参考 API 文档。

[[返回顶端]](#信息和记忆管理)
