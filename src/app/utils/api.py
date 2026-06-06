import os

#hifsfunktion fuer das setzen von Api keys
def set_api_key(api_key_env_var):
    api_key = os.getenv(api_key_env_var)
    if not api_key:
        raise ValueError(f"Umgebungsvariable '{api_key_env_var}' ist nicht gesetzt.")
    return api_key

#hilfsfunktion um den Header für die API Anfragen zu bauen
def build_api_header(api_key):
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
