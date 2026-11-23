"""Accès à l'API FFTT (apiv2.fftt.com) avec le compte licencié.

Identifiants lus dans les variables d'environnement FFTT_LICENCE_USER et FFTT_LICENCE_PWD.
Le jeton est renouvelé automatiquement s'il expire (réponse 401).
"""
import json, os, threading, time, urllib.error, urllib.request

BASE = "https://apiv2.fftt.com"
_token = None
_lock = threading.Lock()

def _login():
    global _token
    body = json.dumps({"username": os.environ["FFTT_LICENCE_USER"], "password": os.environ["FFTT_LICENCE_PWD"],
                       "scope": "licence"}).encode()
    r = urllib.request.Request(BASE + "/api/login_check", data=body, method="POST",
                               headers={"Content-Type": "application/json", "Accept": "application/json"})
    with urllib.request.urlopen(r, timeout=60) as resp:
        d = json.load(resp)
    if "token" not in d:
        raise RuntimeError("Connexion FFTT refusée (double authentification active ?)")
    _token = d["token"]

def get(path, pause=0.15):
    """GET JSON-LD sur l'API, avec 4 essais et reconnexion si le jeton a expiré."""
    for i in range(4):
        with _lock:
            if _token is None: _login()
            tok = _token
        r = urllib.request.Request(BASE + path, headers={"Accept": "application/ld+json", "Authorization": "Bearer " + tok})
        try:
            with urllib.request.urlopen(r, timeout=90) as resp:
                d = json.load(resp)
            time.sleep(pause)
            return d
        except urllib.error.HTTPError as e:
            if e.code == 401 and i < 3:
                with _lock:
                    if _token == tok: _login()
                continue
            if e.code >= 500 and i < 3:
                time.sleep(5 * (i + 1)); continue
            raise
        except (urllib.error.URLError, TimeoutError):
            if i == 3: raise
            time.sleep(5 * (i + 1))
