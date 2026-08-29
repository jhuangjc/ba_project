"""
Batch-Skript: Führt alle Experimente aus der Registry 3× aus
und sammelt Metriken (P/R/F1) vor und nach dem Refinement.
"""
import json
import sys
import os
import traceback
from argparse import Namespace
from datetime import datetime
from pathlib import Path

# Projekt-Root + src ins sys.path, damit imports funktionieren
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app.utils.io import load_registry, RESULTS_DIR
from app.commands.run import run


def main():
    registry = load_registry()
    experiments = registry["experiments"]
    num_runs = 3

    batch_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    batch_dir = RESULTS_DIR / f"batch_{batch_ts}"
    summary = {}

    print(f"=== Starte {len(experiments)} Experimente, {num_runs}× ===\n")
    print(f"Batch-Verzeichnis: {batch_dir}\n")

    for run_idx in range(1, num_runs + 1):
        print(f"--- Run {run_idx}/{num_runs} ---")
        for exp in experiments:
            eid = exp["experiment_id"]
            run_dir = batch_dir / eid / f"run_{run_idx}"
            run_dir.mkdir(parents=True, exist_ok=True)

            print(f"  {eid} ... ", end="", flush=True)

            def run_single():
                args = Namespace(expId=eid)
                output = run(args, output_dir=run_dir)

                b = output["evaluation_results"]["metrics_before_refinement"]
                a = output["evaluation_results"]["metrics_after_refinement"]

                def extract(m):
                    return {
                        "entity_f1": m["entity_metrics"]["f1"],
                        "relation_f1": m["relation_metrics"]["f1"],
                        "triple_f1": m["triple_metrics"]["f1"],
                        "cluster_coverage": m["cluster_hit_metrics"]["coverage"],
                        "cluster_avg_hit": m["cluster_hit_metrics"]["avg_cluster_hit"],
                        "fp_name_in_gold_rate": m["fp_name_in_gold_metrics"]["name_in_gold_rate"],
                        "duplicated_rate": m["duplicated_cluster_metrics"]["duplicated_rate"],
                    }
                return extract(b), extract(a), b, a

            for attempt in (1, 2):
                try:
                    before, after, b, a = run_single()
                    summary.setdefault(eid, {})[f"run_{run_idx}"] = {
                        "before": before,
                        "after": after,
                    }
                    print(f"ok  (vor: Cov={b['cluster_hit_metrics']['coverage']:.2f} "
                          f"AvgHit={b['cluster_hit_metrics']['avg_cluster_hit']:.2f}  |  "
                          f"nach: Cov={a['cluster_hit_metrics']['coverage']:.2f} "
                          f"AvgHit={a['cluster_hit_metrics']['avg_cluster_hit']:.2f})")
                    break
                except Exception as e:
                    if attempt == 1:
                        print(f"\n    ⚠ Fehler (Wiederholung {eid} Run {run_idx}): {e}")
                        traceback.print_exc()
                    else:
                        print(f"    ✗ Fehler (endgültig {eid} Run {run_idx}): {e}")
                        summary.setdefault(eid, {})[f"run_{run_idx}"] = {
                            "before": None,
                            "after": None,
                        }

    # ---- Summary speichern ----
    summary_path = batch_dir / "summary.json"
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\nSummary gespeichert: {summary_path}")

    # ---- Zusammenfassung als Tabelle ----
    print("\n\n========== ZUSAMMENFASSUNG ==========\n")
    header = (f"{'Experiment':35s} | {'Run1 Cov':>7s} | {'Run1 #Hit':>7s} | "
              f"{'Run2 Cov':>7s} | {'Run2 #Hit':>7s} | "
              f"{'Run3 Cov':>7s} | {'Run3 #Hit':>7s}")
    sep = "-" * len(header)
    print(header)
    print(sep)

    for exp in experiments:
        eid = exp["experiment_id"]
        runs = summary.get(eid, {})
        row = f"{eid:35s}"
        for r in range(1, num_runs + 1):
            rdata = runs.get(f"run_{r}", {})
            a = rdata.get("after")
            cov = a["cluster_coverage"] if a else None
            ah  = a["cluster_avg_hit"] if a else None
            row += f" | {f'{cov:.2f}' if cov is not None else '-':>7s}"
            row += f" | {f'{ah:.2f}' if ah is not None else '-':>7s}"
        print(row)

    print(sep)
    print(f"\nAlle Ergebnisse in: {batch_dir}")


if __name__ == "__main__":
    main()
