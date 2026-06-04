from pathlib import Path
# Projekt Pfad hilfsvariable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

# Hilfsfuntion fuer das Lesen von Dateien
def read_file(path):
    with open(path, "r") as file:
        return file.read()

# ladet die inputtext mit dem pfad aus der registry
def load_input_files(exp):
    input_path = PROJECT_ROOT / exp["input_path"]
    return read_file(input_path)
