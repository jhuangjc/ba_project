#!/usr/bin/env python3
"""
Berechnet Durchschnittswerte (loose metrics) über alle Runs pro Experiment.
Input:  Batch-Verzeichnis (z.B. data/results/batch_20260810_024409)
Output: JSON-Datei in data/results/ mit avg before/after pro Experiment
"""
import json
import sys
from pathlib import Path
from statistics import mean


METRICS = {
    "entity_f1":        ("entity_metrics", "f1"),
    "triple_f1":        ("triple_metrics", "f1"),
    "relation_f1":      ("relation_metrics", "f1"),
    "type_error_rate":  ("fp_name_in_gold_metrics", "name_in_gold_rate"),
    "coverage":         ("cluster_hit_metrics", "coverage"),
    "avg_cluster_hit":  ("cluster_hit_metrics", "avg_cluster_hit"),
    "duplicated_rate":  ("duplicated_cluster_metrics", "duplicated_rate"),
}


def load_run_metrics(result_path):
    with open(result_path) as f:
        data = json.load(f)
    ev = data["evaluation_results"]
    return ev["metrics_loose_before"], ev["metrics_loose_after"]


def collect_batch(batch_dir: Path):
    experiments = {}
    for exp_dir in sorted(batch_dir.iterdir()):
        if not exp_dir.is_dir():
            continue
        eid = exp_dir.name
        runs = {"before": {k: [] for k in METRICS}, "after": {k: [] for k in METRICS}}

        for run_dir in sorted(exp_dir.iterdir()):
            if not run_dir.is_dir():
                continue
            result_files = list(run_dir.glob("result_*.json"))
            if not result_files:
                continue
            before, after = load_run_metrics(result_files[0])

            for name, (section, key) in METRICS.items():
                runs["before"][name].append(before[section][key])
                runs["after"][name].append(after[section][key])

        experiments[eid] = runs
    return experiments


def compute_averages(experiments):
    result = {}
    for eid, runs in experiments.items():
        result[eid] = {}
        for name in METRICS:
            b_vals = runs["before"][name]
            a_vals = runs["after"][name]
            result[eid][name] = {
                "before": mean(b_vals) if b_vals else None,
                "after":  mean(a_vals) if a_vals else None,
            }
    return result


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <batch_dir> [output.json]")
        sys.exit(1)

    batch_dir = Path(sys.argv[1])
    if not batch_dir.is_dir():
        print(f"❌ Nicht gefunden: {batch_dir}")
        sys.exit(1)

    out_path = sys.argv[2] if len(sys.argv) > 2 else f"data/results/{batch_dir.name}_avg.json"

    experiments = collect_batch(batch_dir)
    avg = compute_averages(experiments)

    with open(out_path, "w") as f:
        json.dump(avg, f, indent=2, ensure_ascii=False)

    print(f"✅ Gespeichert: {out_path}")


if __name__ == "__main__":
    main()
