
import json

# Build the prompt for extracting entities from raw text.
def build_entity_extraction_prompt(text):
    return (
        "Extract the entities from the following text and return JSON with an 'entities' list.\n\n"
        f"Text:\n{text}"
    )


# Build the prompt for extracting relations from the text and entities.
def build_relation_extraction_prompt(text, entities):
    entity_block = json.dumps(entities, ensure_ascii=False, indent=2)
    return (
        "Extract the relations between the given entities and return JSON with a 'triples' list.\n\n"
        f"Entities:\n{entity_block}\n\n"
        f"Text:\n{text}"
    )
