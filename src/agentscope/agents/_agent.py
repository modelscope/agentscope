# -*- coding: utf-8 -*-
# pylint: disable=protected-access, too-many-public-methods
""" Base class for Agent """

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from functools import wraps
from types import GeneratorType
from typing import Optional, Generator, Tuple, Callable, Dict
from typing import Sequence
from typing import Union
from typing import Any
import json
import uuid
from loguru import logger

from ..rpc.rpc_config import DistConf
from ..rpc.rpc_meta import RpcMeta, async_func, sync_func
from ..logging import log_stream_msg, log_msg
from ..manager import ModelManager
from ..message import Msg, ToolUseBlock, TextBlock
from ..memory import TemporaryMemory


class _HooksMeta(type):
    """The hooks metaclass for all agents."""

    def __new__(mcs, name: Any, bases: Any, attrs: Dict) -> Any:
        """Wrap the `reply` and `observe` function with hooks."""
        if "reply" in attrs:
            original_reply = attrs["reply"]

            @wraps(original_reply)
            def wrapped_reply(
                self: AgentBase,
                x: Optional[Union[Msg, list[Msg]]] = None,
            ) -> Union[Union[Msg, list[Msg]], None]:
                # Pre hooks
                current_input = x
                for _, hook in self._hooks_pre_reply.items():
                    hook_result = hook(self, deepcopy(current_input))
                    if hook_result is not None:
                        current_input = hook_result

                # Original function
                reply_result = original_reply(self, current_input)

                # Post hooks
                current_output = reply_result
                for _, hook in self._hooks_post_reply.items():
                    hook_result = hook(self, deepcopy(current_output))
                    if hook_result is not None:
                        current_output = hook_result

                return current_output

            attrs["reply"] = wrapped_reply

        if "observe" in attrs:
            original_observe = attrs["observe"]

            @wraps(original_observe)
            def wrapped_observe(
                self: AgentBase,
                x: Union[Msg, list[Msg]],
            ) -> None:
                # Pre hooks
                current_input = deepcopy(x)
                for _, hook in self._hooks_pre_observe.items():
                    hook_result = hook(self, deepcopy(current_input))
                    if hook_result is not None:
                        current_input = hook_result

                # Original function
                original_observe(self, current_input)

                # Post hooks
                for _, hook in self._hooks_post_observe.items():
                    hook(self)  # type: ignore[call-arg]

            attrs["observe"] = wrapped_observe

        return super().__new__(mcs, name, bases, attrs)


class _AgentMeta(_HooksMeta, RpcMeta):
    """The combined metaclass for all agents.

    TODO: The RpcMeta will be deprecated in the future.
    """

    def __new__(mcs, name: Any, bases: Any, attrs: Dict) -> Any:
        """Add hooks to the agent class."""
        # First apply HooksMeta
        _HooksMeta.__new__(mcs, name, bases, attrs)
        # Then apply RpcMeta
        return RpcMeta.__new__(mcs, name, bases, attrs)


class AgentBase(metaclass=_AgentMeta):
    """Base class for all agents.

    All agents should inherit from this class and implement the `reply`
    function.
    """

    _version: int = 1

    _hooks_pre_reply: dict[
        str,
        Callable[
            [
                AgentBase,
                Union[Msg, list[Msg], None],
            ],
            Union[Msg, list[Msg], None],
        ],
    ] = OrderedDict()
    """The hooks function that will be called before the reply function, which
    takes the `self` object and a deep copied input message(s) as input. If
    the return of the hook is not `None`, the new output will be passed to the
    next hook or the original reply function. Otherwise, the original input
    will be passed instead."""

    _hooks_post_reply: dict[
        str,
        Callable[[AgentBase, Msg], Union[Msg, None]],
    ] = OrderedDict()
    """The hooks function that will be called after the reply function, which
    takes the `self` object and a deep copied output message as input. If the
    hook returns a message, the new message will be passed to the next hook or
    the original reply function. Otherwise, the original output will be passed
    instead."""

    _hooks_pre_speak: dict[
        str,
        Callable[
            [AgentBase, Msg, bool, bool],
            Union[Msg, None],
        ],
    ] = OrderedDict()
    """The hooks function that will be called before printing, which
    takes the `self` object, a deep copied printing message, a streaming flag,
    and a last flag as input. In streaming mode, the deep copied message will
    be a chunk of the original message, the streaming flat will be `True`, and
    the last flag will be `False` at the end of the streaming. If the hook
    returns a message, the new message will be passed to the next hook or the
    original speak function. Otherwise, the original input message will be
    passed instead."""

    _hooks_post_speak: dict[str, Callable[[AgentBase], None]] = OrderedDict()
    """The hooks function that will be called after the speak function, which
    takes the `self` object as input."""

    _hooks_pre_observe: dict[
        str,
        Callable[
            [AgentBase, Union[Msg, list[Msg]]],
            Union[Union[Msg, list[Msg]], None],
        ],
    ] = OrderedDict()
    """The hooks function that will be called before the observe function,
    which takes the `self` object and a deep copied input message(s) as input.
    If the hook returns a new message, the new message will be passed to the
    next hook or the original observe function. Otherwise, the original input
    will be passed instead."""

    _hooks_post_observe: dict[str, Callable[[AgentBase], None]] = OrderedDict()
    """The hooks function that will be called after the observe function,
    which takes the `self` object as input."""

    def __init__(
        self,
        name: str,
        sys_prompt: Optional[str] = None,
        model_config_name: str = None,
        use_memory: bool = True,
        to_dist: Optional[Union[DistConf, bool]] = False,
    ) -> None:
        r"""Initialize an agent from the given arguments.

        Args:
            name (`str`):
                The name of the agent.
            sys_prompt (`Optional[str]`):
                The system prompt of the agent, which can be passed by args
                or hard-coded in the agent.
            model_config_name (`str`, defaults to None):
                The name of the model config, which is used to load model from
                configuration.
            use_memory (`bool`, defaults to `True`):
                Whether the agent has memory.
            to_dist (`Optional[Union[DistConf, bool]]`, default to `False`):
                The configurations passed to :py:meth:`to_dist` method. Used in
                :py:class:`RpcMeta`, when this parameter is provided,
                the agent will automatically be converted into its distributed
                version. Below are some examples:

                .. code-block:: python

                    # run as a sub process
                    agent = XXXAgent(
                        # ... other parameters
                        to_dist=True,
                    )

                    # connect to an existing agent server
                    agent = XXXAgent(
                        # ... other parameters
                        to_dist=DistConf(
                            host="<ip of your server>",
                            port=<port of your server>,
                            # other parameters
                        ),
                    )

                See :doc:`Tutorial<tutorial/208-distribute>` for detail.
        """
        self.name = name
        self.sys_prompt = sys_prompt

        # TODO: support to receive a ModelWrapper instance
        if model_config_name is not None:
            model_manager = ModelManager.get_instance()
            self.model = model_manager.get_model_by_config_name(
                model_config_name,
            )

        if use_memory:
            self.memory = TemporaryMemory()
        else:
            self.memory = None

        # The audience of this agent, which means if this agent generates a
        # response, it will be passed to all agents in the audience.
        self._audience = None
        # convert to distributed agent, conversion is in `_AgentMeta`
        if to_dist is not False and to_dist is not None:
            logger.info(
                f"Convert {self.__class__.__name__}[{self.name}] into"
                " a distributed agent.",
            )

    @classmethod
    def generate_agent_id(cls) -> str:
        """Generate the agent_id of this agent instance"""
        # TODO: change cls.__name__ into a global unique agent_type
        return uuid.uuid4().hex

    @async_func
    def reply(self, x: Optional[Union[Msg, list[Msg]]] = None) -> Msg:
        """Define the actions taken by this agent.

        Args:
            x (`Optional[Union[Msg, list[Msg]]]`, defaults to `None`):
                The input message(s) to the agent, which also can be omitted if
                the agent doesn't need any input.

        Returns:
            `Msg`: The output message generated by the agent.

        Note:
            Given that some agents are in an adversarial environment,
            their input doesn't include the thoughts of other agents.
        """
        raise NotImplementedError(
            f"Agent [{type(self).__name__}] is missing the required "
            f'"reply" function.',
        )

    @async_func
    def __call__(self, *args: Any, **kwargs: Any) -> Msg:
        """Calling the reply function, and broadcast the generated
        response to all audiences if needed."""
        res = self.reply(*args, **kwargs)

        # broadcast to audiences if needed
        if self._audience is not None:
            self._broadcast_to_audience(res)

        return res

    def speak(
        self,
        content: Union[
            str,
            Msg,
            Generator[Tuple[bool, str], None, None],
            None,
        ],
        tool_calls: Optional[list[ToolUseBlock]] = None,
    ) -> None:
        """
        Speak out the message generated by the agent. If a string is given,
        a Msg object will be created with the string as the content.

        Args:
            content
             (`Union[str, Msg, Generator[Tuple[bool, str], None, None],
             None]`):
                The content of the message to be spoken out. If a string is
                given, a Msg object will be created with the agent's name, role
                as "assistant", and the given string as the content.
                If the content is a Generator, the agent will speak out the
                message chunk by chunk.
            tool_calls (`Optional[list[ToolUseBlock]]`, defaults to `None`):
                The tool calls generated by the agent. This parameter is only
                used when the content is a string or a generator (TODO). When
                the content is a Msg object, the tool calls should be included
                in the content field of the Msg object.
        """

        def _call_pre_speak_hooks(
            msg: Msg,
            stream: bool,
            last: bool,
        ) -> Msg:
            """Call the hooks in the speak function."""
            current_input = deepcopy(msg)
            for _, hook in self._hooks_pre_speak.items():
                hook_result = hook(self, deepcopy(current_input), stream, last)
                if hook_result is not None:
                    current_input = hook_result
            return current_input

        # Streaming mode
        if isinstance(content, GeneratorType):
            # The streaming message must share the same id for displaying in
            # the agentscope studio.
            msg = Msg(name=self.name, content="", role="assistant")
            for last, text_chunk in content:
                msg.content = text_chunk  # type: ignore[misc]
                # Call the hooks
                new_input = _call_pre_speak_hooks(
                    msg,
                    stream=True,
                    last=last,
                )
                log_stream_msg(new_input, last=last)

            # Call the post speak hooks
            for _, hook in self._hooks_post_speak.items():
                hook(self)

            return
        # Non-streaming mode
        if isinstance(content, str):
            content = [TextBlock(type="text", text=content)]
            if tool_calls:
                content.extend(tool_calls)
            msg_to_speak = Msg(
                name=self.name,
                content=content,
                role="assistant",
            )
        elif content is None:
            msg_to_speak = (
                Msg(
                    name=self.name,
                    content=tool_calls,
                    role="assistant",
                )
                if tool_calls
                else None
            )
        elif isinstance(content, Msg):
            msg_to_speak = content
        else:
            raise TypeError(
                "From version 0.0.5, the speak method only accepts str, Msg "
                "object and Generator, got {type(content)} instead.",
            )

        if msg_to_speak is None:
            logger.warning(
                "The content and tool_calls cannot be `None` at the same "
                "time, skip the speak function.",
            )
            return

        # Call the hooks
        msg_hook = _call_pre_speak_hooks(msg_to_speak, stream=False, last=True)

        log_msg(msg_hook)

        # Call the post speak hooks
        for _, hook in self._hooks_post_speak.items():
            hook(self)

    def observe(self, x: Union[Msg, Sequence[Msg]]) -> None:
        """Observe the input, store it in memory without response to it.

        Args:
            x (`Union[Msg, Sequence[Msg]]`):
                The input message to be recorded in memory.
        """
        if self.memory:
            self.memory.add(x)

    def reset_audience(self, audience: Sequence[AgentBase]) -> None:
        """Set the audience of this agent, which means if this agent
        generates a response, it will be passed to all audiences.

        Args:
            audience (`Sequence[AgentBase]`):
                The audience of this agent, which will be notified when this
                agent generates a response message.
        """
        # TODO: we leave the consideration of nested msghub for future.
        #  for now we suppose one agent can only be in one msghub
        self._audience = [_ for _ in audience if _ != self]

    def clear_audience(self) -> None:
        """Remove the audience of this agent."""
        # TODO: we leave the consideration of nested msghub for future.
        #  for now we suppose one agent can only be in one msghub
        self._audience = None

    def rm_audience(
        self,
        audience: Union[Sequence[AgentBase], AgentBase],
    ) -> None:
        """Remove the given audience from the Sequence"""
        if not isinstance(audience, Sequence):
            audience = [audience]

        for agent in audience:
            if self._audience is not None and agent in self._audience:
                self._audience.pop(self._audience.index(agent))
            else:
                logger.warning(
                    f"Skip removing agent [{agent.name}] from the "
                    f"audience for its inexistence.",
                )

    def _broadcast_to_audience(self, x: dict) -> None:
        """Broadcast the input to all audiences."""
        for agent in self._audience:
            agent.observe(x)

    @sync_func
    def __str__(self) -> str:
        serialized_fields = {
            "name": self.name,
            "type": self.__class__.__name__,
            "sys_prompt": self.sys_prompt,
            "agent_id": self.agent_id,
        }
        if hasattr(self, "model"):
            serialized_fields["model"] = {
                "model_type": self.model.model_type,
                "config_name": self.model.config_name,
            }
        return json.dumps(serialized_fields, ensure_ascii=False)

    @property
    def agent_id(self) -> str:
        """The unique id of this agent.

        Returns:
            str: agent_id
        """
        return self._oid

    @agent_id.setter
    def agent_id(self, agent_id: str) -> None:
        """Set the unique id of this agent."""
        self._oid = agent_id

    def _register_hook(
        self,
        hooks_attr_name: str,
        hook_name: str,
        hook: Callable,
    ) -> None:
        """The universal function to register a hook to the agent.

        Args:
            hooks_attr_name (`str`):
                The name of the hooks attribute.
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable`):
                The hook function.
        """
        assert hooks_attr_name.startswith("_hooks_") and hasattr(
            self,
            hooks_attr_name,
        ), f"Invalid hooks attribute name: {hooks_attr_name}"

        hooks = getattr(self, hooks_attr_name)
        hooks[hook_name] = hook

    def _remove_hook(self, hooks_attr_name: str, hook_name: str) -> None:
        """The universal function to remove a hook from the agent.

        Args:
            hooks_attr_name (`str`):
                The name of the hooks attribute.
            hook_name (`str`):
                The name of the hook to be removed.
        """
        assert hooks_attr_name.startswith("_hooks_") and hasattr(
            self,
            hooks_attr_name,
        ), f"Invalid hooks attribute name: {hooks_attr_name}"

        hooks = getattr(self, hooks_attr_name)
        if hook_name in hooks:
            hooks.pop(hook_name)
        else:
            raise ValueError(
                f"Hook [{hook_name}] not found in {hooks_attr_name}.",
            )

    def _clear_hooks(self, hooks_attr_name: str) -> None:
        """Clear the specified hooks from the agent.

        Args:
            hooks_attr_name (`str`):
                The name of the hooks attribute.
        """
        assert hooks_attr_name.startswith("_hooks_") and hasattr(
            self,
            hooks_attr_name,
        ), f"Invalid hooks attribute name: {hooks_attr_name}"

        hooks = getattr(self, hooks_attr_name)
        hooks.clear()

    def register_pre_reply_hook(
        self,
        hook_name: str,
        hook: Callable[
            [AgentBase, Optional[Union[Msg, list[Msg]]]],
            Union[Union[Msg, list[Msg]], None],
        ],
    ) -> None:
        """Register a pre-reply hook to the agent, which will be called
        before calling the reply function. If the hook returns messages(s),
        the original message(s) will be replaced as the input of the reply
        function.

        Arg:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase, Optional[Union[Msg, list[Msg]]]],
                Union[Union[Msg, list[Msg]], None]`):
                The hook function which takes the `self` object and the input
                message(s) as input. If the hook returns message(s), the
                original message(s) will be replaced as the input of the reply
                function.
        """
        self._register_hook("_hooks_pre_reply", hook_name, hook)

    def remove_pre_reply_hook(self, hook_name: str) -> None:
        """Remove the pre reply hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_pre_reply", hook_name)

    def clear_pre_reply_hooks(self) -> None:
        """Clear all pre reply hooks from the agent."""
        self._clear_hooks("_hooks_pre_reply")

    def register_post_reply_hook(
        self,
        hook_name: str,
        hook: Callable[
            [AgentBase, Msg],
            Union[Msg, None],
        ],
    ) -> None:
        """Register a post-reply hook to the agent, which will be called
        after calling the reply function. If the hook returns a message, the
        original message will be replaced as the output of the reply function.

        Args:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase, Msg], Union[Msg, None]]`):
                The hook function which takes the `self` object and the output
                message as input. If the hook returns a message, the original
                message will be replaced as the output of the reply function.
        """
        self._register_hook("_hooks_post_reply", hook_name, hook)

    def remove_post_reply_hook(
        self,
        hook_name: str,
    ) -> None:
        """Remove the post reply hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_post_reply", hook_name)

    def clear_post_reply_hooks(self) -> None:
        """Clear all post reply hooks from the agent."""
        self._clear_hooks("_hooks_post_reply")

    def register_pre_speak_hook(
        self,
        hook_name: str,
        hook: Callable[
            [AgentBase, Msg, bool, bool],
            Union[Msg, None],
        ],
    ) -> None:
        """Register a pre-speak hook to the agent, which will be called
        during the speak function. If the hook returns a message, the original
        message will be replaced as the input of the speak function.

        Args:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase, Msg, bool, bool], Union[Msg, None]]`):
                The hook function which takes the `self` object, the input
                message, a streaming flag, and a last flag as input. Within the
                speak function, the streaming message will be split into
                multiple sub messages with the same id, and the hook will be
                called for each sub message. If the hook returns a message, the
                original message will be replaced as the input of the speak
                function.
        """
        self._register_hook("_hooks_pre_speak", hook_name, hook)

    def remove_pre_speak_hook(self, hook_name: str) -> None:
        """Remove the pre speak hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_pre_speak", hook_name)

    def clear_pre_speak_hooks(self) -> None:
        """Clear all pre speak hooks from the agent."""
        self._clear_hooks("_hooks_pre_speak")

    def register_post_speak_hook(
        self,
        hook_name: str,
        hook: Callable[[AgentBase], None],
    ) -> None:
        """Register a post-speak hook to the agent, which will be called
        after calling the speak function.

        Args:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase], None]`):
                The hook function which takes the `self` object as input.
        """
        self._register_hook("_hooks_post_speak", hook_name, hook)

    def remove_post_speak_hook(self, hook_name: str) -> None:
        """Remove the post speak hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_post_speak", hook_name)

    def clear_post_speak_hooks(self) -> None:
        """Clear all post speak hooks from the agent."""
        self._clear_hooks("_hooks_post_speak")

    def register_pre_observe_hook(
        self,
        hook_name: str,
        hook: Callable[
            [AgentBase, Union[Msg, list[Msg]]],
            Union[Union[Msg, list[Msg]], None],
        ],
    ) -> None:
        """Register a pre-observe hook to the agent, which will be called
        before calling the observe function. If the hook returns message(s),
        the original message(s) will be replaced as the input of the observe
        function.

        Args:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase, Union[Msg, list[Msg]]],
                Union[Union[Msg, list[Msg]], None]`):
                The hook function which takes the `self` object and the input
                message(s) as input. If the hook returns message(s), the
                original message(s) will be replaced as the input of the
                observe function.
        """
        self._register_hook(
            "_hooks_pre_observe",
            hook_name,
            hook,
        )

    def remove_pre_observe_hook(
        self,
        hook_name: str,
    ) -> None:
        """Remove the pre observe hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_pre_observe", hook_name)

    def clear_pre_observe_hooks(self) -> None:
        """Clear all pre observe hooks from the agent."""
        self._clear_hooks("_hooks_pre_observe")

    def register_post_observe_hook(
        self,
        hook_name: str,
        hook: Callable[[AgentBase], None],
    ) -> None:
        """Register a post-observe hook to the agent, which will be called
        after calling the observe function.

        Args:
            hook_name (`str`):
                The name of the hook. If the name is already registered, the
                hook will be overwritten.
            hook (`Callable[[AgentBase], None]`):
                The hook function which takes the `self` object as input.
        """
        self._register_hook(
            "_hooks_post_observe",
            hook_name,
            hook,
        )

    def remove_post_observe_hook(self, hook_name: str) -> None:
        """Remove the post observe hook from the agent.

        Args:
            hook_name (`str`):
                The name of the hook to be removed.
        """
        self._remove_hook("_hooks_post_observe", hook_name)

    def clear_post_observe_hooks(self) -> None:
        """Clear all post observe hooks from the agent."""
        self._clear_hooks("_hooks_post_observe")

    def clear_all_hooks(self) -> None:
        """Clear all hooks from the agent."""
        self.clear_pre_reply_hooks()
        self.clear_post_reply_hooks()
        self.clear_pre_speak_hooks()
        self.clear_post_speak_hooks()
        self.clear_pre_observe_hooks()
        self.clear_post_observe_hooks()
