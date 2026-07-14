from app.utils.io import load_input_file, load_registry, load_goldstandard
from app.pipeline.triple_generator import gen_triples
from app.pipeline.refiner import refine_data
from app.pipeline.metrics import measure_data, generate_combined_metrics

from datetime import datetime
from pathlib import Path
import json

def run(args):
    ex_id = args.expId
    registry_data = load_registry()
    experiments = registry_data["experiments"]
    exp = None
    for e in experiments:
        if e["experiment_id"] == ex_id:
            exp = e
            break
    if exp is None:
        raise ValueError(f"{ex_id} nicht in der Registry")

    # lade den input text
    input_text = load_input_file(exp)

    goldstandard = load_goldstandard(exp)
    # generiere die Tripel
    triples_result = gen_triples(input_text,goldstandard)
    # messungen vor dem Refinement
    metrics_before,_ = measure_data(triples_result, goldstandard, before_refinement=True)

    # verfeinere die Daten
    refined_result, entity_mapping, relation_mapping = refine_data(triples_result)
    
    # messingen nach dem Refinement
    metrics_after,details = measure_data(refined_result, goldstandard, before_refinement=False)

    #generiere die Metriken
    res=generate_combined_metrics(metrics_before, metrics_after, goldstandard, entity_mapping)
    output ={
        "metadata": {
            "experiment_id": ex_id,
            "input_type": exp["input_type"],
            "source_group": exp["source_group"],
            "gold_id": exp["gold_id"]
        },
        "extraction_results": {
            "entities": refined_result["entities"],
            "triples": refined_result["triples"],
            "relations": refined_result["relations"]
        },
        "evaluation_results": {
            "metrics_before_refinement": metrics_before,
            "metrics_after_refinement": metrics_after,
            "combined_metrics": res
        },
        "details": {
            "entities": details["entities"],
            "triples": details["triples"],
            "relations": details["relations"]
        }
    }
    #speicher die Ergebnisse in einer Datei
    result_dir = Path(__file__).resolve().parent.parent.parent.parent/"data/results"
    result_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{ex_id}_{timestamp}.json"

    with open(result_dir / filename, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Gespeichert: {result_dir / filename}")
    return output 