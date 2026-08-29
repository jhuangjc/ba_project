#!/usr/bin/env python3
"""
Recalculate the batch metrics using the CURRENT metric code from
src/app/pipeline/metrics.py — without re-running the LLM pipeline.

The predicted data is reconstructed from the stored result JSONs, then the
current measure_data is applied. Run this tool whenever the metric functions
are adjusted (e.g. the one-to-one matching fixes) to produce corrected
numbers for an already stored batch.

Writes into a separate directory, never touches the original batch.

Inputs:
  - data/thesis_results/batch_20260810_204548/**/result_*.json
  - data/goldstandard_json_flat_with_types/gold_0X.json

Outputs (separate dir, by default batch_..._corrected/):
  - corrected_metrics.json  (per-run + per-experiment, stored vs recalculated)
  - SUMMARY.md              (human-readable overview + recheck cross-check)
"""
import json
import glob
import os
import sys
from datetime import datetime
from pathlib import Path
from statistics import mean

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app.pipeline.metrics import measure_data  # noqa: E402 (aktuelle Version)

BATCH = "data/thesis_results/batch_20260810_204548"
GOLD_DIR = "data/goldstandard_json_flat_with_types"
OUT_DIR = "data/thesis_results/batch_20260810_204548_corrected"

SECTIONS = {
    "strict_before": "metrics_before_refinement",
    "strict_after":  "metrics_after_refinement",
    "loose_before":  "metrics_loose_before",
    "loose_after":   "metrics_loose_after",
}


def load_gold(gold_id):
    gs = json.load(open(os.path.join(GOLD_DIR, f"{gold_id}.json")))
    return gs


def reconstruct_before(details):
    """Reconstruct the pre-refinement predicted dict from the stored details.

    matched + extra cover all predicted items; relations are unchanged by
    refinement, so they come from extraction_results (passed by caller).
    """
    det_entities = details["entities"]
    det_triples = details["triples"]

    entities = [{"name": x["name"], "type": x["type"]} for x in det_entities["matched"]]
    entities += [{"name": x["name"], "type": x["type"]} for x in det_entities["extra"]]

    triples = []
    for x in det_triples["matched"] + det_triples["extra"]:
        triples.append({
            "subject": {"name": x["subject"]["name"], "type": x["subject"]["type"]},
            "predicate": x["predicate"],
            "object": {"name": x["object"]["name"], "type": x["object"]["type"]},
        })
    return {"entities": entities, "triples": triples}


def f1_of(metrics, which):
    return metrics[which]["f1"]


def extract_f1s(section_result):
    m = section_result["metrics"]
    return {
        "entity_f1": m["entity_metrics"]["f1"],
        "relation_f1": m["relation_metrics"]["f1"],
        "triple_f1": m["triple_metrics"]["f1"],
    }


def main():
    files = sorted(glob.glob(os.path.join(BATCH, "**", "result_*.json"), recursive=True))

    runs = {}
    per_exp = {}
    for f in files:
        d = json.load(open(f))
        gid = d["metadata"]["gold_id"]
        eid = d["metadata"]["experiment_id"]
        gold = load_gold(gid)
        det = d["details"]
        ev = d["evaluation_results"]

        after_pred = d["extraction_results"]

        # before-dict needs relations from extraction_results
        before_strict = reconstruct_before(det["strict_before"])
        before_strict["relations"] = after_pred["relations"]
        before_loose = reconstruct_before(det["loose_before"])
        before_loose["relations"] = after_pred["relations"]

        # aktuelle measure_data; Daten sind bereits lowercase -> keine weitere Normalisierung
        res_strict_before = measure_data(before_strict, gold, before_refinement=False)
        res_loose_before = measure_data(before_loose, gold, before_refinement=False)
        res_after = measure_data(after_pred, gold, before_refinement=False)

        corrected_by_sec = {
            "strict_before": extract_f1s(res_strict_before["strict"]),
            "loose_before": extract_f1s(res_loose_before["loose"]),
            "strict_after": extract_f1s(res_after["strict"]),
            "loose_after": extract_f1s(res_after["loose"]),
        }

        entry = {"experiment_id": eid, "gold_id": gid, "sections": {}}
        per_exp.setdefault(eid, {s: {"stored": [], "corrected": []} for s in SECTIONS})

        for sec, mkey in SECTIONS.items():
            stored = {
                "entity_f1": ev[mkey]["entity_metrics"]["f1"],
                "relation_f1": ev[mkey]["relation_metrics"]["f1"],
                "triple_f1": ev[mkey]["triple_metrics"]["f1"],
            }
            corrected = corrected_by_sec[sec]
            entry["sections"][sec] = {
                "stored": {k: round(v, 6) for k, v in stored.items()},
                "corrected": {k: round(v, 6) for k, v in corrected.items()},
                "delta": {k: round(corrected[k] - stored[k], 6) for k in stored},
            }
            per_exp[eid][sec]["stored"].append(stored["entity_f1"])
            per_exp[eid][sec]["corrected"].append(corrected["entity_f1"])

        runs[os.path.basename(f)] = entry

    # per-experiment averages (entity F1, loose blocks like avg_metrics.py)
    avg = {}
    for eid, secs in per_exp.items():
        avg[eid] = {}
        for sec in SECTIONS:
            if secs[sec]["stored"]:
                avg[eid][sec] = {
                    "stored_mean": round(mean(secs[sec]["stored"]), 6),
                    "corrected_mean": round(mean(secs[sec]["corrected"]), 6),
                    "delta": round(mean(secs[sec]["corrected"]) - mean(secs[sec]["stored"]), 6),
                }
            else:
                avg[eid][sec] = {"stored_mean": None, "corrected_mean": None, "delta": None}

    # cross-check against the recheck scripts (counting-only correction)
    mismatches = []
    for which, key in (("entity", "entity_f1"), ("triple", "triple_f1")):
        recheck = json.load(open(os.path.join(PROJECT_ROOT, "data", "results",
                                              f"{which}_f1_recheck", f"corrected_{which}_f1.json")))
        for fname, r in recheck["runs"].items():
            for sec, sv in r["sections"].items():
                if abs(sv["corrected"]["f1"] - runs[fname]["sections"][sec]["corrected"][key]) > 1e-6:
                    mismatches.append({
                        "file": fname, "section": sec, "metric": which,
                        "recheck": sv["corrected"]["f1"],
                        "rebuild": runs[fname]["sections"][sec]["corrected"][key],
                    })

    out = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "batch_dir": BATCH,
        "method": {
            "before": "predicted entities/triples reconstructed from details.<sec> (matched + extra); relations from extraction_results",
            "after": "extraction_results used directly",
            "computation": "aktuelle measure_data (z.B. mit One-to-One-Matching) aus src/app/pipeline/metrics.py",
            "caveats": [
                "before-sections: predicted order = matched then extra, so which duplicate lands in matched/extra may differ from the original run",
                "gold: data/goldstandard_json_flat_with_types",
            ],
        },
        "recheck_mismatches": mismatches,
        "runs": runs,
        "experiment_averages": avg,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "corrected_metrics.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # ---- SUMMARY.md (loose blocks) ----
    lines = [
        "# Batch metrics recalculated with current measure_data",
        "",
        f"Generated: {out['generated_at']}",
        "",
        "Stored metrics come from the old run (double-counting bugs). Corrected",
        "metrics are recalculated from the stored data with the current measure_data.",
        "Thesis aggregation uses LOOSE blocks; table shows entity F1.",
        "",
        "| Experiment | stored before/after | corrected before/after | delta before | delta after |",
        "|---|---|---|---|---|",
    ]
    for eid in sorted(avg):
        lb = avg[eid]["loose_before"]
        la = avg[eid]["loose_after"]
        lines.append(
            f"| {eid} | {lb['stored_mean']:.4f} / {la['stored_mean']:.4f} | "
            f"{lb['corrected_mean']:.4f} / {la['corrected_mean']:.4f} | "
            f"{lb['delta']:+.4f} | {la['delta']:+.4f} |"
        )
    lines += [
        "",
        f"Recheck cross-check mismatches: {len(mismatches)}",
    ]
    if mismatches:
        lines.append("Mismatches between rebuild and the counting-only recheck scripts:")
        for m in mismatches[:20]:
            lines.append(f"- {m['file']} {m['section']} {m['metric']}: recheck {m['recheck']:.6f} vs rebuild {m['rebuild']:.6f}")
    lines += [
        "",
        "Full per-run numbers: corrected_metrics.json",
        "",
    ]
    with open(os.path.join(OUT_DIR, "SUMMARY.md"), "w") as fh:
        fh.write("\n".join(lines))

    print(f"wrote: {OUT_DIR}/corrected_metrics.json")
    print(f"wrote: {OUT_DIR}/SUMMARY.md")
    print(f"files processed: {len(files)}")
    print(f"recheck mismatches: {len(mismatches)}")


if __name__ == "__main__":
    main()
