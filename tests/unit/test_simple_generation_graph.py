import pytest

from src.graphs.simple_generation_graph import SimpleGenerationGraph, call_model


class FakeGraph:
    def __init__(self, result):
        self._result = result
        self.last_state = None

    def invoke(self, initial_state):
        self.last_state = initial_state
        return self._result


def test_call_model_uses_response_content(monkeypatch) -> None:
    class DummyResponse:
        def __init__(self, content: str) -> None:
            self.content = content

    class DummyModel:
        def invoke(self, messages):
            return DummyResponse("ok")

    def fake_init_chat_model(_name: str):
        return DummyModel()

    monkeypatch.setattr(
        "src.graphs.simple_generation_graph.init_chat_model",
        fake_init_chat_model,
    )

    result = call_model({"messages": [{"role": "user", "content": "hi"}], "user_profile": {}})

    assert result == {"response": "ok"}


def test_invoke_returns_response_string() -> None:
    graph = SimpleGenerationGraph()
    fake_graph = FakeGraph({"response": "hello"})
    graph.graph = fake_graph

    result = graph.invoke(
        [{"role": "user", "content": "hi"}],
        {"name": "Ada"},
    )

    assert result == "hello"
    assert fake_graph.last_state["messages"] == [{"role": "user", "content": "hi"}]
    assert fake_graph.last_state["user_profile"] == {"name": "Ada"}


def test_invoke_raises_on_invalid_graph_response() -> None:
    graph = SimpleGenerationGraph()
    graph.graph = FakeGraph("not-a-dict")

    with pytest.raises(ValueError, match="invalid response"):
        graph.invoke([], {})


def test_invoke_raises_on_missing_response_string() -> None:
    graph = SimpleGenerationGraph()
    graph.graph = FakeGraph({"response": 123})

    with pytest.raises(ValueError, match="missing a response string"):
        graph.invoke([], {})
