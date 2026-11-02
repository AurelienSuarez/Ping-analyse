"""Liste les jeunes de SQY Ping (catégories avant seniors : jusqu'aux juniors, moins de 19 ans).

L'API ne donne pas l'âge des licenciés. On part de tous les joueurs SQY présents sur une feuille de match
de la saison (toutes équipes), et on classe chacun d'après les compétitions réservées à un âge :
  - jeune  : Critérium fédéral « Moins de N ans » / « - N ans » (N <= 19), Top Jeunes, Championnat des Jeunes ;
  - senior : Critérium fédéral « Plus de 19 ans » ou « Elite » ;
  - sinon  : âge inconnu -> jeunes_a_verifier.json.
Ajouts à la main : jeunes_ajouts.json, [{"licence": "...", "nom": "..."}], repris à chaque relance.
Écrit jeunes.json (non versionné) pour progression.py. Nécessite sqy_pools.json (étape 1 du README).
"""
import datetime, json, os, re
from progression import get, parties

today = datetime.date.today().isoformat()


def joueurs_sqy():
    joueurs = {}
    for pool in json.load(open("sqy_pools.json"))["hydra:member"]:
        for m in get(f"/api/sport_matches?pool.id={pool['id']}&itemsPerPage=100")["hydra:member"]:
            equipes = [((m.get(s) or {}).get("team") or {}).get("name", "") for s in ("homeOpponent", "awayOpponent")]
            if not any("SQY" in e.upper() for e in equipes) or (m.get("date") or "9")[:10] >= today:
                continue
            d = get(m["@id"])
            for side, sheet in (("homeOpponent", "homeSheetMatches"), ("awayOpponent", "awaySheetMatches")):
                if "SQY" not in ((d.get(side) or {}).get("team") or {}).get("name", "").upper():
                    continue
                for sp in d.get(sheet) or []:
                    p = sp.get("player")
                    if p:
                        joueurs[p["identifier"]] = f'{p["person"]["givenName"]} {p["person"]["familyName"]}'
    return joueurs


def indice_age(contest, division):
    """('jeune' | 'senior' | None, libellé)"""
    if "Jeunes" in contest:
        return "jeune", (division or contest).replace("D78_", "")
    if "Crit" in contest:
        m = re.search(r"(?:Moins de|-)\s*(\d+)\s*ans", division or "")
        if m:
            return ("jeune" if int(m.group(1)) <= 19 else "senior"), f"Critérium -{m.group(1)} ans"
        if re.search(r"Plus de 19|Elite", division or ""):
            return "senior", "Critérium " + division
    return None, None


jeunes, a_verifier = {}, []
for lic, nom in sorted(joueurs_sqy().items(), key=lambda x: x[1]):
    indices, points = set(), None
    for g in parties(lic):
        division = ((g.get("sportMatch") or {}).get("division") or {}).get("name", "")
        k, libelle = indice_age(g["contest"]["name"], division)
        if k:
            indices.add((k, libelle))
        for side in ("homePlayer", "awayPlayer"):
            if (g.get(side) or {}).get("identifier") == lic:
                points = g[side].get("points")
    e = dict(licence=lic, nom=nom, points=points, categories=sorted(l for _, l in indices))
    types = {k for k, _ in indices}
    if "jeune" in types:
        jeunes[lic] = e
    elif "senior" not in types:
        a_verifier.append(e)

if os.path.exists("jeunes_ajouts.json"):
    for e in json.load(open("jeunes_ajouts.json")):
        jeunes.setdefault(e["licence"], dict(e, categories=e.get("categories", ["ajout manuel"])))
        a_verifier = [x for x in a_verifier if x["licence"] != e["licence"]]

liste = sorted(jeunes.values(), key=lambda e: e["nom"])
json.dump(liste, open("jeunes.json", "w"), ensure_ascii=False, indent=1)
json.dump(a_verifier, open("jeunes_a_verifier.json", "w"), ensure_ascii=False, indent=1)
print(len(liste), "jeunes -> jeunes.json ;", len(a_verifier), "joueurs sans indice d'âge -> jeunes_a_verifier.json")
