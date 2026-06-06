import pytest
from app.utils.api import set_api_key,build_api_header


def test_set_api_key(monkeypatch):
    #mock key
    api_key = "test_api_key"
    #setzt die Umgebungsvariable für den Test
    monkeypatch.setenv("API_KEY", api_key)   

    assert set_api_key("API_KEY") == api_key

def test_build_api_header():
    #mock key
    api_key = "test_api_key"
    #erwarteter Header
    expected_header = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    assert build_api_header(api_key) == expected_header