"""Functionality tests for the core F1 metric functions.

Covers the calculation helpers and the three metric generators:
  calculate_precision / calculate_recall / calculate_f1
  gen_entity_metrics
  gen_relation_metrics
  gen_triple_metrics

The triple tests assert one-to-one matching semantics (each gold relation can be
matched by at most one predicted triple). Tests that encode this intended
behavior are marked with the reason string where the current implementation
diverges.
"""
import pytest

from app.pipeline.metrics import (
    calculate_f1,
    calculate_precision,
    calculate_recall,
    gen_entity_metrics,
    gen_relation_metrics,
    gen_triple_metrics,
)


# -------------------- calculation helpers --------------------

def test_calculate_precision_normal():
    assert calculate_precision(3, 2) == pytest.approx(0.6)


def test_calculate_precision_zero_denominator():
    assert calculate_precision(0, 0) == 0.0


def test_calculate_precision_no_tp():
    assert calculate_precision(0, 5) == 0.0


def test_calculate_recall_normal():
    assert calculate_recall(3, 2) == pytest.approx(0.6)


def test_calculate_recall_zero_denominator():
    assert calculate_recall(0, 0) == 0.0


def test_calculate_recall_no_tp():
    assert calculate_recall(0, 5) == 0.0


def test_calculate_f1_normal():
    assert calculate_f1(0.6, 0.4) == pytest.approx(0.48)


def test_calculate_f1_both_zero():
    assert calculate_f1(0.0, 0.0) == 0.0


def test_calculate_f1_mixed():
    # P=1, R=0.5 -> F1 = 2*0.5/1.5 = 2/3
    assert calculate_f1(1.0, 0.5) == pytest.approx(2 / 3)


# -------------------- entity metrics --------------------

def test_gen_entity_metrics_all_matched():
    resolved = {("alice", "PER"): 1, ("bob", "PER"): 2}
    gold = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
    m = gen_entity_metrics(resolved, gold)
    assert m["true_positives"] == 2
    assert m["false_positives"] == 0
    assert m["false_negatives"] == 0
    assert m["precision"] == 1.0
    assert m["recall"] == 1.0
    assert m["f1"] == 1.0


def test_gen_entity_metrics_mixed():
    resolved = {("alice", "PER"): 1, ("carol", "PER"): -1}
    gold = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
    m = gen_entity_metrics(resolved, gold)
    assert m["true_positives"] == 1
    assert m["false_positives"] == 1
    assert m["false_negatives"] == 1
    assert m["precision"] == pytest.approx(0.5)
    assert m["recall"] == pytest.approx(0.5)
    assert m["f1"] == pytest.approx(0.5)


def test_gen_entity_metrics_none_matched():
    resolved = {("x", "PER"): -1, ("y", "ORG"): -1}
    gold = [{"id": 1, "name": "alice"}, {"id": 2, "name": "bob"}]
    m = gen_entity_metrics(resolved, gold)
    assert m["true_positives"] == 0
    assert m["false_positives"] == 2
    assert m["false_negatives"] == 2
    assert m["precision"] == 0.0
    assert m["recall"] == 0.0
    assert m["f1"] == 0.0


# -------------------- relation metrics --------------------

def test_gen_relation_metrics_exact():
    metrics, details = gen_relation_metrics(["knows", "lives_in"], ["knows", "lives_in"])
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["f1"] == 1.0
    assert len(details["matched"]) == 2
    assert len(details["unmatched"]) == 0
    assert len(details["extra"]) == 0


def test_gen_relation_metrics_mixed():
    metrics, _ = gen_relation_metrics(["knows", "works_for"], ["knows", "lives_in"])
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["f1"] == pytest.approx(0.5)


def test_gen_relation_metrics_duplicate_predicted():
    # duplicated correct relation: one TP, one extra FP
    metrics, details = gen_relation_metrics(["knows", "knows"], ["knows"])
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == pytest.approx(2 / 3)
    assert len(details["extra"]) == 1


def test_gen_relation_metrics_both_empty():
    metrics, _ = gen_relation_metrics([], [])
    assert metrics["true_positives"] == 0
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["f1"] == 0.0


# -------------------- triple metrics --------------------

def make_triple(subj, subj_type, pred, obj, obj_type):
    return {
        "subject": {"name": subj, "type": subj_type},
        "predicate": pred,
        "object": {"name": obj, "type": obj_type},
    }


def make_gold(relations):
    return {"relations": [{"head_id": h, "tail_id": t, "relation_label": r} for h, t, r in relations]}


def test_gen_triple_metrics_all_matched():
    triples = [
        make_triple("Alice", "PER", "knows", "Bob", "PER"),
        make_triple("Bob", "PER", "lives_in", "Berlin", "LOC"),
    ]
    resolved = {("Alice", "PER"): 1, ("Bob", "PER"): 2, ("Berlin", "LOC"): 4}
    gold = make_gold([(1, 2, "knows"), (2, 4, "lives_in")])
    metrics, _ = gen_triple_metrics(triples, resolved, gold)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 0
    assert metrics["false_negatives"] == 0
    assert metrics["f1"] == 1.0


def test_gen_triple_metrics_mixed():
    triples = [
        make_triple("Alice", "PER", "knows", "Bob", "PER"),
        make_triple("Alice", "PER", "hates", "Bob", "PER"),
        make_triple("Bob", "PER", "lives_in", "Berlin", "LOC"),
    ]
    resolved = {("Alice", "PER"): 1, ("Bob", "PER"): 2, ("Berlin", "LOC"): 4}
    gold = make_gold([(1, 2, "knows"), (2, 4, "lives_in"), (1, 5, "works_for")])
    metrics, _ = gen_triple_metrics(triples, resolved, gold)
    assert metrics["true_positives"] == 2
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["f1"] == pytest.approx(2 / 3)


def test_gen_triple_metrics_unresolved_entity():
    triples = [make_triple("Alice", "PER", "knows", "Bob", "PER")]
    # Bob missing from resolved -> id -1 -> no match possible
    resolved = {("Alice", "PER"): 1}
    gold = make_gold([(1, 2, "knows")])
    metrics, _ = gen_triple_metrics(triples, resolved, gold)
    assert metrics["true_positives"] == 0
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["f1"] == 0.0


def test_gen_triple_metrics_duplicate_predicted_triples():
    """Two identical predicted triples vs one gold relation.

    Intended one-to-one semantics: one TP, the copy is an FP.
    KNOWN BUG: current triples_in_gold double-matches the same gold relation,
    giving tp=3/fn=-1 and F1 > 1.
    """
    triples = [
        make_triple("Alice", "PER", "knows", "Bob", "PER"),
        make_triple("Alice", "PER", "knows", "Bob", "PER"),
        make_triple("Alice", "PER", "lives_in", "Berlin", "LOC"),
    ]
    resolved = {("Alice", "PER"): 1, ("Bob", "PER"): 2, ("Berlin", "LOC"): 3}
    gold = make_gold([(1, 2, "knows"), (1, 3, "lives_in")])
    metrics, _ = gen_triple_metrics(triples, resolved, gold)
    assert metrics["true_positives"] == 2  # one knows + one lives_in
    assert metrics["false_positives"] == 1  # duplicate copy
    assert metrics["false_negatives"] == 0
    assert metrics["precision"] == pytest.approx(2 / 3)
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == pytest.approx(0.8)


def test_gen_triple_metrics_alias_variants_same_gold_id():
    """Two name variants resolving to the same gold id must not both match the
    same gold relation.

    KNOWN BUG: current triples_in_gold matches both against the same gold
    relation, giving tp=2/fn=0 and F1=1.0 instead of 0.5.
    """
    triples = [
        make_triple("Blackadder", "MISC", "present in work", "BBC1", "ORG"),
        make_triple("Blackadder Goes Forth", "MISC", "present in work", "BBC1", "ORG"),
    ]
    # both names resolve to gold entity 2 (name + alias)
    resolved = {("Blackadder", "MISC"): 2, ("Blackadder Goes Forth", "MISC"): 2, ("BBC1", "ORG"): 4}
    gold = make_gold([(2, 4, "present in work"), (2, 4, "original network")])
    metrics, _ = gen_triple_metrics(triples, resolved, gold)
    assert metrics["true_positives"] == 1
    assert metrics["false_positives"] == 1
    assert metrics["false_negatives"] == 1
    assert metrics["precision"] == pytest.approx(0.5)
    assert metrics["recall"] == pytest.approx(0.5)
    assert metrics["f1"] == pytest.approx(0.5)
