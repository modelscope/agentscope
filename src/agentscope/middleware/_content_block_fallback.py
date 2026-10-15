# -*- coding: utf-8 -*-
"""Content-block fallback extension points."""
import inspect
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass, field
from typing import AsyncGenerator, Awaitable, Callable, TYPE_CHECKING

from ._base import MiddlewareBase
from .._logging import logger
from ..exception import ContentBlockedError
from ..message import Msg, TextBlock, ToolResultBlock
from ..model import ChatModelBase, ChatResponse, FinishedReason
from ..tool import ToolChoice

if TYPE_CHECKING:
    from ..agent import Agent

_MASKED_CONTENT = "[Content omitted after a provider content block.]"


def _merge_quarantine(
    target: dict[str, list[str]],
    additions: dict[str, list[str]],
) -> None:
    """Merge message-scoped block IDs without retaining duplicate IDs."""
    for message_id, block_ids in additions.items():
        target[message_id] = list(
            dict.fromkeys([*target.get(message_id, []), *block_ids]),
        )


@dataclass(frozen=True)
class ContentBlockFallbackContext:
    """The context passed to a content-block fallback strategy."""

    agent: "Agent"
    """The agent whose model call was blocked."""

    current_model: ChatModelBase
    """The model used for the blocked call."""

    messages: list[Msg]
    """A defensive copy of the messages used for the blocked call.

    A strategy can mutate these messages in place and return them without
    changing the agent's stored conversation context.
    """

    tools: list[dict]
    """The tool schemas used for the blocked call."""

    tool_choice: ToolChoice | None
    """The tool choice used for the blocked call."""

    error: ContentBlockedError
    """The normalized provider error."""

    attempt: int
    """The one-based fallback attempt number."""


@dataclass(frozen=True)
class ContentBlockFallbackDecision:
    """A strategy decision to retry with replacement messages."""

    messages: list[Msg]
    """The protocol-valid replacement messages for the next model call."""

    quarantined_blocks: dict[str, list[str]] = field(default_factory=dict)
    """Proposed assistant text/tool-result block IDs, keyed by message ID.

    After successful recovery, the middleware records these IDs in the
    agent state and replaces their content with the built-in placeholder on
    future calls. Custom strategies leave this empty for transient edits.
    These IDs describe effective isolation, not confirmed policy violations.
    """


class ContentBlockFallbackStrategy(ABC):
    """Create a replacement request after a content block."""

    @abstractmethod
    async def recover(
        self,
        context: ContentBlockFallbackContext,
    ) -> ContentBlockFallbackDecision | None:
        """Propose replacement input without calling the model or tools.

        Args:
            context (`ContentBlockFallbackContext`):
                The blocked call and one-based recovery attempt. The
                middleware deep-copies only the messages; a strategy may
                mutate that copy but must preserve valid tool call/result
                pairing and treat the other shared objects as read-only.

        Returns:
            `ContentBlockFallbackDecision | None`:
                Replacement messages, or ``None`` to make the middleware
                re-raise the current content-block error. Leave quarantine
                IDs empty for transient edits. Proposed IDs accumulate
                across attempts and request the built-in placeholder on
                future calls only after recovery succeeds; they do not
                persist arbitrary replacement text.

        Exceptions raised by the strategy propagate to the caller. The
        middleware, not the strategy, owns the retry budget and state commit.
        """


class ReverseMaskStrategy(ContentBlockFallbackStrategy):
    """Mask one assistant message per attempt, from newest to oldest.

    Replace non-empty text blocks and tool-result outputs with a placeholder.
    Tool outputs are replaced in full, including any nested media. Preserve
    tool calls, IDs, metadata, thinking blocks, and other content blocks.
    User and system messages are never modified.

    Mutate only the defensive message copy supplied by the middleware. Skip
    already masked content so successive attempts retain earlier masks and
    move backwards. No per-call state is stored on the strategy instance.
    Return ``None`` when no candidate remains. Propose quarantine IDs for
    successful recovery to persist without modifying conversation history.
    """

    async def recover(
        self,
        context: ContentBlockFallbackContext,
    ) -> ContentBlockFallbackDecision | None:
        """Mask the newest assistant message with eligible content.

        Args:
            context (`ContentBlockFallbackContext`):
                The blocked input, including masks from earlier attempts.
                Its messages are modified in place. Direct callers must
                supply their own copy to protect stored conversation history.

        Returns:
            `ContentBlockFallbackDecision | None`:
                The same message list with all eligible text and tool-result
                outputs in one assistant message replaced, plus that
                message's newly masked block IDs. Return ``None`` if no
                candidate remains. Empty or already masked content and all
                user/system messages are skipped; other blocks are preserved.

        This method neither calls the model nor commits isolation records.
        """
        for message in reversed(context.messages):
            if message.role != "assistant":
                continue
            block_ids = []
            for block in message.content:
                if isinstance(block, TextBlock):
                    if block.text and block.text != _MASKED_CONTENT:
                        block.text = _MASKED_CONTENT
                        block_ids.append(block.id)
                elif isinstance(block, ToolResultBlock):
                    if block.output and block.output != _MASKED_CONTENT:
                        block.output = _MASKED_CONTENT
                        block_ids.append(block.id)
            if block_ids:
                return ContentBlockFallbackDecision(
                    messages=context.messages,
                    quarantined_blocks={message.id: block_ids},
                )
        return None


class ContentBlockFallbackMiddleware(MiddlewareBase):
    """Retry blocked model calls with messages supplied by a strategy.

    The middleware retries only the intercepted model call. It never re-runs
    the surrounding reasoning or acting loop, so already completed tools are
    not executed again.
    """

    def __init__(
        self,
        strategy: ContentBlockFallbackStrategy,
        max_fallback_attempts: int = 3,
    ) -> None:
        """Initialize the content-block fallback middleware.

        Args:
            strategy (`ContentBlockFallbackStrategy`):
                The downstream strategy that supplies replacement messages.
            max_fallback_attempts (`int`, defaults to `3`):
                The maximum number of replacement calls per middleware chain.
                A separately configured fallback model starts a new chain.
                The initial call is not counted. Zero disables replacement
                calls but still applies previously committed isolation.

        Raises:
            `ValueError`:
                If ``max_fallback_attempts`` is negative.
        """
        if max_fallback_attempts < 0:
            raise ValueError("max_fallback_attempts must be non-negative.")
        self.strategy = strategy
        self.max_fallback_attempts = max_fallback_attempts

    async def clear_quarantine(self, agent: "Agent") -> None:
        """Clear this middleware's isolation records for an idle agent.

        Remove this middleware's state namespace without changing original
        messages or other middleware state. Missing records are a no-op.
        This does not cancel in-flight recovery, which could commit new IDs,
        so call it only when the agent is idle. No disk write is performed.

        Args:
            agent (`Agent`):
                The agent whose subsequent calls should use original content.
                Save its state through the normal session persistence path
                to retain this reset across reloads.
        """
        agent.state.middle_context.pop(await self.get_middleware_key(), None)

    async def _apply_quarantine(
        self,
        agent: "Agent",
        messages: list[Msg],
    ) -> list[Msg]:
        """Apply committed masks without modifying history or retry budgets.

        Match both message and block IDs, replacing only assistant text and
        tool-result outputs. Missing IDs are ignored; new blocks remain
        visible. Records are read from the agent's middleware state.

        Returns:
            `list[Msg]`:
                The original list if there are no isolation records;
                otherwise a deep copy with matching blocks masked, even if
                none of the recorded IDs occur in the current input.
        """
        state = agent.state.middle_context.get(
            await self.get_middleware_key(),
            {},
        )
        quarantined = state.get("quarantined_blocks", {})
        if not quarantined:
            return messages
        messages = deepcopy(messages)
        for message in messages:
            if message.role != "assistant":
                continue
            block_ids = quarantined.get(message.id, [])
            for block in message.content:
                if block.id not in block_ids:
                    continue
                if isinstance(block, TextBlock):
                    block.text = _MASKED_CONTENT
                elif isinstance(block, ToolResultBlock):
                    block.output = _MASKED_CONTENT
        return messages

    async def _recover_messages(
        self,
        *,
        agent: "Agent",
        current_model: ChatModelBase,
        messages: list[Msg],
        tools: list[dict],
        tool_choice: ToolChoice | None,
        error: ContentBlockedError,
        completed_attempts: int,
        pending_quarantine: dict[str, list[str]],
    ) -> tuple[list[Msg], int]:
        """Prepare the next replacement without executing a model call.

        Deep-copy ``messages`` before invoking the strategy. Merge accepted
        quarantine proposals into ``pending_quarantine`` in place, leaving
        persistent agent state unchanged. ``completed_attempts`` counts
        replacement calls already attempted, excluding the initial call.

        Returns:
            `tuple[list[Msg], int]`:
                Replacement messages and the next attempt number, which the
                caller uses as its updated counter when issuing the call.

        Raises:
            `ContentBlockedError`:
                The supplied ``error`` if the budget is exhausted or the
                strategy returns ``None``. Strategy exceptions also propagate.
        """
        attempt = completed_attempts + 1
        details = (
            f"agent={agent.name}, model={current_model.model}, "
            f"provider={error.provider}, code={error.original_code}, "
            f"request_id={error.request_id}, phase={error.phase}"
        )
        message = f"Content-block fallback: blocked; {details}."
        logger.warning(message)
        if attempt > self.max_fallback_attempts:
            message = (
                f"Content-block fallback: budget exhausted "
                f"({completed_attempts}/{self.max_fallback_attempts}); "
                f"{details}."
            )
            logger.warning(message)
            raise error

        decision = await self.strategy.recover(
            ContentBlockFallbackContext(
                agent=agent,
                current_model=current_model,
                messages=deepcopy(messages),
                tools=tools,
                tool_choice=tool_choice,
                error=error,
                attempt=attempt,
            ),
        )
        if decision is None:
            message = (
                f"Content-block fallback: strategy stopped at attempt "
                f"{attempt}/{self.max_fallback_attempts}; {details}."
            )
            logger.warning(message)
            raise error
        message = (
            f"Content-block fallback: retrying with replacement messages "
            f"({attempt}/{self.max_fallback_attempts}); {details}."
        )
        logger.info(message)
        _merge_quarantine(pending_quarantine, decision.quarantined_blocks)
        return decision.messages, attempt

    async def _complete_recovery(
        self,
        agent: "Agent",
        current_model: ChatModelBase,
        completed_attempts: int,
        pending_quarantine: dict[str, list[str]],
    ) -> None:
        """Commit successful isolation and report recovery without payloads.

        The caller must establish successful completion before invoking this
        method. Merge ``pending_quarantine`` into the agent's middleware
        state without changing history or clearing the pending mapping.
        Normal AgentState persistence saves the IDs; no disk write occurs
        here. Log success only when replacement calls were attempted.
        """
        if pending_quarantine:
            state = agent.state.middle_context.setdefault(
                await self.get_middleware_key(),
                {},
            )
            _merge_quarantine(
                state.setdefault("quarantined_blocks", {}),
                pending_quarantine,
            )
        if completed_attempts:
            message = (
                f"Content-block fallback: recovered after "
                f"{completed_attempts} replacement call(s); "
                f"agent={agent.name}, model={current_model.model}."
            )
            logger.info(message)

    async def _wrap_stream(
        self,
        *,
        stream: AsyncGenerator[ChatResponse, None],
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable[
            ...,
            Awaitable[ChatResponse | AsyncGenerator[ChatResponse, None]],
        ],
        messages: list[Msg],
        completed_attempts: int,
        pending_quarantine: dict[str, list[str]],
    ) -> AsyncGenerator[ChatResponse, None]:
        """Consume and recover a stream only before any chunk is emitted.

        Continue the same retry budget and ``pending_quarantine`` mapping
        used to obtain ``stream``. Any yielded chunk, including one carrying
        only usage, or an error with ``partial_output=True`` prevents replay.
        Close each consumed inner stream in ``finally``.

        Commit pending IDs only after normal stream exhaustion and cleanup
        without an interrupted result, or after a replacement non-stream
        result marked COMPLETED. Errors, interruption, cancellation, and
        early closure before completion do not commit pending IDs.

        Yields:
            `ChatResponse`:
                Original or replacement stream chunks, or a single response
                if a replacement call returns a non-stream result.

        Raises:
            `ContentBlockedError`:
                If replay is unsafe, the budget is exhausted, or the strategy
                stops. Other model, strategy, and cleanup errors propagate.
        """
        current_stream = stream
        current_messages = messages
        attempts = completed_attempts

        while True:
            emitted = False
            completed = False
            interrupted = False
            try:
                async for chunk in current_stream:
                    emitted = True
                    interrupted = interrupted or (
                        chunk.finished_reason == FinishedReason.INTERRUPTED
                    )
                    yield chunk
                completed = True
            except ContentBlockedError as error:
                if emitted or error.partial_output:
                    error.partial_output = True
                    message = (
                        f"Content-block fallback: stopped after partial "
                        f"output; agent={agent.name}, "
                        f"model={input_kwargs['current_model'].model}, "
                        f"provider={error.provider}, "
                        f"code={error.original_code}, "
                        f"request_id={error.request_id}."
                    )
                    logger.warning(message)
                    raise
                current_messages, attempts = await self._recover_messages(
                    agent=agent,
                    current_model=input_kwargs["current_model"],
                    messages=current_messages,
                    tools=input_kwargs["tools"],
                    tool_choice=input_kwargs["tool_choice"],
                    error=error,
                    completed_attempts=attempts,
                    pending_quarantine=pending_quarantine,
                )
            finally:
                await current_stream.aclose()

            if completed:
                if not interrupted:
                    await self._complete_recovery(
                        agent,
                        input_kwargs["current_model"],
                        attempts,
                        pending_quarantine,
                    )
                return

            while True:
                try:
                    result = await next_handler(messages=current_messages)
                    break
                except ContentBlockedError as error:
                    current_messages, attempts = await self._recover_messages(
                        agent=agent,
                        current_model=input_kwargs["current_model"],
                        messages=current_messages,
                        tools=input_kwargs["tools"],
                        tool_choice=input_kwargs["tool_choice"],
                        error=error,
                        completed_attempts=attempts,
                        pending_quarantine=pending_quarantine,
                    )

            if isinstance(result, ChatResponse):
                if result.finished_reason == FinishedReason.COMPLETED:
                    await self._complete_recovery(
                        agent,
                        input_kwargs["current_model"],
                        attempts,
                        pending_quarantine,
                    )
                yield result
                return
            current_stream = result

    async def on_model_call(
        self,
        agent: "Agent",
        input_kwargs: dict,
        next_handler: Callable[
            ...,
            Awaitable[ChatResponse | AsyncGenerator[ChatResponse, None]],
        ],
    ) -> ChatResponse | AsyncGenerator[ChatResponse, None]:
        """Apply saved isolation and recover a blocked model call.

        Args:
            agent (`Agent`):
                The agent owning the conversation and isolation records.
            input_kwargs (`dict`):
                Call arguments containing ``messages``, ``current_model``,
                ``tools``, and ``tool_choice``.
            next_handler (`Callable`):
                The next model-call handler. Each invocation overrides only
                ``messages``; other arguments remain bound to the chain.

        Returns:
            `ChatResponse | AsyncGenerator[ChatResponse, None]`:
                A non-stream result or a wrapped stream. Stream recovery and
                errors occur during iteration, not when the stream is returned.

        Raises:
            `ContentBlockedError`:
                If replacement attempts are exhausted or the strategy stops.
                Other handler and strategy exceptions propagate unchanged.

        Previously committed masks apply before the initial call without
        consuming the per-chain replacement budget. New IDs remain local
        until a COMPLETED non-stream result or successful stream completion.
        Failed or interrupted recovery leaves earlier records intact. The
        middleware updates AgentState only; it neither writes to storage nor
        restarts the agent loop or completed tools. Separately configured
        fallback models have independent chains and replacement budgets.
        """
        messages = await self._apply_quarantine(
            agent,
            input_kwargs["messages"],
        )
        completed_attempts = 0
        pending_quarantine: dict[str, list[str]] = {}

        while True:
            try:
                result = await next_handler(messages=messages)
                break
            except ContentBlockedError as error:
                messages, completed_attempts = await self._recover_messages(
                    agent=agent,
                    current_model=input_kwargs["current_model"],
                    messages=messages,
                    tools=input_kwargs["tools"],
                    tool_choice=input_kwargs["tool_choice"],
                    error=error,
                    completed_attempts=completed_attempts,
                    pending_quarantine=pending_quarantine,
                )

        if not inspect.isasyncgen(result):
            if result.finished_reason == FinishedReason.COMPLETED:
                await self._complete_recovery(
                    agent,
                    input_kwargs["current_model"],
                    completed_attempts,
                    pending_quarantine,
                )
            return result

        return self._wrap_stream(
            stream=result,
            agent=agent,
            input_kwargs=input_kwargs,
            next_handler=next_handler,
            messages=messages,
            completed_attempts=completed_attempts,
            pending_quarantine=pending_quarantine,
        )
