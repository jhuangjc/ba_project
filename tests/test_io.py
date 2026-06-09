# zu testen load_input_file
import pytest
from app.utils.io import load_input_file, load_registry

#testet ob der inputtext korrekt mithilf des eines exp objextes geladen wird
def test_load_input_file():
    
    #beispiel experiment
    registry=load_registry()
    result = load_input_file(registry["experiments"][0])
    #schaut die antwort nen string ist und nicht leer ist
    assert isinstance(result, str)
    assert result != ""