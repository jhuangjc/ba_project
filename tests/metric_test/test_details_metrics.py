import pytest
from app.pipeline.metrics import get_details_entities,get_details_relations, get_details_triples,map_relations_to_gold,apply_id,triples_in_gold


def test_get_details_entities_mixed():
    gold = [
        {"id": 1, "name": "Alice", "type": "PER"},
        {"id": 2, "name": "Bob", "type": "PER"},
        {"id": 3, "name": "Charlie", "type": "PER"},
    ]
    resolved= {("bbc1", "ORG"):3,
               ("bbc2", "ORG"):-1,
               ("Bob", "PER"):2}
    
    matched,unmatched, extra = get_details_entities(resolved, gold)
    assert len(matched) == 2
    assert len(unmatched) == 1
    assert len(extra) == 1

def test_get_details_relations_mixed():
    gold = ["related_to", "knows", "lives_in"]
    predicted = ["related_to", "knows", "works_for"]
    relation_matches, extra_relations = map_relations_to_gold(predicted, gold)
    matched, unmatched = get_details_relations(relation_matches, gold)
    assert len(matched) == 2
    assert len(unmatched) == 1
    assert len(extra_relations) == 1

def test_get_details_triples_mixed():
    predicted = [
        {"subject": {"name": "Alice", "type": "PER"}, "predicate": "knows", "object": {"name": "Bob", "type": "PER"}},
        {"subject": {"name": "Charlie", "type": "PER"}, "predicate": "lives_in", "object": {"name": "New York", "type": "LOC"}},
        {"subject": {"name": "David", "type": "PER"}, "predicate": "hates", "object": {"name": "Bob", "type": "PER"}},
        ]
    resolved = {("Alice", "PER"): 1,
                ("Bob", "PER"): 2,
                ("Charlie", "PER"): 3,
                ("New York", "LOC"): 4,
                ("David", "PER"): 5,
                ("CompanyX", "ORG"): 6}
    triples_with_ids = apply_id(predicted, resolved)
    goldstandard = {
        "relations": [
            {"head_id": 1, "tail_id": 2, "relation_label": "knows"},
            {"head_id": 3, "tail_id": 4, "relation_label": "lives_in"},
            {"head_id": 5, "tail_id": 6, "relation_label": "works_for"},
            {"head_id": 1, "tail_id": 6, "relation_label": "knows"}
            ]
    }
    triples_matches, extra_triples = triples_in_gold(triples_with_ids, goldstandard)
    matched, unmatched = get_details_triples(triples_matches, goldstandard)
    assert len(matched) == 2
    assert len(unmatched) == 2  
    assert len(extra_triples) == 1