import os
from pathlib import Path

import httpx

from app.utils.api_utils import validate_response_entity, validate_response_relation
from app.utils.file_utils import read_file
from app.utils.prompt_utils import build_entity_extraction_prompt, build_relation_extraction_prompt


def gen_triples(args):
    # Read the API key from the environment.
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        raise ValueError("DEEPSEEK_API_KEY ist nicht gesetzt. Bitte setzen Sie die Umgebungsvariable.")

    # Check that the input file exists before reading it.
    file_path = Path(args.file)
    if not file_path.exists():
        raise ValueError(f"Datei nicht gefunden: {args.file}")
    if not file_path.is_file():
        raise ValueError(f"Keine gültige Datei: {args.file}")

    # Load the file content that will be sent to the model.
    text = read_file(file_path)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    # First ask the model to extract entities.
    entity_prompt = build_entity_extraction_prompt(text)
    entity_response = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": entity_prompt}
            ],
        },
        timeout=30.0,
    )
    entity_response.raise_for_status()
    entity_data = entity_response.json()
    entity_content = entity_data["choices"][0]["message"]["content"]
    print(entity_content)
    entity_result = validate_response_entity(entity_content)
    # Extract the entity list for the next prompt.
    entities = entity_result["entities"]

    # Then ask the model to extract relations using the entity list.
    relation_prompt = build_relation_extraction_prompt(text, entities)
    relation_response = httpx.post(
        "https://api.deepseek.com/v1/chat/completions",
        headers=headers,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": relation_prompt}
            ],
        },
        timeout=30.0,
    )
    relation_response.raise_for_status()
    relation_data = relation_response.json()
    relation_content = relation_data["choices"][0]["message"]["content"]
    print(relation_content)
    relation_result = validate_response_relation(relation_content)
    return {
        "entities": entities,
        "triples": relation_result["triples"],
    }