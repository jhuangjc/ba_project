import json

# ladet den prompt für die entity extraction
def build_entity_extraction_prompt(text):
    return (
        "Extract key entities from the source text. Extracted entities are subjects or objects. "
        "This is for an extraction task, please be thorough and accurate to the reference text. "
        "Return only valid JSON with an 'entities' object list. Each entity object must contain exactly these keys: "
        "'name' (string) and 'type' (one of: PER, ORG, LOC, MISC, TIME, NUM). "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Text:\n{text}"
    )

# ladet den prompt für die relation extraction, der die entity list als input bekommt
def build_relation_extraction_prompt(text, entities, gold_relations):
    entity_block = json.dumps(entities, ensure_ascii=False, indent=2)
    gold_block = ", ".join(gold_relations)
    return (
        "Extract subject-predicate-object triples from the source text. "
        "Subject and object must be from the entities list. "
        "Entities provided were previously extracted from the same source text. "
        "This is for an extraction task, please be thorough, accurate, and faithful to the reference text. "
        "Each triple must have 'subject' (object with 'name' and 'type'), "
        "'predicate' (string), and 'object' (object with 'name' and 'type'). "
        "Only use these relation types: " + gold_block + ".\n\n"
        "Return a list of such objects, not arrays or tuples. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Entities:\n{entity_block}\n\n"
        f"Text:\n{text}" 
    )
# ladet den prompt für die deduplication, der die query item und die candidate items als input bekommt
def build_deduplication_prompt_relation(query_item, candidate_items, input_text):
    return (
        "Given a query item (a relation predicate) and a numbered list of candidate relation predicates, "
        "find which candidates are duplicates of the query item. "
        "Duplicates are those that are the same in meaning, such as with variation in tense, "
        "plural form, stem form, case, abbreviation, or shorthand "
        "(e.g., 'screenwriter' and 'written_by' refer to the same relation). "
        "Be conservative: keep predicates separate unless they are clearly synonyms. "
        "For example, 'broadcast_on' and 'written_by' are NOT duplicates.\n\n"
        "Return only valid JSON with a 'duplicates' list containing the 1-based indices of matching candidates. "
        "Return an empty list if there are none. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item:\n{query_item}\n\n"
        f"Candidate Items:\n{candidate_items}\n\n"
        f"Input Text:\n{input_text}"
    )
#promt fuer die entity refinement
def build_deduplication_prompt_entity(query_item, candidate_items, input_text):
    return (
        "Given a query item and a numbered list of candidate items, find which candidates "
        "are duplicates of the query item. "
        "Duplicates are those that refer to the same real-world entity, such as with variation in "
        "name length (e.g., 'Haig' vs 'Field Marshal Haig'), abbreviations, or alternate spellings. "
        "Each item shows its number, name, and type (PER, ORG, LOC, MISC, TIME, NUM). "
        "Items with the same name but different types are NOT duplicates "
        "(e.g., 'Blackadder' as PER and 'Blackadder' as MISC are distinct).\n\n"
        "Return only valid JSON with a 'duplicates' list containing the 1-based indices of matching candidates. "
        "Return an empty list if there are none. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item:\n{query_item}\n\n"
        f"Candidate Items:\n{candidate_items}\n\n"
        f"Input Text:\n{input_text}"
    )