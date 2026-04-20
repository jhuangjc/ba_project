import json

# Check that the API returned something we can work with.
def validate_response_content(content):
    if not content:
        raise ValueError("Die Antwort ist leer.")
    if not isinstance(content, str):
        raise ValueError("Die Antwort ist kein String.")


# Make sure the parsed JSON is a dictionary.
def validate_response_structure(data):
    if not isinstance(data, dict):
        raise ValueError("Die Antwort ist kein gültiges JSON-Objekt.")
    return data


# Convert the JSON string from the model into a Python object.
def _load_json_content(content):
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Die Antwort ist kein gültiges JSON.") from exc



#TODO: implement more specific validation functions for entities and relations

# Validate the entity response format from the model.
def validate_response_entity(content):
    #validate response content
    validate_response_content(content)
    #validate response structure
    data = _load_json_content(content)
    validate_response_structure(data)
    if "entities" not in data:
        raise ValueError("Die Antwort enthält keine 'entities'-Schlüssel.")
    #validate entities
    all_entities = data["entities"]
    if not isinstance(all_entities, list):
        raise ValueError("Die 'entities'-Schlüssel muss eine Liste sein.")
    #TODO: validate entity structure
    return data





# Validate the relation response format from the model.
def validate_response_relation(content):
    #validate response content
    validate_response_content(content)
    #validate response structure
    data = _load_json_content(content)
    validate_response_structure(data) 
    if "triples" not in data:
        raise ValueError("Die Antwort enthält keine 'triples'-Schlüssel.")
    #validate triples
    all_triples = data["triples"]
    if not isinstance(all_triples, list):
        raise ValueError("Die 'triples'-Schlüssel muss eine Liste sein.")
    for triple in all_triples:
        if not isinstance(triple, dict):
            raise ValueError("Jedes Triple muss ein JSON-Objekt sein.")
        if set(triple.keys()) != {"subject", "predicate", "object"}:
            raise ValueError("Jedes Triple muss 'subject', 'predicate' und 'object' enthalten.")
        for field in ["subject", "predicate", "object"]:
            if not isinstance(triple[field], str) or len(triple[field].strip()) == 0:
                raise ValueError(f"Das Feld '{field}' muss ein String sein.")
    return data
