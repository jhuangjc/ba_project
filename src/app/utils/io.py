import json
from pathlib import Path
# Projekt Pfad hilfsvariable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTRY_PATH = PROJECT_ROOT / "data/registry/registry.json"
RESULTS_DIR = PROJECT_ROOT / "data/results"
# Hilfsfuntion fuer das Lesen von Dateien
def read_file(path):
    with open(path, "r") as file:
        return file.read()

# ladet die inputtext mit dem pfad aus der registry
def load_input_file(exp):
    input_path = PROJECT_ROOT / exp["input_path"]
    return read_file(input_path)

# ladet die Registry 
def load_registry():
    return json.loads(read_file(REGISTRY_PATH))

#hilfsfunktion um die goldstandard triples mit dem pfad aus der registry zu laden
def load_goldstandard(exp):
    gold_path = PROJECT_ROOT / exp["gold_path"]
    return json.loads(read_file(gold_path))