import json
import httpx
from app.utils.api import set_api_key, build_api_header
from app.utils.prompts import build_deduplication_prompt_entity
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
                        "items": {"type": "integer"},
                        "description": "indices(1 based) of the candidate items that are considered duplicates of the query item",
                    }
                },
                "required": ["duplicates"],
                "additionalProperties": False,
            }
        }
    }
]


def send_llm_candidates(query_item, candidate_list_items, input_text):
    #api ver setzen
    api_key = set_api_key("DEEPSEEK_API_KEY")
    # header bauen
    headers = build_api_header(api_key)

    #fueg indices zu den candidate items hinzu, damit die mapping korrekt ist
    candidate_lines = []
    for i, item in enumerate(candidate_list_items, start=1):
        candidate_lines.append(f"{i}. {item['name']} ({item['type']})")
    numbered_block = "\n".join(candidate_lines)

    prompt = build_deduplication_prompt_entity(query_item, numbered_block, input_text)
    dedup_response = httpx.post(
            "https://api.deepseek.com/beta/v1/chat/completions",
            headers=headers,
            json={
                "model": "deepseek-v4-flash",
                "thinking": {"type": "disabled"},
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
    # konvertiere indizes zu (name, type)-tuples
    result_mappings = []
    for i in dedup_mappings:
        candidate_item = candidate_list_items[i - 1]  # 1-based index to 0-based
        result_mappings.append((candidate_item["name"], candidate_item["type"]))
    return result_mappings
