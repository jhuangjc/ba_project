import json

# ladet den prompt für die entity extraction
def build_entity_extraction_prompt(text):
    return (
        "Extract the entities from the following text and return only valid JSON with an 'entities' list. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Text:\n{text}"
    )

# ladet den prompt für die relation extraction, der die entity list als input bekommt
def build_relation_extraction_prompt(text, entities):
    entity_block = json.dumps(entities, ensure_ascii=False, indent=2)
    return (
        "Extract the relations between the given entities and return only valid JSON with a 'triples' list. "
        "Each triple must be a JSON object with exactly these keys: 'subject', 'predicate', and 'object'. "
        "Return a list of such objects, not arrays or tuples. Do not include markdown, code fences, or any explanation.\n\n"
        f"Entities:\n{entity_block}\n\n"
        f"Text:\n{text}"
    )
