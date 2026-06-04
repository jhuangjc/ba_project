from types import SimpleNamespace

from app.commands.triple_generator import gen_triples


class _FakeResponse:
    def __init__(self, content):
        self._content = content

    def raise_for_status(self):
        return None

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def test_gen_triples_returns_entities_and_triples(monkeypatch, tmp_path):
    input_file = tmp_path / "input.txt"
    input_file.write_text("Alice met Bob.", encoding="utf-8")

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")

    responses = iter(
        [
            _FakeResponse('{"entities": ["Alice", "Bob"]}'),
            _FakeResponse('{"triples": [{"subject": "Alice", "predicate": "met", "object": "Bob"}]}'),
        ]
    )

    def fake_post(*args, **kwargs):
        return next(responses)

    monkeypatch.setattr("app.commands.triple_generator.httpx.post", fake_post)

    result = gen_triples(SimpleNamespace(file=str(input_file)))

    assert result["entities"] == ["Alice", "Bob"]
    assert result["triples"][0]["subject"] == "Alice"