"""Accès authentifié à l'API monclub (apiv2.fftt.com).

Depuis novembre 2026, l'API refuse les requêtes anonymes (401 « JWT Token not found »).
Identifiants lus dans les variables d'environnement FFTT_LICENCE_USER et FFTT_LICENCE_PWD.
Le jeton (valable 10 min) reste en mémoire : il n'est jamais écrit sur disque ni affiché.
Il est renouvelé avant expiration, ou après un 401.
"""
import base64, json, os, threading, time, urllib.error, urllib.request

BASE = "https://apiv2.fftt.com"
_lock = threading.Lock()
_token = {"value": None, "exp": 0}


def _login():
    user, pwd = os.environ.get("FFTT_LICENCE_USER"), os.environ.get("FFTT_LICENCE_PWD")
    if not user or not pwd:
        raise SystemExit("FFTT_LICENCE_USER et FFTT_LICENCE_PWD doivent être définies.")
    body = json.dumps({"username": user, "password": pwd, "scope": "licence"}).encode()
    req = urllib.request.Request(BASE + "/api/login_check", data=body,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        tok = json.load(urllib.request.urlopen(req, timeout=60))["token"]
    except urllib.error.HTTPError as e:
        raise SystemExit(f"Connexion FFTT refusée (HTTP {e.code}) : vérifiez les identifiants.") from None
    payload = tok.split(".")[1]
    exp = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))).get("exp", time.time() + 600)
    _token.update(value=tok, exp=exp)


def _bearer(force=False):
    with _lock:
        if force or not _token["value"] or time.time() > _token["exp"] - 60:
            _login()
        return _token["value"]


def get(path, retries=3, pause=3):
    """GET authentifié sur un chemin de l'API (ex. "/api/pools?..."), renvoie le JSON-LD décodé."""
    force = False
    for i in range(retries + 1):
        req = urllib.request.Request(BASE + path, headers={"Accept": "application/ld+json",
                                                           "Authorization": "Bearer " + _bearer(force)})
        force = False
        try:
            return json.load(urllib.request.urlopen(req, timeout=90))
        except urllib.error.HTTPError as e:
            if e.code == 401 and i < retries:
                force = True  # jeton expiré ou révoqué : nouvelle connexion
                continue
            if e.code in (403, 404) or i == retries:
                raise
        except Exception:
            if i == retries:
                raise
        time.sleep(pause * (i + 1))
