import pytest

from app.utils.api_utils import validate_response_entity, validate_response_relation
from app.utils.prompt_utils import build_entity_extraction_prompt, build_relation_extraction_prompt


# These tests check that valid JSON is accepted.
def test_validate_response_entity_accepts_valid_json():
    content = '{"entities": ["Alice", "Bob"]}'

    result = validate_response_entity(content)

    assert result["entities"] == ["Alice", "Bob"]


# Missing the "entities" key should raise an error.
def test_validate_response_entity_rejects_missing_entities():
    content = '{"wrong": []}'

    with pytest.raises(ValueError, match="entities"):
        validate_response_entity(content)


# This checks one valid triple example.
def test_validate_response_relation_accepts_valid_json():
    content = '{"triples": [{"subject": "Alice", "predicate": "knows", "object": "Bob"}]}'

    result = validate_response_relation(content)

    assert result["triples"][0]["subject"] == "Alice"


# An empty subject should not be accepted.
def test_validate_response_relation_rejects_invalid_triples():
    content = '{"triples": [{"subject": "", "predicate": "knows", "object": "Bob"}]}'

    with pytest.raises(ValueError, match="subject"):
        validate_response_relation(content)


# The prompt should contain the input text.
def test_build_entity_extraction_prompt_includes_text():
    prompt = build_entity_extraction_prompt("Alice met Bob.")

    assert "Alice met Bob." in prompt
    assert "entities" in prompt


# The relation prompt should include both the text and the entity list.
def test_build_relation_extraction_prompt_includes_entities_and_text():
    prompt = build_relation_extraction_prompt("Alice met Bob.", ["Alice", "Bob"])

    assert "Alice met Bob." in prompt
    assert "Alice" in prompt
    assert "triples" in prompt

#todo: test that check the pram types of the prompt building functions, e.g. that passing non-string to build_entity_extraction_prompt raises an error, etc.