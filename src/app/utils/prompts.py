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
#promt fuer die entity refinement
def build_deduplication_prompt_entity(query_item, candidate_items, input_text):
    return (
        "Given a query item and a numbered list of candidate items, determine which candidates "
        "are duplicates of the query item. "
        "Duplicates are items that unambiguously refer to the EXACT SAME real-world entity.\n\n"
        "CRITICAL — You MUST use the source text to verify coreference:\n"
        "- Check whether the query item and each candidate appear in the same context, "
        "refer to the same event/person/place, or are used interchangeably.\n"
        "- A partial name match alone is NOT sufficient evidence. "
        "The source text must confirm they are the same entity.\n"
        "- If the source text does not provide clear evidence, do NOT merge.\n\n"
        "RULES:\n"
        "1. Different types (PER, ORG, LOC, MISC, TIME, NUM) ALWAYS mean different entities.\n"
        "2. Same name with different types are NOT duplicates "
        "(e.g., 'Blackadder' as PER and 'Blackadder' as MISC are distinct).\n"
        "3. Do NOT merge entities that merely share a word "
        "(e.g., 'United Kingdom' and 'United States' are NOT duplicates).\n"
        "4. When in doubt, keep entities separate.\n\n"
        "Return only valid JSON with a 'duplicates' list containing the 1-based indices of matching candidates. "
        "Return an empty list if there are none. "
        "Do not include markdown, code fences, or any explanation.\n\n"
        f"Query Item: {query_item['name']} ({query_item['type']})\n\n"
        f"Candidate Items:\n{candidate_items}\n\n"
        f"Source Text:\n{input_text}"
    )