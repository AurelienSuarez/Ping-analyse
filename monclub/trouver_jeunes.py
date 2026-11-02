"""Liste les jeunes de SQY Ping : joueurs SQY inscrits sur une feuille du Championnat des Jeunes de la saison.
Écrit jeunes.json (non versionné) pour progression.py. Nécessite sqy_pools.json (étape 1 du README).
Limite : un jeune qui ne joue pas ce championnat n'est pas trouvé ; ajoutez-le dans jeunes_ajouts.json
(même format : [{"licence": "...", "nom": "..."}]), il sera repris à chaque relance."""
import datetime, json, os
from progression import get

today = datetime.date.today().isoformat()
jeunes = {}
for pool in json.load(open("sqy_pools.json"))["hydra:member"]:
    ms = get(f"/api/sport_matches?pool.id={pool['id']}&itemsPerPage=100")["hydra:member"]
    if not ms or "Jeunes" not in ms[0]["division"].get("contest", {}).get("name", ""):
        continue
    for m in ms:
        equipes = [((m.get(s) or {}).get("team") or {}).get("name", "") for s in ("homeOpponent", "awayOpponent")]
        if not any("SQY" in e.upper() for e in equipes) or (m.get("date") or "9")[:10] >= today:
            continue
        d = get(m["@id"])
        cat = d["division"]["name"].replace("D78_", "")
        for side, sheet in (("homeOpponent", "homeSheetMatches"), ("awayOpponent", "awaySheetMatches")):
            if "SQY" not in ((d.get(side) or {}).get("team") or {}).get("name", "").upper():
                continue
            for sp in d.get(sheet) or []:
                p = sp.get("player")
                if p:
                    e = jeunes.setdefault(p["identifier"], dict(licence=p["identifier"], nom=f'{p["person"]["givenName"]} {p["person"]["familyName"]}',
                                                                points=p.get("points"), categories=[]))
                    if cat not in e["categories"]:
                        e["categories"].append(cat)
# jeunes ajoutés à la main (ex. un jeune qui ne joue qu'en équipe adulte) : conservés à chaque relance
if os.path.exists("jeunes_ajouts.json"):
    for e in json.load(open("jeunes_ajouts.json")):
        jeunes.setdefault(e["licence"], dict(e, categories=e.get("categories", ["ajout manuel"])))
liste = sorted(jeunes.values(), key=lambda e: e["nom"])
json.dump(liste, open("jeunes.json", "w"), ensure_ascii=False, indent=1)
print(len(liste), "jeunes ->", "jeunes.json")
