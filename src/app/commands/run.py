from app.utils.io import load_input_file, load_registry, load_goldstandard
from app.pipeline.triple_generator import gen_triples
from app.pipeline.refiner import refine_data
from app.pipeline.metrics import measure_data, generate_combined_metrics

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
    triples_result = gen_triples(input_text)
    # messungen vor dem Refinement
    metrics_before = measure_data(triples_result, goldstandard, before_refinement=True)

    # verfeinere die Daten
    refined_result, entity_mapping, relation_mapping = refine_data(triples_result)

    # messingen nach dem Refinement
    metrics_after = measure_data(refined_result, goldstandard, before_refinement=False)

    #generiere die Metriken
    generate_combined_metrics(metrics_before, metrics_after, goldstandard, refined_result)
    return {
        "experiment_id": ex_id,
        "input_type": exp["input_type"],
        "source_group": exp["source_group"],
        "gold_id": exp["gold_id"],
        "entities": refined_result["entities"],
        "triples": refined_result["triples"],
        "relations": refined_result["relations"],
        "entity_mapping": entity_mapping,
        "relation_mapping": relation_mapping,
    }