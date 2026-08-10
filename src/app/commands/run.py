from app.utils.io import load_input_file, load_registry, load_goldstandard,RESULTS_DIR
from app.utils.json import serialize_tuple_keys

from app.pipeline.triple_generator import gen_triples
from app.pipeline.refiner import refine_data
from app.pipeline.metrics import measure_data, categorize_error_sources

from datetime import datetime
from pathlib import Path
import json

def run(args, output_dir=None):
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
    data_before = measure_data(triples_result, goldstandard, before_refinement=True)
    # verfeinere die Daten
    refined_result, entity_mapping = refine_data(triples_result, input_text)
    
    # messungen nach dem Refinement
    data_after = measure_data(refined_result, goldstandard, before_refinement=False)

    #error sources
    error_sources = categorize_error_sources(data_before["strict"]["details"], data_after["strict"]["details"])


    output = {
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
            "metrics_before_refinement": data_before["strict"]["metrics"],
            "metrics_after_refinement": data_after["strict"]["metrics"],
            "metrics_loose_before": data_before["loose"]["metrics"],
            "metrics_loose_after": data_after["loose"]["metrics"],
            "delta_before": data_before["delta"],
            "delta_after": data_after["delta"]
        },
        "details": {
            "strict_before": data_before["strict"]["details"],
            "strict_after": data_after["strict"]["details"],
            "loose_before": data_before["loose"]["details"],
            "loose_after": data_after["loose"]["details"],
            "error_sources": error_sources
        },
        "debug": {
            "resolved_entities_strict": data_after["debug"]["resolved_entities_strict"],
            "resolved_entities_loose": data_after["debug"]["resolved_entities_loose"],
            "entity_mapping": serialize_tuple_keys(entity_mapping)
        }
    }
    #speicher die Ergebnisse in einer Datei

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"result_{ex_id}_{timestamp}.json"

    #output order bestimmen
    if output_dir is not None:
        result_dir = Path(output_dir)
    else:
        result_dir = RESULTS_DIR
    result_dir.mkdir(parents=True, exist_ok=True)
    
    with open(result_dir / filename, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Gespeichert: {result_dir / filename}")
    return output 