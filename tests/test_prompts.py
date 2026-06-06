import pytest

from app.utils.prompts import build_entity_extraction_prompt, build_relation_extraction_prompt



# testet ob die ein prompt  mit dem test erstellt wird.
def test_build_entity_extraction_prompt_includes_text():
    prompt = build_entity_extraction_prompt("Alice met Bob.")

    assert "Alice met Bob." in prompt
    assert "entities" in prompt


# testet ob die ein prompt  mit dem test erstellt wird.
def test_build_relation_extraction_prompt_includes_entities_and_text():
    prompt = build_relation_extraction_prompt("Alice met Bob.", ["Alice", "Bob"])

    assert "Alice met Bob." in prompt
    assert "Alice" in prompt
    assert "triples" in prompt
    assert "subject" in prompt
    assert "predicate" in prompt
    assert "object" in prompt
