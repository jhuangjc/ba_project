import pytest
from app.pipeline.refiner import (
    data_to_lowercase,
    convert_dicts_to_tuples,
    convert_tuples_to_dicts,
    rm_exact_duplicates,
    dedup_list,
    gen_reverse_mapping,
    apply_mapping,
    refine_data,
)
#beispiel testdaten
@pytest.fixture
def sample_data():
    return {
        "entities": [
            {"name": "Alice", "type": "PER"},
            {"name": "Bob", "type": "PER"},
            {"name": "alice", "type": "PER"},
            {"name": "Robert", "type": "PER"},
            {"name": "bob", "type": "PER"},
            {"name": "Robert Smith", "type": "PER"},
        ],
        "triples": [
            {"subject": {"name": "Alice", "type": "PER"}, "predicate": "knows", "object": {"name": "Bob", "type": "PER"}},
            {"subject": {"name": "Alice", "type": "PER"}, "predicate": "knows", "object": {"name": "Bob", "type": "PER"}},
            {"subject": {"name": "Bob", "type": "PER"}, "predicate": "knows", "object": {"name": "Alice", "type": "PER"}},
            {"subject": {"name": "Robert", "type": "PER"}, "predicate": "knows", "object": {"name": "Alice", "type": "PER"}},
            {"subject": {"name": "bob", "type": "PER"}, "predicate": "knows", "object": {"name": "Alice", "type": "PER"}},
            {"subject": {"name": "Robert Smith", "type": "PER"}, "predicate": "knows", "object": {"name": "Alice", "type": "PER"}},
        ],
        "relations": ["knows", "knows"],
    }
##############testblock data_to_lowercase########################
def test_data_to_lowercase(sample_data):
    result = data_to_lowercase(sample_data)
    assert all( (entity["name"].islower() for entity in result["entities"]) )
    assert all( ( triple["subject"]["name"].islower() and triple["predicate"].islower() and triple["object"]["name"].islower() for triple in result["triples"] ))

#################testblock dedup_list#########################
def test_dedup_list():
    input_list = ["Alice", "Bob", "Alice", "Charlie", "Bob"]
    expected_output = ["Alice", "Bob", "Charlie"]
    assert dedup_list(input_list) == expected_output
def test_dedup_list_no_duplicates():
    input_list = ["Alice", "Bob", "Charlie"]
    expected_output = ["Alice", "Bob", "Charlie"]
    assert dedup_list(input_list) == expected_output
def test_dedup_list_empty_list():
    input_list = []
    expected_output = []
    assert dedup_list(input_list) == expected_output
   ####################testblock convert_dicts_to_tuples und convert_tuples_to_dicts#########################
#testet ob die konvertierung von dicts zu tuples und zurück die original daten ergibt
def test_convert_dicts_to_tuples(sample_data): 
    dict_triples = sample_data["triples"]
    expected_tuples = [
        (("Alice", "PER"), "knows", ("Bob", "PER")),
        (("Alice", "PER"), "knows", ("Bob", "PER")),
        (("Bob", "PER"), "knows", ("Alice", "PER")),
        (("Robert", "PER"), "knows", ("Alice", "PER")),
        (("bob", "PER"), "knows", ("Alice", "PER")),
        (("Robert Smith", "PER"), "knows", ("Alice", "PER")),
    ]
    assert convert_dicts_to_tuples(dict_triples) == expected_tuples

def test_convert_tuples_to_dicts(sample_data):
    tuples_triples = [
        (("Alice", "PER"), "knows", ("Bob", "PER")),
        (("Alice", "PER"), "knows", ("Bob", "PER")),
        (("Bob", "PER"), "knows", ("Alice", "PER")),
        (("Robert", "PER"), "knows", ("Alice", "PER")),
        (("bob", "PER"), "knows", ("Alice", "PER")),
        (("Robert Smith", "PER"), "knows", ("Alice", "PER")),
    ]
    expected_dicts = sample_data["triples"]
    assert convert_tuples_to_dicts(tuples_triples) == expected_dicts

def test_round_triple_conversion(sample_data):

    dict_triples = sample_data["triples"]
    tuples_triples = convert_dicts_to_tuples(dict_triples)
    result_dict_triples = convert_tuples_to_dicts(tuples_triples)
    assert dict_triples == result_dict_triples
#####################testblock rm_exact_duplicates#########################
def test_rm_exact_duplicates(sample_data):
    result = rm_exact_duplicates(sample_data)
    assert len(result["entities"]) == 6
    assert len(result["triples"]) == 5
    assert len(result["relations"]) == 1
######################testblack gen_reverse_mapping#########################
# beispiel mapping
@pytest.fixture
def sample_mapping():
    return {
        "Alice": ["alice"],
        "Bob": ["bob"],
        "Robert": ["robert"],
    }
#prüft ob die reverse mapping invertiert das original ergebnis ergibt
def test_gen_reverse_mapping(sample_mapping):
    mapping = sample_mapping
    reverse_mapping = gen_reverse_mapping(mapping)
    for key, value in mapping.items():
        for v in value:
            assert reverse_mapping[v] == key
######################testblock apply_mapping#########################
@pytest.fixture
def test_mapping():
    return {
        ("Alice", "PER"): [("alice", "PER")],
        ("Bob", "PER"): [("bob", "PER"), ("Robert Smith", "PER"), ("Robert", "PER"), ("robert", "PER")],
    }
def test_apply_mapping(sample_data, test_mapping):
    entity_mapping = test_mapping
    result = apply_mapping(sample_data, entity_mapping)
    #prüft ob die duplikate in entities ersetzt wurden
    for entity in result["entities"]:
        assert entity["name"] not in ["alice", "bob", "robert", "robert smith"]

    #prüft ob die duplikate in triples ersetzt wurden
    for triple in result["triples"]:
        assert triple["subject"]["name"] not in ["alice", "bob", "robert", "robert smith"]
        assert triple["object"]["name"] not in ["alice", "bob", "robert", "robert smith"]

########################testblock refine_data#########################
def test_refine_data_errors(sample_data):
    with pytest.raises(ValueError):
        refine_data("not a dict", "Test input text for context")

    with pytest.raises(ValueError):
        refine_data(["list", "of", "things"], "Test input text for context")

    with pytest.raises(ValueError):
        refine_data(None, "Test input text for context")