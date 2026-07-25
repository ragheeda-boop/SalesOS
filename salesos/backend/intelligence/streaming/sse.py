from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, AsyncGenerator, AsyncIterator

from intelligence.providers.base import StreamEvent


@dataclass
class SSEMessage:
    event: str = "message"
    data: str = ""
    id: str | None = None
    retry: int | None = None


def format_sse_event(event: StreamEvent) -> str:
    if event.type == "chunk":
        payload = json.dumps({"type": "chunk", "content": event.content}, ensure_ascii=False)
    elif event.type == "done":
        payload = json.dumps(
            {
                "type": "done",
                "finish_reason": event.finish_reason.value if event.finish_reason else "stop",
                "usage": event.usage,
            },
        )
    elif event.type == "error":
        payload = json.dumps({"type": "error", "error": event.error or "Unknown error"})
    elif event.type == "tool_call":
        payload = json.dumps({"type": "tool_call", "tool_calls": event.tool_calls})
    else:
        payload = json.dumps({"type": event.type, "content": event.content})

    return f"data: {payload}\n\n"


async def stream_to_sse(stream: AsyncIterator[StreamEvent]) -> AsyncGenerator[str, None]:
    async for event in stream:
        yield format_sse_event(event)


async def stream_to_async_gen(stream: AsyncIterator[StreamEvent]) -> AsyncGenerator[dict[str, Any], None]:
    async for event in stream:
        if event.type == "chunk":
            yield {"type": "chunk", "content": event.content}
        elif event.type == "done":
            yield {
                "type": "done",
                "finish_reason": event.finish_reason.value if event.finish_reason else "stop",
                "usage": event.usage,
            }
        elif event.type == "error":
            yield {"type": "error", "error": event.error or "Unknown error"}
        elif event.type == "tool_call":
            yield {"type": "tool_call", "tool_calls": event.tool_calls}
        else:
            yield {"type": event.type, "content": event.content}
