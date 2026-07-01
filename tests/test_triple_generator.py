from app.pipeline import triple_generator
import json

#fake response klasse zum testen
class FakeResponse:
    def __init__(self, json_data):
        self._json_data = json_data
#returnt die json daten, die in der klasse gespeichert sind        
    def json(self):
        return self._json_data
    def raise_for_status(self):
        pass #nicht relevent for now

#triple und entity data, die von den fake post methoden zurückgegeben werden sollen
relation_data={"triples": [
    {"subject": "Entity1", "predicate": "related_to", "object": "Entity2"}
    ]
}

entity_data={"entities": 
    [{"name": "Entity1", "type": "PER"}, {"name": "Entity2", "type": "PER"}]
}
#json strings der daten
arguments_string_entities = json.dumps(entity_data)
arguments_string_relations = json.dumps(relation_data)


#
def build_fake_response(json_data):
    return FakeResponse({
        "choices": [{
            "message":{
                "tool_calls":[{
                    "function":{
                        "arguments": json_data
                        }
                    }]
                }
            }]
        }
)


def test_triple_generator(monkeypatch):

    #setz den api key
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fake_api_key")
    #erstellt einen iterator, der die fake post methoden abwechselnd zurückgibt 
    fake_post_entities = build_fake_response(arguments_string_entities)
    fake_post_relations = build_fake_response(arguments_string_relations)
    responses = iter([fake_post_entities, fake_post_relations])
    
    # Testet die Triple Generator Funktion mit einem Fake Response
    monkeypatch.setattr("app.pipeline.triple_generator.httpx.post", lambda *args, **kwargs: next(responses))
    gen_result = triple_generator.gen_triples("Test input text")
    # schaut ob die results den erwarteten daten entsprechen
    assert gen_result["entities"] == entity_data["entities"]
    assert gen_result["triples"] == relation_data["triples"]

    # spaeter: fehlerfaelle testen, z.B. ungültige JSON, fehlende Keys, etc.