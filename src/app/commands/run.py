from app.utils.io import load_input_file, load_registry
from app.pipeline.triple_generator import gen_triples
from app.pipeline.refiner import refine_data

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

    # generiere die Tripel
    triples_result = gen_triples(input_text)
    # metriken abnehemen

    # verfeinere die Daten
    refined_result = refine_data(triples_result)
    #sende die verfeinerten Date an die LLM

    #wende die mappings an

    # metriken abnehemen
     
    return {
        "experiment_id": ex_id,
        "input_type": exp["input_type"],
        "source_group": exp["source_group"],
        "gold_id": exp["gold_id"],
        "entities": triples_result["entities"],
        "triples": triples_result["triples"],
    }