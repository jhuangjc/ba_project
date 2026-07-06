import json
import httpx
from app.utils.api import set_api_key, build_api_header
from app.utils.prompts import build_deduplication_prompt_relation, build_deduplication_prompt_entity
#tools für deduplication
dedup_tool = [
    {
        "type": "function",
        "function": {
            "name": "deduplicate",
            "strict": True,
            "description": "given a list of items and a query item, return a list of candidates that are considered duplicates of the query item",
            "parameters": {
                "type": "object",
                "properties": {
                    "duplicates": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of candidates that are considered duplicates of the query item",
                    }
                },
                "required": ["duplicates"],
                "additionalProperties": False,
            }
        }
    }
]


def send_llm_candidates(query_item, candidate_list_items,Is_relation):
    #api ver setzen
    api_key = set_api_key("DEEPSEEK_API_KEY")
    # header bauen
    headers = build_api_header(api_key)
    #mesage bauen
    if Is_relation:
        prompt = build_deduplication_prompt_relation(query_item, candidate_list_items)
    else:
        prompt = build_deduplication_prompt_entity(query_item, candidate_list_items)
    dedup_response = httpx.post(
            "https://api.deepseek.com/beta/v1/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "tools": dedup_tool,
                "tool_choice": "required",
            },
        timeout=30.0,
)
    # extrahiere mappings aus der antwort
    dedup_response.raise_for_status()
    response_data = dedup_response.json()
    dedup_content = response_data["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"]
    dedup_mappings = json.loads(dedup_content)["duplicates"]
#fuer den entity fall, wenn der query item ein dict ist, dann muss auch der type mitgegeben werden, damit die mapping korrekt ist
    if not Is_relation:
        for i,item in enumerate(dedup_mappings):
            dedup_mappings[i] = (item, query_item["type"])

    return dedup_mappings
