"""Streaming SSE tests — format_sse_event, stream_to_sse, stream_to_async_gen."""
from __future__ import annotations

import pytest

from intelligence.streaming.sse import format_sse_event, stream_to_sse, stream_to_async_gen
from intelligence.providers.base import StreamEvent, FinishReason


def test_format_sse_event_chunk():
    event = StreamEvent(type="chunk", content="Hello")
    output = format_sse_event(event)
    assert output.startswith("data: ")
    assert "Hello" in output
    assert output.endswith("\n\n")


def test_format_sse_event_done():
    event = StreamEvent(type="done", finish_reason=FinishReason.STOP, usage={"prompt_tokens": 10, "completion_tokens": 5})
    output = format_sse_event(event)
    assert "done" in output
    assert "stop" in output
    assert "prompt_tokens" in output


def test_format_sse_event_error():
    event = StreamEvent(type="error", error="API key invalid")
    output = format_sse_event(event)
    assert "error" in output
    assert "API key invalid" in output


def test_format_sse_event_tool_call():
    event = StreamEvent(type="tool_call", tool_calls=[{"id": "call_1", "function": {"name": "test"}}])
    output = format_sse_event(event)
    assert "tool_call" in output
    assert "call_1" in output


@pytest.mark.asyncio
async def test_stream_to_sse():
    async def mock_stream():
        yield StreamEvent(type="chunk", content="Hello ")
        yield StreamEvent(type="chunk", content="World")
        yield StreamEvent(type="done", finish_reason=FinishReason.STOP)

    results = []
    async for sse in stream_to_sse(mock_stream()):
        results.append(sse)

    assert len(results) == 3
    assert "Hello" in results[0]
    assert "World" in results[1]
    assert "done" in results[2]


@pytest.mark.asyncio
async def test_stream_to_async_gen():
    async def mock_stream():
        yield StreamEvent(type="chunk", content="Hello ")
        yield StreamEvent(type="chunk", content="World")
        yield StreamEvent(type="done", finish_reason=FinishReason.STOP)

    results = []
    async for item in stream_to_async_gen(mock_stream()):
        results.append(item)

    assert len(results) == 3
    assert results[0]["type"] == "chunk"
    assert results[0]["content"] == "Hello "
    assert results[2]["type"] == "done"


@pytest.mark.asyncio
async def test_stream_error_handling():
    async def error_stream():
        yield StreamEvent(type="error", error="Rate limit exceeded")

    results = []
    async for item in stream_to_async_gen(error_stream()):
        results.append(item)

    assert len(results) == 1
    assert results[0]["type"] == "error"
    assert "Rate limit" in results[0]["error"]
