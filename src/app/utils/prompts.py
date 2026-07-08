import json

# ladet den prompt für die entity extraction
def build_entity_extraction_prompt(text):
    return (
        "Extract the entities from the following text and return only valid JSON with an 'entities' object list. Each entity object must contain exactly these keys: 'name' and 'type'. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Text:\n{text}"
    )

# ladet den prompt für die relation extraction, der die entity list als input bekommt
def build_relation_extraction_prompt(text, entities, gold_relations):
    entity_block = json.dumps(entities, ensure_ascii=False, indent=2)
    gold_block = ", ".join(gold_relations)
    return (
        "Extract the relations between the given entities and return only valid JSON with a 'triples' list. "
        "Each triple must have 'subject' (object with 'name' and 'type'), "
        "'predicate' (string), and 'object' (object with 'name' and 'type'). "
        "Only use these relation types: " + gold_block + ".\n\n"
        "Return a list of such objects, not arrays or tuples. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Entities:\n{entity_block}\n\n"
        f"Text:\n{text}" 
    )
# ladet den prompt für die deduplication, der die query item und die candidate items als input bekommt
def build_deduplication_prompt_relation(query_item, candidate_items):
    candidate_block = json.dumps(candidate_items, ensure_ascii=False, indent=2)
    return (
        "Given a query item (a relation predicate) and a list of candidate relation predicates, "
        "identify which candidates are duplicates of the query item. "
        "Only merge predicates that have identical meaning (e.g., 'screenwriter' and 'written_by' "
        "refer to the same relation). "
        "Be conservative: keep predicates separate unless they are clearly synonyms. "
        "For example, 'broadcast_on' and 'written_by' are NOT duplicates.\n\n"
        "Return only valid JSON with a 'duplicates' list containing the duplicate items. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item:\n{query_item}\n\n"
        f"Candidate Items:\n{candidate_block}"
    )
#promt fuer die entity refinement
def build_deduplication_prompt_entity(query_item, candidate_items):
    candidate_block = json.dumps(candidate_items, ensure_ascii=False, indent=2)
    return (
        "Given a query item and a list of candidate items, identify which candidates are duplicates of the query item. "
        "Each item is a dictionary with 'name' and 'type' (PER, ORG, LOC, MISC, TIME, NUM). "
        "Only consider candidates as duplicates if they refer to the same real-world entity. "
        "Items with the same name but different types are NOT duplicates "
        "(e.g., 'Blackadder' as PER and 'Blackadder' as MISC are distinct).\n\n"
        "Return only valid JSON with a 'duplicates' list containing the duplicate items. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item:\n{query_item}\n\n"
        f"Candidate Items:\n{candidate_block}"
    )