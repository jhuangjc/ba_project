import json


def _raise_value_error(message):
    print(message)
    raise ValueError(message)


def _raise_value_error_from(message, exc):
    print(message)
    raise ValueError(message) from exc

# Check that the API returned something we can work with.
def validate_response_content(content):
    if not isinstance(content, str):
        _raise_value_error("Die Antwort ist kein String.")
    if not content.strip():
        _raise_value_error("Die Antwort ist leer.")


# Make sure the parsed JSON is a dictionary.
def validate_response_structure(data):
    if not isinstance(data, dict):
        _raise_value_error("Die Antwort ist kein gültiges JSON-Objekt.")
    return data


# Convert the JSON string from the model into a Python object.
def _load_json_content(content):
    try:
        cleaned_content = content.strip()
        if cleaned_content.startswith("```"):
            lines = cleaned_content.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned_content = "\n".join(lines).strip()
        return json.loads(cleaned_content)
    except json.JSONDecodeError as exc:
        _raise_value_error_from("Die Antwort ist kein gültiges JSON.", exc)



#TODO: implement more specific validation functions for entities and relations

# Validate the entity response format from the model.
def validate_response_entity(content):
    #validate response content
    validate_response_content(content)
    #validate response structure
    data = _load_json_content(content)
    validate_response_structure(data)
    if "entities" not in data:
        _raise_value_error("Die Antwort enthält keine 'entities'-Schlüssel.")
    #validate entities
    all_entities = data["entities"]
    if not isinstance(all_entities, list):
        _raise_value_error("Die 'entities'-Schlüssel muss eine Liste sein.")
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
        _raise_value_error("Die Antwort enthält keine 'triples'-Schlüssel.")
    #validate triples
    all_triples = data["triples"]
    if not isinstance(all_triples, list):
        _raise_value_error("Die 'triples'-Schlüssel muss eine Liste sein.")
    for triple in all_triples:
        if not isinstance(triple, dict):
            _raise_value_error("Jedes Triple muss ein JSON-Objekt sein.")
        if set(triple.keys()) != {"subject", "predicate", "object"}:
            _raise_value_error("Jedes Triple muss 'subject', 'predicate' und 'object' enthalten.")
        for field in ["subject", "predicate", "object"]:
            if not isinstance(triple[field], str) or len(triple[field].strip()) == 0:
                _raise_value_error(f"Das Feld '{field}' muss ein String sein.")
    return data
