"""Tests for streaming event handling.

Tests the behavior specified in the plan:
- Test 1: stream_and_print yields tokens from messages-tuple events
- Test 2: stream_and_print accumulates content by message id
- Test 3: stream_and_print returns final accumulated text
- Test 4: stream_and_print handles tool call events
- Test 5: stream_and_print handles tool result events
- Test 6: stream_and_print handles custom retry events
- Test 7: stream_and_print handles end event

Plus error handling tests:
- Test 8: GeneratorExit is caught and re-raised (clean interrupt)
- Test 9: Unknown exception during streaming is raised
- Test 10: Partial output before error is preserved
- Test 11: Tool execution errors don't crash the stream (ERRR-02)
"""
import io
import sys
import pytest


class TestStreamAndPrint:
    """Tests for stream_and_print function."""

    def test_token_streaming_from_messages_tuple(self, mock_deerflow_client, capsys):
        """Test 1: stream_and_print yields tokens from messages-tuple events."""
        from lib.stream import stream_and_print

        # Create events with AI message tokens
        events = [
            ("messages-tuple", {"type": "ai", "content": "Hello", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": " world", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": "!", "id": "msg-1"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "test prompt", thread_id="test-thread")

        captured = capsys.readouterr()
        # Should print tokens as they arrive (with flush=True)
        assert "Hello" in captured.out
        assert "world" in captured.out
        assert "!" in captured.out
        # Should return the final text
        assert result == "Hello world!"

    def test_accumulates_content_by_message_id(self, mock_deerflow_client, capsys):
        """Test 2: stream_and_print accumulates content by message id."""
        from lib.stream import stream_and_print

        # Multiple messages with different IDs (parallel tool calls)
        events = [
            ("messages-tuple", {"type": "ai", "content": "First ", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": "Second ", "id": "msg-2"}),
            ("messages-tuple", {"type": "ai", "content": "message", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": "content", "id": "msg-2"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "test", thread_id="t1")

        # Should track content by message ID
        # The last message ID determines the final response
        # In this case, msg-2 is the last, so result should be "Second content"
        assert "Second content" in result

    def test_returns_final_accumulated_text(self, mock_deerflow_client):
        """Test 3: stream_and_print returns final accumulated text."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {"type": "ai", "content": "The answer ", "id": "final"}),
            ("messages-tuple", {"type": "ai", "content": "is 42", "id": "final"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "question", thread_id="t1")

        assert result == "The answer is 42"

    def test_handles_tool_call_events(self, mock_deerflow_client, capsys):
        """Test 4: stream_and_print handles tool call events."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {
                "type": "ai",
                "content": "",
                "id": "msg-1",
                "tool_calls": [{"name": "search", "args": {"query": "test"}, "id": "tc-1"}]
            }),
            ("messages-tuple", {"type": "ai", "content": "Done", "id": "msg-2"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "test", thread_id="t1")

        captured = capsys.readouterr()
        # Should print tool call notification to stderr or stdout
        # The plan says: "[Calling: {tool_name}]"
        assert "Calling" in captured.out or "Calling" in captured.err
        assert "search" in captured.out or "search" in captured.err

    def test_handles_tool_result_events(self, mock_deerflow_client, capsys):
        """Test 5: stream_and_print handles tool result events."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {
                "type": "ai",
                "content": "",
                "id": "msg-1",
                "tool_calls": [{"name": "calculator", "args": {}, "id": "tc-1"}]
            }),
            ("messages-tuple", {
                "type": "tool",
                "content": "42",
                "name": "calculator",
                "tool_call_id": "tc-1",
                "id": "tool-msg-1"
            }),
            ("messages-tuple", {"type": "ai", "content": "The answer is 42", "id": "msg-2"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "test", thread_id="t1")

        captured = capsys.readouterr()
        # Should print tool completion notification
        # The plan says: "[Tool {name} completed]"
        assert "Tool" in captured.out or "Tool" in captured.err
        assert "calculator" in captured.out or "calculator" in captured.err

    def test_handles_custom_retry_events(self, mock_deerflow_client, capsys):
        """Test 6: stream_and_print handles custom retry events."""
        from lib.stream import stream_and_print

        events = [
            ("custom", {"type": "llm_retry", "attempt": 1, "max_attempts": 3, "wait_ms": 1000}),
            ("custom", {"type": "llm_retry", "attempt": 2, "max_attempts": 3, "wait_ms": 2000}),
            ("messages-tuple", {"type": "ai", "content": "Success!", "id": "msg-1"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)
        result = stream_and_print(client, "test", thread_id="t1")

        captured = capsys.readouterr()
        # Should print retry progress
        # The plan says: "[LLM retry {attempt}/{max}, waiting {wait}s]"
        assert "retry" in captured.out.lower() or "retry" in captured.err.lower()
        assert "1" in captured.out or "1" in captured.err
        assert "3" in captured.out or "3" in captured.err

    def test_handles_end_event(self, mock_deerflow_client, capsys):
        """Test 7: stream_and_print handles end event."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {"type": "ai", "content": "Hello", "id": "msg-1"}),
            ("end", {"usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}}),
        ]

        client = mock_deerflow_client(events=events)
        # Should not raise an exception
        result = stream_and_print(client, "test", thread_id="t1")

        assert result == "Hello"
        # End event should be handled silently (no error)


class TestStreamingErrors:
    """Tests for streaming error handling."""

    def test_generator_exit_propagates(self, mock_deerflow_client):
        """Test 8: GeneratorExit is caught and re-raised (clean interrupt)."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {"type": "ai", "content": "Partial", "id": "msg-1"}),
        ]

        client = mock_deerflow_client(events=events, error=GeneratorExit())

        # GeneratorExit should propagate (user interrupt)
        with pytest.raises(GeneratorExit):
            stream_and_print(client, "test", thread_id="t1")

    def test_unknown_exception_propagates(self, mock_deerflow_client):
        """Test 9: Unknown exception during streaming is raised."""
        from lib.stream import stream_and_print

        events = [
            ("messages-tuple", {"type": "ai", "content": "Start", "id": "msg-1"}),
        ]

        client = mock_deerflow_client(events=events, error=RuntimeError("Unexpected error"))

        with pytest.raises(RuntimeError, match="Unexpected error"):
            stream_and_print(client, "test", thread_id="t1")

    def test_partial_output_preserved_before_error(self, mock_deerflow_client, capsys):
        """Test 10: Partial output before error is preserved."""
        from lib.stream import stream_and_print

        # This test verifies that when an exception occurs mid-stream,
        # any output printed before the exception is preserved (printed to stdout)
        events = [
            ("messages-tuple", {"type": "ai", "content": "Before ", "id": "msg-1"}),
            ("messages-tuple", {"type": "ai", "content": "error", "id": "msg-1"}),
        ]

        client = mock_deerflow_client(events=events, error=ValueError("Test error"))

        with pytest.raises(ValueError, match="Test error"):
            stream_and_print(client, "test", thread_id="t1")

        # The partial output should have been printed
        captured = capsys.readouterr()
        assert "Before" in captured.out
        assert "error" in captured.out

    def test_tool_error_continues_stream(self, mock_deerflow_client, capsys):
        """Test 11: Tool execution errors don't crash the stream (ERRR-02)."""
        from lib.stream import stream_and_print

        # Tool result event with error field
        events = [
            ("messages-tuple", {
                "type": "ai",
                "content": "",
                "id": "msg-1",
                "tool_calls": [{"name": "risky_tool", "args": {}, "id": "tc-1"}]
            }),
            ("messages-tuple", {
                "type": "tool",
                "content": "Error: Permission denied",
                "name": "risky_tool",
                "tool_call_id": "tc-1",
                "id": "tool-msg-1",
                "error": True  # This indicates tool execution error
            }),
            ("messages-tuple", {"type": "ai", "content": "I encountered an error but continued", "id": "msg-2"}),
            ("end", {}),
        ]

        client = mock_deerflow_client(events=events)

        # Should NOT raise an exception - tool errors should be handled gracefully
        result = stream_and_print(client, "test", thread_id="t1")

        captured = capsys.readouterr()
        # Should print warning about tool error
        assert "error" in captured.err.lower() or "error" in captured.out.lower()
        # Should continue streaming and return response
        assert "continued" in result
