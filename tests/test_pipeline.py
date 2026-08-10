import pytest
from app.pipeline.refiner import refine_data

def fake_send_llm_candidates(query_item, candidates, input_text):
    #fake implementation die einfach die ersten 3 items als (name, type)-tuples zurückgibt
    ret = candidates[:3]
    return [(item["name"], item["type"]) for item in ret]

def test_refine_data(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    #testdaten
    data ={
        "entities": [
            {"name": "Alice Smith", "type": "PER"},
            {"name": "Alice S.", "type": "PER"},
            {"name": "Sergey", "type": "PER"},
            {"name": "Sergay", "type": "PER"},
            {"name": "Bob Marley", "type": "PER"},
            {"name": "Bobby M.", "type": "PER"},
        ],
        "triples": [
            {"subject": {"name": "Alice Smith", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergey", "type": "PER"}},
            {"subject": {"name": "Alice S.", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergay", "type": "PER"}},
            {"subject": {"name": "Bob Marley", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergey", "type": "PER"}},
            {"subject": {"name": "Bobby M.", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergay", "type": "PER"}},
        ],
        "relations": ["knows"]}
    # execution
    result, entity_mapping = refine_data(data, "Test input text for context")
    #asserts
    assert "entities" in result
    assert "triples" in result
    assert "relations" in result
    assert len(entity_mapping) > 0

def test_refine_count(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    
    #testdaten
    data ={
        "entities": [
            {"name": "Alice Smith", "type": "PER"},
            {"name": "Alice S.", "type": "PER"},
            {"name": "Sergey", "type": "PER"},
            {"name": "Sergay", "type": "PER"},
            {"name": "Bob Marley", "type": "PER"},
            {"name": "Bobby M.", "type": "PER"},
        ],
        "triples": [
            {"subject": {"name": "Alice Smith", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergey", "type": "PER"}},
            {"subject": {"name": "Alice S.", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergay", "type": "PER"}},
            {"subject": {"name": "Bob Marley", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergey", "type": "PER"}},
            {"subject": {"name": "Bobby M.", "type": "PER"}, "predicate": "knows", "object": {"name": "Sergay", "type": "PER"}},
        ],
        "relations": ["knows"]}
    # execution
    before_count = len(data["entities"])
    result, entity_mapping = refine_data(data, "Test input text for context")
    after_count = len(result["entities"])

    #asserts
    assert after_count < before_count

def test_refine_empty_entities(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    
    #testdaten
    data ={"entities": [],
       "triples": [],
       "relations": []}
    # execution with raised error
    with pytest.raises(ValueError, match="No entities to refine."):
        result, entity_mapping = refine_data(data, "Test input text for context")

def test_refine_one_entity(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    
    #testdaten
    data ={
        "entities": [{"name": "Alice Smith", "type": "PER"}],
        "triples": [{"subject": {"name": "Alice Smith", "type": "PER"}, "predicate": "knows", "object": {"name": "Alice Smith", "type": "PER"}}],
        "relations": ["knows"]}
    # execution
    result, entity_mapping = refine_data(data, "Test input text for context")
    #asserts
    assert result["entities"] == [{"name": "alice smith", "type": "PER"}]
    assert result["triples"] == [{"subject": {"name": "alice smith", "type": "PER"}, "predicate": "knows", "object": {"name": "alice smith", "type": "PER"}}]
    assert result["relations"] == ["knows"]
    assert entity_mapping == {("alice smith", "PER"): []}