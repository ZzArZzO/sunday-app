"""Tests for the streaming assistant's compliance-safe guardrail (assistant.answer_stream).

The critical property: advice-shaped text must NEVER appear in a released
`delta` event — it has to be caught inside the safety window and replaced.
Uses a fake Anthropic client (no network).
"""

from types import SimpleNamespace

from app.schemas.chat import ChatMessage
from app.services.llm import assistant


class _FakeStream:
    def __init__(self, chunks: list[str]):
        self._chunks = chunks

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    @property
    def text_stream(self):
        return iter(self._chunks)


class _FakeMessages:
    def __init__(self, stream_chunks: list[str], create_text: str):
        self._stream_chunks = stream_chunks
        self._create_text = create_text

    def stream(self, **_):
        return _FakeStream(self._stream_chunks)

    def create(self, **_):
        return SimpleNamespace(content=[SimpleNamespace(type="text", text=self._create_text)])


class _FakeClient:
    def __init__(self, messages: _FakeMessages):
        self.messages = messages


def _portfolio():
    return SimpleNamespace(positions=[], user=None, snapshots=[])


def _msgs():
    return [ChatMessage(role="user", content="tell me about my portfolio")]


def _run(monkeypatch, chunks: list[str], create_text: str) -> list[dict]:
    client = _FakeClient(_FakeMessages(chunks, create_text))
    monkeypatch.setattr(assistant, "get_client", lambda: client)
    return list(assistant.answer_stream(_portfolio(), _msgs()))


def test_clean_stream_releases_full_text(monkeypatch):
    chunks = [
        "Your portfolio is concentrated in technology. ",
        "Concentration above roughly ten percent in one name ",
        "is generally considered elevated because it raises single-stock risk.",
    ]
    events = _run(monkeypatch, chunks, create_text="unused")
    delta_text = "".join(e["text"] for e in events if e["type"] == "delta")
    assert delta_text == "".join(chunks)
    assert events[-1]["type"] == "done"
    assert events[-1]["guardrail_triggered"] is False
    assert not any(e["type"] == "guardrail" for e in events)


def test_advice_is_never_released_and_gets_replaced(monkeypatch):
    chunks = [
        "Your NVDA position is very large, ",
        "so you should trim it down to reduce risk right now.",
    ]
    events = _run(
        monkeypatch,
        chunks,
        create_text="Concentration means a single name drives much of your portfolio's moves.",
    )
    released = "".join(e["text"] for e in events if e["type"] == "delta").lower()
    assert "you should" not in released  # the forbidden phrase never leaked

    assert any(e["type"] == "guardrail" for e in events)
    replace = [e for e in events if e["type"] == "replace"]
    assert replace and "you should" not in replace[0]["text"].lower()
    assert events[-1]["type"] == "done"
    assert events[-1]["guardrail_triggered"] is True
