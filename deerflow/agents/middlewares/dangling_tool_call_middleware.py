"""Middleware to fix dangling tool calls in message history.

A dangling tool call occurs when an AIMessage contains tool_calls but there are
no corresponding ToolMessages in the history (e.g., due to user interruption or
request cancellation). This causes LLM errors due to incomplete message format.

This middleware intercepts the model call to detect and patch such gaps by
inserting synthetic ToolMessages with an error indicator immediately after the
AIMessage that made the tool calls, ensuring correct message ordering.

Note: Uses wrap_model_call instead of before_model to ensure patches are inserted
at the correct positions (immediately after each dangling AIMessage), not appended
to the end of the message list as before_model + add_messages reducer would do.
"""

import json
import logging
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import override

from langchain.agents import AgentState
from langchain.agents.middleware import AgentMiddleware
from langchain.agents.middleware.types import ModelCallResult, ModelRequest, ModelResponse
from langchain_core.messages import ToolMessage

logger = logging.getLogger(__name__)


class DanglingToolCallMiddleware(AgentMiddleware[AgentState]):
    """Inserts placeholder ToolMessages for dangling tool calls before model invocation.

    Scans the message history for AIMessages whose tool_calls lack corresponding
    ToolMessages, and injects synthetic error responses immediately after the
    offending AIMessage so the LLM receives a well-formed conversation.
    """

    @staticmethod
    def _message_tool_calls(msg) -> list[dict]:
        """Return normalized tool calls from structured fields or raw provider payloads."""
        tool_calls = getattr(msg, "tool_calls", None) or []
        if tool_calls:
            return list(tool_calls)

        raw_tool_calls = (getattr(msg, "additional_kwargs", None) or {}).get("tool_calls") or []
        normalized: list[dict] = []
        for raw_tc in raw_tool_calls:
            if not isinstance(raw_tc, dict):
                continue

            function = raw_tc.get("function")
            name = raw_tc.get("name")
            if not name and isinstance(function, dict):
                name = function.get("name")

            args = raw_tc.get("args", {})
            if not args and isinstance(function, dict):
                raw_args = function.get("arguments")
                if isinstance(raw_args, str):
                    try:
                        parsed_args = json.loads(raw_args)
                    except (TypeError, ValueError, json.JSONDecodeError):
                        parsed_args = {}
                    args = parsed_args if isinstance(parsed_args, dict) else {}

            normalized.append(
                {
                    "id": raw_tc.get("id"),
                    "name": name or "unknown",
                    "args": args if isinstance(args, dict) else {},
                }
            )

        return normalized

    def _build_patched_messages(self, messages: list) -> list | None:
        """Return a new message list with patches inserted at the correct positions.

        For each AIMessage with dangling tool_calls (no corresponding ToolMessage),
        a synthetic ToolMessage is inserted immediately after that AIMessage.
        Returns None if no patches are needed.

        This normalizes model-bound causal order before provider serialization while
        preserving already valid transcripts unchanged.
        """
        tool_messages_by_id: dict[str, deque[ToolMessage]] = defaultdict(deque)
        for msg in messages:
            if isinstance(msg, ToolMessage):
                tool_messages_by_id[msg.tool_call_id].append(msg)

        tool_call_ids: set[str] = set()
        for msg in messages:
            if getattr(msg, "type", None) != "ai":
                continue
            for tc in self._message_tool_calls(msg):
                tc_id = tc.get("id")
                if tc_id:
                    tool_call_ids.add(tc_id)

        patched: list = []
        patch_count = 0
        for msg in messages:
            if isinstance(msg, ToolMessage) and msg.tool_call_id in tool_call_ids:
                continue

            patched.append(msg)

            for tc in self._message_tool_calls(msg):
                tc_id = tc.get("id")
                if not tc_id:
                    continue

                tool_msg_queue = tool_messages_by_id.get(tc_id)
                existing_tool_msg = tool_msg_queue.popleft() if tool_msg_queue else None
                if existing_tool_msg is not None:
                    patched.append(existing_tool_msg)
                else:
                    patched.append(
                        ToolMessage(
                            content="[Tool call was interrupted and did not return a result.]",
                            tool_call_id=tc_id,
                            name=tc.get("name", "unknown"),
                            status="error",
                        )
                    )
                    patch_count += 1

        if patched == messages:
            return None

        logger.warning(f"Injecting {patch_count} placeholder ToolMessage(s) for dangling tool calls")
        return patched

    @override
    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelCallResult:
        patched = self._build_patched_messages(request.messages)
        if patched is not None:
            request = request.override(messages=patched)
        return handler(request)

    @override
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelCallResult:
        patched = self._build_patched_messages(request.messages)
        if patched is not None:
            request = request.override(messages=patched)
        return await handler(request)
