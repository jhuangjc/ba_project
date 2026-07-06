import json
import httpx

from app.utils.prompts import build_entity_extraction_prompt, build_relation_extraction_prompt
from app.utils.api import set_api_key
from app.utils.api import build_api_header
################################################util functions######################
def extract_relations(triples):
    relations = []
    for triple in triples:
        relations.append(triple["predicate"])
    return relations
#tools for entety extraction
entity_ext_tool = [
    {
        "type": "function",
        "function": {
            "name": "extract_entities",
            "strict": True,
            "description": "Extract the entities form the text",
            "parameters": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        #jede entity soll aus name und type bestehen
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {
                                        "type": "string"
                                    },
                                    "type": {
                                        "type": "string",
                                        "enum": ["PER", "ORG", "LOC", "MISC", "TIME", "NUM"]
                                    }
                                },
                                "required": ["name", "type"],
                                "additionalProperties": False
                            }
                    }
                },
                "required": ["entities"],
                "additionalProperties": False,
            }
        }
    }
]

#tool for relation extraction
relation_ext_tool = [
    {
        "type": "function",
        "function": {
            "name": "extract_relations",
            "strict": True,
            "description": "Extract the relations form the text and the entity list",
            "parameters": {
                "type": "object",
                "properties": {
                    #die antwort soll aus Tripeln bestehen
                    "triples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            #jedes Triple soll aus subject, predicate und objekt bestehen
                            "properties": {
                                "subject": {
                                    "type": "string",
                                    "description": "The subject of the triple"
                                },
                                "predicate": {
                                    "type": "string",
                                    "description": "The predicate of the triple"
                                },
                                "object": {
                                    "type": "string",
                                    "description": "The object of the triple"
                                },
                            },
                            "required": ["subject", "predicate", "object"],
                            "additionalProperties": False,
                        },
                        "description": "List of triples extracted from the text. Each triple is an object with subject, predicate and object.",
                    }
                },
                "required": ["triples"],
                "additionalProperties": False,
            }
        }
    }
]

# diese funtion gitb imputtext rein und gibt die extrahierten entities und triples zurueck
def gen_triples(input_text):
    # setzt den API key aus der Umgebungvariable
    api_key = set_api_key("DEEPSEEK_API_KEY")

    # bau den Header für die API Anfragen
    headers = build_api_header(api_key)

    # Entity Extraction
    entity_prompt = build_entity_extraction_prompt(input_text)
    entity_response = httpx.post(
        "https://api.deepseek.com/beta/v1/chat/completions",
        headers=headers,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": entity_prompt}
            ],
            "tools": entity_ext_tool,
            "tool_choice": "required",
 
        },
        timeout=30.0,
    )
    # Check ob die Anfrage erfolgreich war und extrahiere die Antwort
    entity_response.raise_for_status()
    entity_data = entity_response.json()
    entity_content = entity_data["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
    entities_object = json.loads(entity_content)["entities"]

    #das print statement ist nur zum debuggen
    print(entity_content)

    # Bau den extraction promt mit dem imputtext und den entities.
    relation_prompt = build_relation_extraction_prompt(input_text, entities_object)
    relation_response = httpx.post(
        "https://api.deepseek.com/beta/v1/chat/completions",
        headers=headers,
        json={
            "model": "deepseek-chat",
            "messages": [
                {"role": "user", "content": relation_prompt}
            ],
            "tools": relation_ext_tool,
            "tool_choice": "required",
        },
        timeout=30.0,
    )
    # Check ob die Anfrage erfolgreich war und extrahiere die Antwort
    relation_response.raise_for_status()
    relation_data = relation_response.json()
    relation_content = relation_data["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
    triples= json.loads(relation_content)["triples"]
    #generate the relations list from the triples
    relations = extract_relations(triples)
    #das print statement ist nur zum debuggen
    print(relation_content)
    return {
        "entities": entities_object,
        "triples": triples,
        "relations": relations,
    }
