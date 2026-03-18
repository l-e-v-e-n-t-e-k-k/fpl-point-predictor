import json
import urllib.request as urllib_request
import urllib.error as urllib_error


def download_json(url: str) -> dict:
    """
    JSON letoltese az API-bol.
    """

    req = urllib_request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
        method="GET",
    )

    try:
        with urllib_request.urlopen(req, timeout=30) as resp:
            body = resp.read()
    except urllib_error.HTTPError:
        raise
    except urllib_error.URLError:
        raise

    data = json.loads(body.decode("utf-8"))
    return data
