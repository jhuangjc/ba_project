"""
Debug-Script: Wiederholt ein oder mehrere Experimente N×
und druckt volle Tracebacks bei Fehlern.
"""
import sys
import os
import traceback
from argparse import ArgumentParser, Namespace
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app.utils.io import RESULTS_DIR
from app.commands.run import run


def main():
    parser = ArgumentParser(
        description="Debug: Experimente N× wiederholen mit vollen Tracebacks"
    )
    parser.add_argument(
        "experiments", nargs="+",
        help="Experiment-IDs (z.B. coherence_block_shuffle proforms_deleted)"
    )
    parser.add_argument(
        "-n", "--runs", type=int, default=5,
        help="Anzahl Wiederholungen pro Experiment (default: 5)"
    )
    args = parser.parse_args()

    debug_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    debug_dir = RESULTS_DIR / f"debug_{debug_ts}"
    debug_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== Debug: {len(args.experiments)} Experiment(e) × {args.runs} Runs ===\n")
    print(f"Debug-Verzeichnis: {debug_dir}\n")

    results = {}

    for eid in args.experiments:
        results[eid] = {"success": 0, "failed": 0, "errors": []}
        exp_dir = debug_dir / eid
        exp_dir.mkdir(parents=True, exist_ok=True)

        for run_idx in range(1, args.runs + 1):
            run_dir = exp_dir / f"run_{run_idx}"
            print(f"  {eid} Run {run_idx}/{args.runs} ... ", end="", flush=True)

            try:
                run_args = Namespace(expId=eid)
                output = run(run_args, output_dir=run_dir)

                b = output["evaluation_results"]["metrics_before_refinement"]
                a = output["evaluation_results"]["metrics_after_refinement"]
                results[eid]["success"] += 1
                print(f"ok  (EntF1 vor={b['entity_metrics']['f1']:.3f} "
                      f"nach={a['entity_metrics']['f1']:.3f}  "
                      f"FPinGold={b['fp_name_in_gold_metrics']['name_in_gold_rate']:.2f}->{a['fp_name_in_gold_metrics']['name_in_gold_rate']:.2f}  "
                      f"DupClust={b['duplicated_cluster_metrics']['duplicated_rate']:.2f}->{a['duplicated_cluster_metrics']['duplicated_rate']:.2f})")

            except Exception as e:
                results[eid]["failed"] += 1
                results[eid]["errors"].append({
                    "run": run_idx,
                    "error": str(e),
                })
                print(f"FEHLER")
                print(f"    ── Traceback ──")
                traceback.print_exc()
                print(f"    ───────────────")

    # ---- Zusammenfassung ----
    print(f"\n=== Zusammenfassung ===")
    for eid, r in results.items():
        total = r["success"] + r["failed"]
        rate = r["success"] / total * 100 if total > 0 else 0
        print(f"  {eid}: {r['success']}/{total} ok ({rate:.0f}%)")
        if r["failed"]:
            print(f"    Fehler in Runs: {[e['run'] for e in r['errors']]}")

    print(f"\nAlle Debug-Ergebnisse in: {debug_dir}")


if __name__ == "__main__":
    main()
