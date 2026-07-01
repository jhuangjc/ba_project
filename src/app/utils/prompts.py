import json

# ladet den prompt für die entity extraction
def build_entity_extraction_prompt(text):
    return (
        "Extract the entities from the following text and return only valid JSON with an 'entities' object list. Each entity object must contain exactly these keys: 'name' and 'type'. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Text:\n{text}"
    )

# ladet den prompt für die relation extraction, der die entity list als input bekommt
def build_relation_extraction_prompt(text, entities):
    entity_block = json.dumps(entities, ensure_ascii=False, indent=2)
    return (
        "Extract the relations between the given Objects and return only valid JSON with a 'triples' list.Each object contains the entity name and the entity type. "
        "Return a list of such objects, not arrays or tuples. Do not include markdown, code fences, or any explanation.\n\n"
        f"Entities:\n{entity_block}\n\n"
        f"Text:\n{text}"
    )
# ladet den prompt für die deduplication, der die query item und die candidate items als input bekommt
def build_deduplication_prompt(query_item, candidate_items):
    candidate_block = json.dumps(candidate_items, ensure_ascii=False, indent=2)
    return (
        "Given a query item and a list of candidate items, identify which candidates are duplicates of the query item. "
        "Return only valid JSON with a 'duplicates' list containing the duplicate items. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item:\n{query_item}\n\n"
        f"Candidate Items:\n{candidate_block}"
    )
