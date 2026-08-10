import pytest
from app.pipeline.metrics import gen_fp_name_in_gold_metrics, gen_duplicated_cluster_metrics

# -------------------- FP Name-in-Gold Tests --------------------

def test_fp_name_in_gold_none():
    """Keine FPs haben namen im goldstandard → rate = 0."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER", "aliases": []},
        {"id": 2, "name": "bob", "type": "PER", "aliases": ["bobby"]},
    ]
    predicted = [
        {"name": "charlie", "type": "PER"},   # FP, name nicht in gold
        {"name": "david", "type": "LOC"},     # FP, name nicht in gold
    ]
    resolved = {("charlie", "PER"): -1, ("david", "LOC"): -1}
    metrics = gen_fp_name_in_gold_metrics(resolved, predicted, gold)
    assert metrics["fp_total"] == 2
    assert metrics["fp_name_in_gold"] == 0
    assert metrics["name_in_gold_rate"] == 0.0

def test_fp_name_in_gold_all():
    """Alle FPs haben namen im goldstandard (falscher typ) → rate = 1."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER", "aliases": []},
        {"id": 2, "name": "paris", "type": "LOC", "aliases": []},
    ]
    predicted = [
        {"name": "alice", "type": "LOC"},     # FP, name existiert aber typ falsch
        {"name": "paris", "type": "PER"},     # FP, name existiert aber typ falsch
    ]
    resolved = {("alice", "LOC"): -1, ("paris", "PER"): -1}
    metrics = gen_fp_name_in_gold_metrics(resolved, predicted, gold)
    assert metrics["fp_total"] == 2
    assert metrics["fp_name_in_gold"] == 2
    assert metrics["name_in_gold_rate"] == 1.0

def test_fp_name_in_gold_mixed():
    """Gemischt: teils namen in gold, teils nicht."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER", "aliases": []},
    ]
    predicted = [
        {"name": "alice", "type": "LOC"},     # FP, name in gold
        {"name": "charlie", "type": "PER"},   # FP, name nicht in gold
    ]
    resolved = {("alice", "LOC"): -1, ("charlie", "PER"): -1}
    metrics = gen_fp_name_in_gold_metrics(resolved, predicted, gold)
    assert metrics["fp_total"] == 2
    assert metrics["fp_name_in_gold"] == 1
    assert metrics["name_in_gold_rate"] == 0.5

def test_fp_name_in_gold_with_alias():
    """FP-name matched via gold-alias, nicht nur name."""
    gold = [
        {"id": 1, "name": "united states", "type": "LOC", "aliases": ["usa", "america"]},
    ]
    predicted = [
        {"name": "usa", "type": "PER"},       # FP, name via alias in gold
    ]
    resolved = {("usa", "PER"): -1}
    metrics = gen_fp_name_in_gold_metrics(resolved, predicted, gold)
    assert metrics["fp_total"] == 1
    assert metrics["fp_name_in_gold"] == 1
    assert metrics["name_in_gold_rate"] == 1.0

# -------------------- Duplicated Cluster Tests --------------------

def test_duplicated_cluster_none():
    """Kein cluster hat mehr als einen hit → rate = 0."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER"},
        {"id": 2, "name": "bob", "type": "PER"},
        {"id": 3, "name": "charlie", "type": "PER"},
    ]
    # alice hit=1, bob hit=1, charlie hit=0
    resolved = {
        ("alice", "PER"): 1,
        ("bob", "PER"): 2,
    }
    metrics = gen_duplicated_cluster_metrics(resolved, gold)
    assert metrics["total_clusters"] == 3
    assert metrics["duplicated_clusters"] == 0
    assert metrics["duplicated_rate"] == 0.0
    assert metrics["avg_hit_in_duplicated"] == 0.0

def test_duplicated_cluster_some():
    """Einige cluster haben mehrere hits."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER"},
        {"id": 2, "name": "bob", "type": "PER"},
        {"id": 3, "name": "charlie", "type": "PER"},
    ]
    # alice hit=3 (duplicated), bob hit=1, charlie hit=0
    resolved = {
        ("alice", "PER"): 1,
        ("alicia", "PER"): 1,
        ("ally", "PER"): 1,
        ("bob", "PER"): 2,
    }
    metrics = gen_duplicated_cluster_metrics(resolved, gold)
    assert metrics["total_clusters"] == 3
    assert metrics["duplicated_clusters"] == 1
    assert metrics["duplicated_rate"] == pytest.approx(1/3, 0.01)
    assert metrics["avg_hit_in_duplicated"] == 3.0

def test_duplicated_cluster_all():
    """Alle cluster haben mehrere hits."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER"},
        {"id": 2, "name": "bob", "type": "PER"},
    ]
    # alice hit=2, bob hit=2
    resolved = {
        ("alice", "PER"): 1,
        ("alicia", "PER"): 1,
        ("bob", "PER"): 2,
        ("bobby", "PER"): 2,
    }
    metrics = gen_duplicated_cluster_metrics(resolved, gold)
    assert metrics["total_clusters"] == 2
    assert metrics["duplicated_clusters"] == 2
    assert metrics["duplicated_rate"] == 1.0
    assert metrics["avg_hit_in_duplicated"] == 2.0

def test_duplicated_cluster_no_hits():
    """Keine hits auf irgendeinem cluster."""
    gold = [
        {"id": 1, "name": "alice", "type": "PER"},
    ]
    resolved = {}
    metrics = gen_duplicated_cluster_metrics(resolved, gold)
    assert metrics["total_clusters"] == 1
    assert metrics["duplicated_clusters"] == 0
    assert metrics["duplicated_rate"] == 0.0
