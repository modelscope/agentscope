(202-pipeline-en)=

# Pipeline and MsgHub

**Pipeline & MsgHub** (message hub) are one or a sequence of steps describing how the structured `Msg` passes between multi-agents, which streamlines the process of collaboration across agents.

`Pipeline` allows users to program communication among agents easily, and `MsgHub` enables message sharing among agents like a group chat.

## Pipelines

`Pipeline` in AgentScope serves as conduits through which messages pass among agents. In AgentScope, an `Agent` is a subclass of an `Operator` that performs some operation on input data. Pipelines extend this concept by encapsulating multiple agents, and also act as an `Operator`.

Here is the base class for all pipeline types:

```python
class PipelineBase(Operator):
   """Base interface of all pipelines."""
    # ... [code omitted for brevity]
    @abstractmethod
    def __call__(self, x: Optional[dict] = None) -> dict:
        """Define the actions taken by this pipeline.

        Args:
            x (Optional[`dict`], optional):
                Dialog history and some environmental information

        Returns:
            `dict`: The pipeline's response to the input.
        """
```

### Category

AgentScope provides two main types of pipelines based on their implementation strategy:

* **Operator-Type Pipelines**

  * These pipelines are object-oriented and inherit from the `PipelineBase`. They are operators themselves and can be combined with other operators to create complex interaction patterns.

    ```python
    # Instantiate and invoke
    pipeline = ClsPipeline(agent1, agent2, agent3)
    x = pipeline(x)
    ```

* **Functional Pipelines**

  * Functional pipelines provide similar control flow mechanisms as the class-based pipelines but are implemented as standalone functions. These are useful for scenarios where a class-based setup may not be necessary or preferred.

    ```python
    # Just invoke
    x = funcpipeline(agent1, agent2, agent3, x)
    ```

Pipelines are categorized based on their functionality, much like programming language constructs. The table below outlines the different pipelines available in AgentScope:

| Operator-Type Pipeline    | Functional Pipeline  | Description                                                  |
| -------------------- | -------------------- | ------------------------------------------------------------ |
| `SequentialPipeline` | `sequentialpipeline` | Executes a sequence of operators in order, passing the output of one as the input to the next. |
| `IfElsePipeline`     | `ifelsepipeline`     | Implements conditional logic, executing one operator if a condition is true and another if it is false. |
| `SwitchPipeline`     | `switchpipeline`     | Facilitates multi-branch selection, executing an operator from a mapped set based on the evaluation of a condition. |
| `ForLoopPipeline`    | `forlooppipeline`    | Repeatedly executes an operator for a set number of iterations or until a specified break condition is met. |
| `WhileLoopPipeline`  | `whilelooppipeline`  | Continuously executes an operator as long as a given condition remains true. |
| -                    | `placeholder`        | Acts as a placeholder in branches that do not require any operations in flow control like if-else/switch |

### Usage

This section illustrates how pipelines can simplify the implementation of logic in multi-agent applications by comparing the usage of pipelines versus approaches without pipelines.

**Note：** Please note that in the examples provided below, we use the term `agent` to represent any instance that can act as an `Operator`. This is for ease of understanding and to illustrate how pipelines orchestrate interactions between different operations. You can replace `agent` with any `Operator`, thus allowing for a mix of `agent` and `pipeline` in practice.

#### `SequentialPipeline`

* Without pipeline:

  ```python
  x = agent1(x)
  x = agent2(x)
  x = agent3(x)
  ```

* Using pipeline:

  ```python
  from agentscope.pipelines import SequentialPipeline

  pipe = SequentialPipeline([agent1, agent2, agent3])
  x = pipe(x)
  ```

* Using functional pipeline:

  ```python
  from agentscope.pipelines import sequentialpipeline

  x = sequentialpipeline([agent1, agent2, agent3], x)
  ```

#### `IfElsePipeline`

* Without pipeline:

  ```python
  if condition(x):
      x = agent1(x)
  else:
      x = agent2(x)
  ```

* Using pipeline:

  ```python
  from agentscope.pipelines import IfElsePipeline

  pipe = IfElsePipeline(condition, agent1, agent2)
  x = pipe(x)
  ```

* Using functional pipeline:

  ```python
  from agentscope.functional import ifelsepipeline

  x = ifelsepipeline(condition, agent1, agent2, x)
  ```

#### `SwitchPipeline`

* Without pipeline:

  ```python
  switch_result = condition(x)
  if switch_result == case1:
      x = agent1(x)
  elif switch_result == case2:
      x = agent2(x)
  else:
      x = default_agent(x)
  ```

* Using pipeline:

  ```python
  from agentscope.pipelines import SwitchPipeline

  case_operators = {case1: agent1, case2: agent2}
  pipe = SwitchPipeline(condition, case_operators, default_agent)
  x = pipe(x)
  ```

* Using functional pipeline:

  ```python
  from agentscope.functional import switchpipeline

  case_operators = {case1: agent1, case2: agent2}
  x = switchpipeline(condition, case_operators, default_agent, x)
  ```

#### `ForLoopPipeline`

* Without pipeline:

  ```python
  for i in range(max_iterations):
      x = agent(x)
      if break_condition(x):
          break
  ```

* Using pipeline:

  ```python
  from agentscope.pipelines import ForLoopPipeline

  pipe = ForLoopPipeline(agent, max_iterations, break_condition)
  x = pipe(x)
  ```

* Using functional pipeline:

  ```python
  from agentscope.functional import forlooppipeline

  x = forlooppipeline(agent, max_iterations, break_condition, x)
  ```

#### `WhileLoopPipeline`

* Without pipeline:

    ```python
    while condition(x):
        x = agent(x)
    ```

* Using pipeline:

    ```python
    from agentscope.pipelines import WhileLoopPipeline

    pipe = WhileLoopPipeline(agent, condition)
    x = pipe(x)
    ```

* Using functional pipeline:

    ```python
    from agentscope.functional import whilelooppipeline

    x = whilelooppipeline(agent, condition, x)
    ```

### Pipeline Combination

It's worth noting that AgentScope supports the combination of pipelines to create complex interactions. For example, we can create a pipeline that executes a sequence of agents in order, and then executes another pipeline that executes a sequence of agents in condition.

```python
from agentscope.pipelines import SequentialPipeline, IfElsePipeline
# Create a pipeline that executes agents in order
pipe1 = SequentialPipeline([agent1, agent2, agent3])
# Create a pipeline that executes agents in ifElsePipeline
pipe2 = IfElsePipeline(condition, agent4, agent5)
# Create a pipeline that executes pipe1 and pipe2 in order
pipe3 = SequentialPipeline([pipe1, pipe2])
# Invoke the pipeline
x = pipe3(x)
```

## MsgHub

`MsgHub` is designed to manage dialogue among a group of agents, allowing for the sharing of messages. Through `MsgHub`, agents can broadcast messages to all other agents in the group with `broadcast`.

Here is the core class for a `MsgHub`:

```python
class MsgHubManager:
    """MsgHub manager class for sharing dialog among a group of agents."""
    # ... [code omitted for brevity]

    def broadcast(self, msg: Union[dict, list[dict]]) -> None:
        """Broadcast the message to all participants."""
        for agent in self.participants:
            agent.observe(msg)

    def add(self, new_participant: Union[Sequence[AgentBase], AgentBase]) -> None:
       """Add new participant into this hub"""
        # ... [code omitted for brevity]

    def delete(self, participant: Union[Sequence[AgentBase], AgentBase]) -> None:
       """Delete agents from participant."""
        # ... [code omitted for brevity]
```

### Usage

#### Creating a MsgHub

To create a `MsgHub`, instantiate a `MsgHubManager` by calling the `msghub` helper function with a list of participating agents. Additionally, you can supply an optional initial announcement that, if provided, will be broadcast to all participants upon initialization.

```python
from agentscope.msg_hub import msghub

# Initialize MsgHub with participating agents
hub_manager = msghub(
    participants=[agent1, agent2, agent3], announcement=initial_announcement
)
```

#### Broadcast  message in MsgHub

The `MsgHubManager` can be used with a context manager to handle the setup and teardown of the message hub environment:

```python
with msghub(
    participants=[agent1, agent2, agent3], announcement=initial_announcement
) as hub:
    # Agents can now broadcast and receive messages within this block
    agent1()
    agent2()

    # Or manually broadcast a message
    hub.broadcast(some_message)

```

Upon exiting the context block, the `MsgHubManager` ensures that each agent's audience is cleared, preventing any unintended message sharing outside of the hub context.

#### Adding and Deleting Participants

You can dynamically add or remove agents from the `MsgHub`:

```python
# Add a new participant
hub.add(new_agent)

# Remove an existing participant
hub.delete(existing_agent)
```

[[Return to the top]](#202-pipeline-en)
