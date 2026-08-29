#!/usr/bin/env python3
"""
Show all metrics from a given experiment in the batch results JSON.

Usage:
    python show_experiment.py <experiment_name>
    python show_experiment.py --list          # list all available experiments
    python show_experiment.py --diff          # show before/after delta for all experiments
"""

import json
import sys
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "batch_20260810_204548_avg.json"

METRIC_LABELS = {
    "entity_f1":         "Entity F1",
    "triple_f1":         "Triple F1",
    "relation_f1":       "Relation F1",
    "type_error_rate":   "Type Error Rate",
    "coverage":          "Coverage",
    "avg_cluster_hit":   "Avg Cluster Hit",
    "duplicated_rate":   "Duplicated Rate",
}


def load_data() -> dict:
    with open(DATA_FILE) as f:
        return json.load(f)


def list_experiments(data: dict) -> None:
    print(f"Available experiments ({len(data)}):\n")
    for name in sorted(data):
        print(f"  {name}")


def show_experiment(data: dict, name: str) -> None:
    if name not in data:
        print(f"Experiment '{name}' not found.", file=sys.stderr)
        print(f"Use --list to see available experiments.", file=sys.stderr)
        sys.exit(1)

    exp = data[name]
    print(f"\n{'=' * 60}")
    print(f"  Experiment: {name}")
    print(f"{'=' * 60}\n")
    print(f"  {'Metric':<22} {'Before':>10} {'After':>10}")
    print(f"  {'-' * 22} {'-' * 10} {'-' * 10}")

    for key, label in METRIC_LABELS.items():
        if key in exp:
            before = exp[key]["before"]
            after = exp[key]["after"]
            print(f"  {label:<22} {before:>10.3f} {after:>10.3f}")

    print()


def show_all_diffs(data: dict) -> None:
    """Print a compact overview of before→after deltas for all experiments."""
    print(f"\n{'Experiment':<36} {'Entity F1':>18} {'Triple F1':>18} {'Relation F1':>18}")
    print(f"{'─' * 36} {'─' * 18} {'─' * 18} {'─' * 18}")

    for name in sorted(data):
        exp = data[name]
        e_before = exp["entity_f1"]["before"]
        e_after  = exp["entity_f1"]["after"]
        t_before = exp["triple_f1"]["before"]
        t_after  = exp["triple_f1"]["after"]
        r_before = exp["relation_f1"]["before"]
        r_after  = exp["relation_f1"]["after"]

        e_str = f"{e_before:.3f} → {e_after:.3f}"
        t_str = f"{t_before:.3f} → {t_after:.3f}"
        r_str = f"{r_before:.3f} → {r_after:.3f}"

        print(f"  {name:<34} {e_str:>18} {t_str:>18} {r_str:>18}")

    print()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python show_experiment.py <name> | --list | --diff", file=sys.stderr)
        sys.exit(1)

    data = load_data()
    arg = sys.argv[1]

    if arg == "--list":
        list_experiments(data)
    elif arg == "--diff":
        show_all_diffs(data)
    else:
        show_experiment(data, arg)


if __name__ == "__main__":
    main()
