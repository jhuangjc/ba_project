"""
Tests für ai_generated_tools/avg_metrics.py — Durchschnittsberechnung über Batch-Runs.
"""
import json
import sys
import os
import pytest
from pathlib import Path
from statistics import mean

# Projekt-Root ins sys.path, damit ai_generated_tools importierbar ist
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from ai_generated_tools.avg_metrics import load_run_metrics, collect_batch, compute_averages, METRICS


# ── Hilfsfunktion: Mini-Batch-Struktur im tmp_path aufbauen ──

def make_result_json(entity_f1_before, entity_f1_after,
                     triple_f1_before, triple_f1_after,
                     relation_f1_before, relation_f1_after,
                     type_err_before, type_err_after,
                     coverage_before, coverage_after,
                     avg_hit_before, avg_hit_after,
                     dup_rate_before, dup_rate_after):
    """Baut eine result.json mit allen METRICS-Feldern (loose only)."""
    return {
        "evaluation_results": {
            "metrics_loose_before": {
                "entity_metrics":           {"f1": entity_f1_before},
                "triple_metrics":           {"f1": triple_f1_before},
                "relation_metrics":         {"f1": relation_f1_before},
                "fp_name_in_gold_metrics":  {"name_in_gold_rate": type_err_before},
                "cluster_hit_metrics":      {"coverage": coverage_before,
                                             "avg_cluster_hit": avg_hit_before},
                "duplicated_cluster_metrics":{"duplicated_rate": dup_rate_before},
            },
            "metrics_loose_after": {
                "entity_metrics":           {"f1": entity_f1_after},
                "triple_metrics":           {"f1": triple_f1_after},
                "relation_metrics":         {"f1": relation_f1_after},
                "fp_name_in_gold_metrics":  {"name_in_gold_rate": type_err_after},
                "cluster_hit_metrics":      {"coverage": coverage_after,
                                             "avg_cluster_hit": avg_hit_after},
                "duplicated_cluster_metrics":{"duplicated_rate": dup_rate_after},
            },
        }
    }


def write_run(batch_dir: Path, exp_id: str, run_idx: int, data: dict):
    """Schreibt eine result_*.json in batch_dir/exp_id/run_N/."""
    run_dir = batch_dir / exp_id / f"run_{run_idx}"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = run_dir / f"result_{exp_id}_run{run_idx}.json"
    with open(path, "w") as f:
        json.dump(data, f)


# ── Fixtures ──

@pytest.fixture
def single_exp_batch(tmp_path):
    """Ein Experiment (clean_00) mit 3 identischen Runs."""
    batch = tmp_path / "batch_test"
    for run_idx in range(1, 4):
        write_run(batch, "clean_00", run_idx,
                  make_result_json(0.8, 0.7,  0.5, 0.4,  0.9, 0.9,
                                   0.3, 0.3,  0.6, 0.6,  1.2, 1.2,
                                   0.1, 0.0))
    return batch


@pytest.fixture
def multi_exp_batch(tmp_path):
    """Drei Experimente mit je 2 Runs, unterschiedliche Werte."""
    batch = tmp_path / "batch_multi"

    # clean_00: zwei Runs mit Werten [1, 2] → avg=1.5
    for run_idx, (ef, tf, rf, te, cov, hit, dup) in enumerate([
        (1.0, 2.0, 3.0, 0.1, 0.5, 0.6, 0.2),
        (2.0, 3.0, 4.0, 0.2, 0.6, 0.7, 0.3),
    ], start=1):
        write_run(batch, "clean_00", run_idx,
                  make_result_json(ef, ef, tf, tf, rf, rf,
                                   te, te, cov, cov, hit, hit,
                                   dup, dup))

    # clean_01: zwei Runs mit Werten [10, 20] → avg=15
    for run_idx, (ef, tf, rf, te, cov, hit, dup) in enumerate([
        (10.0, 20.0, 30.0, 0.5, 0.8, 0.9, 0.1),
        (20.0, 30.0, 40.0, 0.6, 0.9, 1.0, 0.2),
    ], start=1):
        write_run(batch, "clean_01", run_idx,
                  make_result_json(ef, ef, tf, tf, rf, rf,
                                   te, te, cov, cov, hit, hit,
                                   dup, dup))

    return batch


# ── Tests: load_run_metrics ──

def test_load_run_metrics_returns_loose_only(tmp_path):
    data = make_result_json(0.8, 0.7,  0.5, 0.4,  0.9, 0.9,
                            0.3, 0.3,  0.6, 0.6,  1.2, 1.2,
                            0.1, 0.0)
    path = tmp_path / "test.json"
    with open(path, "w") as f:
        json.dump(data, f)

    before, after = load_run_metrics(path)
    assert before["entity_metrics"]["f1"] == 0.8
    assert after["entity_metrics"]["f1"] == 0.7
    assert before["triple_metrics"]["f1"] == 0.5
    assert after["duplicated_cluster_metrics"]["duplicated_rate"] == 0.0


# ── Tests: collect_batch ──

def test_collect_single_experiment_three_runs(single_exp_batch):
    exps = collect_batch(single_exp_batch)
    assert "clean_00" in exps
    runs = exps["clean_00"]
    # Jede Metrik sollte 3 Werte haben
    assert len(runs["before"]["entity_f1"]) == 3
    assert len(runs["after"]["entity_f1"]) == 3


def test_collect_multi_experiment(multi_exp_batch):
    exps = collect_batch(multi_exp_batch)
    assert set(exps.keys()) == {"clean_00", "clean_01"}
    assert len(exps["clean_00"]["before"]["entity_f1"]) == 2
    assert len(exps["clean_01"]["before"]["entity_f1"]) == 2


def test_collect_skips_non_dirs(tmp_path):
    """Dateien im Batch-Root werden ignoriert."""
    batch = tmp_path / "batch_junk"
    batch.mkdir()
    (batch / "README.txt").write_text("noise")
    exps = collect_batch(batch)
    assert exps == {}


# ── Tests: compute_averages ──

def test_compute_average_two_runs(multi_exp_batch):
    exps = collect_batch(multi_exp_batch)
    avg = compute_averages(exps)

    # clean_00: [1.0, 2.0] → avg before/after = 1.5
    assert avg["clean_00"]["entity_f1"]["before"] == 1.5
    assert avg["clean_00"]["entity_f1"]["after"] == 1.5
    # clean_00: triple [2.0, 3.0] → avg = 2.5
    assert avg["clean_00"]["triple_f1"]["before"] == 2.5
    # clean_00: type_error [0.1, 0.2] → avg = 0.15
    assert avg["clean_00"]["type_error_rate"]["before"] == pytest.approx(0.15)

    # clean_01: [10.0, 20.0] → avg = 15.0
    assert avg["clean_01"]["entity_f1"]["before"] == 15.0
    assert avg["clean_01"]["relation_f1"]["before"] == 35.0  # [30, 40]


def test_compute_average_empty_lists(tmp_path):
    """Leere Wertelisten → None."""
    exps = {"empty_exp": {"before": {k: [] for k in METRICS},
                          "after":  {k: [] for k in METRICS}}}
    avg = compute_averages(exps)
    assert avg["empty_exp"]["entity_f1"]["before"] is None
    assert avg["empty_exp"]["entity_f1"]["after"] is None


def test_avg_matches_manual_mean(single_exp_batch):
    """Kontrolliert: mean() über die Rohwerte muss mit avg übereinstimmen."""
    exps = collect_batch(single_exp_batch)
    avg = compute_averages(exps)

    runs = exps["clean_00"]
    for name in METRICS:
        expected_before = mean(runs["before"][name])
        expected_after  = mean(runs["after"][name])
        assert avg["clean_00"][name]["before"] == expected_before
        assert avg["clean_00"][name]["after"]  == expected_after
