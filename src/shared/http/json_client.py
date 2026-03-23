
import requests

def fetch_url(base_url: str, path: str, params: dict | None = None):
    url = f"{base_url.rstrip('/')}/{path.lstrip('/')}"
    
    clean_params = {}

    if params:
        for key, value in params.items():
            if value is not None:
                clean_params[key] = value

    params = clean_params
    
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    
    return response.json()
