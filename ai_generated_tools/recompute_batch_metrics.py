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
  - corrected result copies (exp/run/result_*.json, Struktur wie im Batch),
    damit avg_metrics.py unveraendert darauf laufen kann
  - corrected_metrics.json  (per-run + per-experiment, stored vs recalculated)
  - SUMMARY.md              (human-readable overview + recheck cross-check)
"""
import json
import glob
import os
import sys
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src"))

from app.pipeline.metrics import measure_data, categorize_error_sources  # noqa: E402 (aktuelle Version)

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
    warnings = []
    for f in files:
        d = json.load(open(f))
        gid = d["metadata"]["gold_id"]
        eid = d["metadata"]["experiment_id"]
        gold = load_gold(gid)
        det = d["details"]
        ev = d["evaluation_results"]

        after_pred = d["extraction_results"]

        # before-dict: relations from the stored before-details (exactly the data
        # the original run measured). Using after_pred["relations"] would silently
        # drift if refinement ever changes the relation list.
        before_strict = reconstruct_before(det["strict_before"])
        before_strict["relations"] = (
            det["strict_before"]["relations"]["matched"]
            + det["strict_before"]["relations"]["extra"])
        before_loose = reconstruct_before(det["loose_before"])
        before_loose["relations"] = (
            det["loose_before"]["relations"]["matched"]
            + det["loose_before"]["relations"]["extra"])

        # aktuelle measure_data; Daten sind bereits lowercase -> keine weitere Normalisierung
        res_strict_before = measure_data(before_strict, gold, before_refinement=False)
        res_loose_before = measure_data(before_loose, gold, before_refinement=False)
        res_after = measure_data(after_pred, gold, before_refinement=False)

        # korrigierte result-Kopie schreiben (Struktur wie im Original-Batch)
        corrected_details = {
            "strict_before": res_strict_before["strict"]["details"],
            "strict_after": res_after["strict"]["details"],
            "loose_before": res_loose_before["loose"]["details"],
            "loose_after": res_after["loose"]["details"],
        }
        copy = {
            "metadata": d["metadata"],
            "extraction_results": d["extraction_results"],
            "evaluation_results": {
                "metrics_before_refinement": res_strict_before["strict"]["metrics"],
                "metrics_after_refinement": res_after["strict"]["metrics"],
                "metrics_loose_before": res_loose_before["loose"]["metrics"],
                "metrics_loose_after": res_after["loose"]["metrics"],
                "delta_before": res_strict_before["delta"],
                "delta_after": res_after["delta"],
            },
            "details": corrected_details,
            "error_sources": categorize_error_sources(
                corrected_details["strict_before"], corrected_details["strict_after"]),
        }
        rel = os.path.relpath(f, BATCH)
        copy_path = os.path.join(OUT_DIR, rel)
        os.makedirs(os.path.dirname(copy_path), exist_ok=True)
        with open(copy_path, "w") as fh:
            json.dump(copy, fh, indent=2)

        corrected_by_sec = {
            "strict_before": extract_f1s(res_strict_before["strict"]),
            "loose_before": extract_f1s(res_loose_before["loose"]),
            "strict_after": extract_f1s(res_after["strict"]),
            "loose_after": extract_f1s(res_after["loose"]),
        }

        entry = {"experiment_id": eid, "gold_id": gid, "sections": {}}

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

            # raw pre-refinement entity list may contain duplicate (name, type) keys;
            # details only store the collapsed set -> recomputed fp_name_in_gold is based
            # on the deduped list. Warn instead of drifting silently.
            stored_fp_total = ev[mkey]["fp_name_in_gold_metrics"]["fp_total"]
            unique_extras = len(det[sec]["entities"]["extra"])
            if stored_fp_total != unique_extras:
                warnings.append(
                    f"{os.path.basename(f)} {sec}: stored fp_total={stored_fp_total} "
                    f"vs {unique_extras} unique extras (duplicate keys in raw list; "
                    f"recomputed fp_name_in_gold uses the deduped set)")

        runs[os.path.basename(f)] = entry

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
            "before": "predicted entities/triples reconstructed from details.<sec> (matched + extra); relations from details.<sec> (matched + extra)",
            "after": "extraction_results used directly",
            "computation": "aktuelle measure_data (z.B. mit One-to-One-Matching) aus src/app/pipeline/metrics.py",
            "caveats": [
                "before-sections: predicted order = matched then extra, so which duplicate lands in matched/extra may differ from the original run",
                "details (get_details_entities) und fp_name_in_gold nutzen in den Kopien noch die alte Semantik, solange die Konsistenz-Patches in metrics.py ausstehen; nach solchen Aenderungen das Tool erneut ausfuehren",
                "gold: data/goldstandard_json_flat_with_types",
            ],
        },
        "recheck_mismatches": mismatches,
        "warnings": warnings,
        "runs": runs,
    }
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(os.path.join(OUT_DIR, "corrected_metrics.json"), "w") as fh:
        json.dump(out, fh, indent=2)

    # ---- SUMMARY.md ----
    lines = [
        "# Batch metrics recalculated with current measure_data",
        "",
        f"Generated: {out['generated_at']}",
        "",
        "Stored metrics come from the old run (double-counting bugs). Corrected",
        "metrics are recalculated from the stored data with the current measure_data.",
        "",
        f"Corrected result copies: {OUT_DIR}/ (avg_metrics.py kann unveraendert auf diesem Verzeichnis laufen)",
        f"Recheck cross-check mismatches: {len(mismatches)}",
        f"Reconstruction warnings: {len(warnings)}",
    ]
    if mismatches:
        lines.append("Mismatches between rebuild and the counting-only recheck scripts:")
        for m in mismatches[:20]:
            lines.append(f"- {m['file']} {m['section']} {m['metric']}: recheck {m['recheck']:.6f} vs rebuild {m['rebuild']:.6f}")
    if warnings:
        lines.append("Warnings: reconstructed before-dict deviates from the original run's input:")
        for w in warnings:
            lines.append(f"- {w}")
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
    print(f"reconstruction warnings: {len(warnings)}")


if __name__ == "__main__":
    main()
