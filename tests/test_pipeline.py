import pytest
from app.pipeline.refiner import refine_data

def fake_send_llm_candidates(query_item, candidates):
    #fake implementation die einfach die ersten 3 items zurückgibt, außer das query item ist unter den candidates, dann wird es übersprungen
    ret= candidates[:3]
    return ret

def test_refine_data(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    #testdaten
    data ={"entities": ["Alice Smith", "Alice S.", "Sergey","Sergay","Bob Marley","Bobby M."],
       "triples": [{"subject": "Alice Smith", "predicate": "knows", "object": "Sergey"},
                   {"subject": "Alice S.", "predicate": "knows", "object": "Sergay"},
                   {"subject": "Bob Marley", "predicate": "knows", "object": "Sergey"},
                   {"subject": "Bobby M.", "predicate": "knows", "object": "Sergay"}]}
    # execution
    result,entity_mapping,relation_mapping = refine_data(data)
    #asserts
    assert "entities" in result
    assert "triples" in result
    assert "relations" in result
    assert len(entity_mapping) > 0
    assert len(relation_mapping) > 0

def test_refine_count(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    
    #testdaten
    data ={"entities": ["Alice Smith", "Alice S.", "Sergey","Sergay","Bob Marley","Bobby M."],
       "triples": [{"subject": "Alice Smith", "predicate": "knows", "object": "Sergey"},
                   {"subject": "Alice S.", "predicate": "knows", "object": "Sergay"},
                   {"subject": "Bob Marley", "predicate": "knows", "object": "Sergey"},
                   {"subject": "Bobby M.", "predicate": "knows", "object": "Sergay"}]}
    # execution
    before_count = len(data["entities"])
    result,entity_mapping,relation_mapping = refine_data(data)
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
    with pytest.raises(ValueError, match="No entities or relations to refine."):
        result,entity_mapping,relation_mapping = refine_data(data)

def test_refine_one_entity(monkeypatch):
    monkeypatch.setattr("app.pipeline.refiner.send_llm_candidates", fake_send_llm_candidates)
    
    #testdaten
    data ={"entities": ["Alice Smith"],
       "triples": [{"subject": "Alice Smith", "predicate": "knows", "object": "Alice Smith"}],
       "relations": ["knows"]}
    # execution with raised error
    result,entity_mapping,relation_mapping = refine_data(data)
    #asserts
    assert result["entities"] == ["alice smith"]
    assert result["triples"] == [{"subject": "alice smith", "predicate": "knows", "object": "alice smith"}]
    assert result["relations"] == ["knows"]
    assert entity_mapping == {"alice smith": []}
    assert relation_mapping == {"knows": []}