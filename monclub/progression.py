"""Classement virtuel : points gagnés par les jeunes de SQY Ping sur une période, tournois compris.

Entrées (dans monclub/) :
  jeunes.json  liste des jeunes à suivre : [{"licence": "7885025", "nom": "Prénom NOM"}, ...]
               (numéro de licence FFTT ; l'API ne donne pas l'âge des autres licenciés)
  bareme.json  grille de l'article IV.205.1 des règlements généraux FFTT, à recopier du texte officiel :
               {"source": "...", "lignes": [{"ecart_max": 24, "victoire_normale": .., "defaite_normale": ..,
                 "victoire_anormale": .., "defaite_anormale": ..}, ...]}   (dernière ligne : "ecart_max": null)
               valeurs positives ; une défaite est retirée.

Usage :
  python3 progression.py --du 2026-10-01 --au 2026-11-30            # affiche le podium (rien n'est envoyé)
  python3 progression.py --du 2026-10-01 --au 2026-11-30 --discord  # envoie aussi le podium sur Discord
                                                                     # (webhook dans DISCORD_WEBHOOK_URL)

Règles appliquées :
  - toutes les parties de simple de la saison en cours (championnat par équipes, tournois, critérium...) ;
  - les doubles et les parties sans score (forfaits, non disputées) sont ignorés ;
  - gain ou perte = valeur du barème selon l'écart de points, multipliée par le coefficient de la compétition
    (lu dans l'API, ex. 0,75 pour un tournoi) ;
  - victoire « normale » = le joueur le mieux classé gagne.
Limite : l'API ne fournit pas les points mensuels de référence, seulement les points actuels. Par défaut on estime
les points de début de période du jeune (actuels - gains, calcul itératif) ; --points-actuels donne le calcul brut.
Les points des adversaires restent leurs points actuels. Le résultat est une estimation.
"""
import argparse, json, os, sys, time, urllib.request
import fftt_api

CACHE = "cache"


def charger(fichier, exemple):
    if not os.path.exists(fichier):
        sys.exit(f"{fichier} manquant. Format attendu : {exemple}")
    return json.load(open(fichier))


def get(path):
    f = os.path.join(CACHE, path.replace("/", "_").replace("?", "_")[:200] + ".json")
    if os.path.exists(f):
        return json.load(open(f))
    d = fftt_api.get(path); time.sleep(0.2)
    os.makedirs(CACHE, exist_ok=True); json.dump(d, open(f, "w"))
    return d


def parties(licence):
    """Parties de la saison en cours d'un joueur (numéro de licence), toutes pages."""
    out, page = [], 1
    while True:
        d = get(f"/api/games?players.licence.identifier={licence}&contest.season.current=true&itemsPerPage=100&page={page}")
        out += d["hydra:member"]
        if len(out) >= d.get("hydra:totalItems", 0) or not d["hydra:member"]:
            return out
        page += 1


_coef = {}
def coefficient(contest):
    if contest["@id"] not in _coef:
        c = get(contest["@id"]).get("coefficient")
        if c is None:
            sys.exit(f"Coefficient absent pour la compétition « {contest.get('name')} » ({contest['@id']}).")
        _coef[contest["@id"]] = float(c)
    return _coef[contest["@id"]]


def bareme_points(bareme, ecart, mieux_classe, victoire):
    for l in bareme["lignes"]:
        if l["ecart_max"] is None or ecart <= l["ecart_max"]:
            if victoire:
                return l["victoire_normale"] if mieux_classe else l["victoire_anormale"]
            return -(l["defaite_anormale"] if mieux_classe else l["defaite_normale"])
    sys.exit("bareme.json : la dernière ligne doit avoir \"ecart_max\": null.")


def bilan(jeune, bareme, du, au, corriger=True):
    total, detail = 0.0, []
    for g in parties(jeune["licence"]):
        jour = (g.get("date") or "")[:10]
        if not (du <= jour <= au) or g.get("doubleOpposition") or g.get("notCounted"):
            continue
        if g.get("homeTeammatePlayer") or g.get("awayTeammatePlayer") or not g.get("setsData") or g.get("winner") not in ("home", "away"):
            continue
        h, a = g.get("homePlayer") or {}, g.get("awayPlayer") or {}
        cote = "home" if h.get("identifier") == jeune["licence"] else "away" if a.get("identifier") == jeune["licence"] else None
        if not cote:
            continue
        moi, adv = (h, a) if cote == "home" else (a, h)
        pm, pa = moi.get("points"), adv.get("points")
        if pm is None or pa is None:
            continue
        coef = coefficient(g["contest"])
        pts = bareme_points(bareme, abs(pm - pa), pm >= pa, g["winner"] == cote) * coef
        total += pts
        detail.append(dict(date=jour, competition=g["contest"].get("name"), adversaire=f'{adv["person"]["givenName"]} {adv["person"]["familyName"]}',
                           points_moi=pm, points_adv=pa, victoire=g["winner"] == cote, coef=coef, points=pts))
    brut, debut = total, None
    if corriger and detail:
        # Les points affichés sont les points actuels, qui incluent déjà les gains de la période.
        # On estime les points de début de période (actuels - gains) et on recalcule, jusqu'à stabilité.
        actuel = detail[0]["points_moi"]
        debut = actuel
        for _ in range(10):
            for d in detail:
                d["points"] = bareme_points(bareme, abs(debut - d["points_adv"]), debut >= d["points_adv"], d["victoire"]) * d["coef"]
            total = sum(d["points"] for d in detail)
            debut = actuel - total
    comps = {}
    for d in detail:
        comps[d["competition"]] = comps.get(d["competition"], 0) + 1
    return dict(nom=jeune.get("nom") or jeune["licence"], licence=jeune["licence"], total=total, brut=brut,
                points_debut_estimes=None if debut is None else round(debut), parties=len(detail),
                tournois=sum("TOURNOI" in (d["competition"] or "").upper() for d in detail), competitions=comps, detail=detail)


def nom_competition(c):
    c = (c or "").replace("FED_", "").replace("D78_", "").replace("L08_", "")
    if "TOURNOI" in c.upper():
        return "au tournoi de " + c.split("_", 1)[-1].split(" ")[0].title()
    return "au " + c.replace("Championnat de France par Equipes", "championnat par équipes").split(" Masculin")[0].split(" Féminin")[0]


def message(classement, du, au, bareme):
    medailles = ["🥇", "🥈", "🥉"]
    lignes = [f"🏓 Podium progression des jeunes de SQY Ping – du {du} au {au} (tournois compris)"]
    for m, r in zip(medailles, classement[:3]):
        hors_equipes = {c: n for c, n in r["competitions"].items() if "Equipes" not in c}
        precision = ""
        if hors_equipes:
            c, n = max(hors_equipes.items(), key=lambda x: x[1])
            precision = f", dont {n} {nom_competition(c)}"
        lignes.append(f"{m} {r['nom']} : {r['total']:+.0f} pts ({r['parties']} parties{precision})")
    lignes.append("Bravo à eux ! Classement virtuel estimé, à confirmer avec les points officiels.")
    return "\n".join(lignes)


def envoyer_discord(texte):
    url = os.environ.get("DISCORD_WEBHOOK_URL")
    if not url:
        sys.exit("DISCORD_WEBHOOK_URL non définie : rien n'a été envoyé.")
    req = urllib.request.Request(url, data=json.dumps({"content": texte, "allowed_mentions": {"parse": []}}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "sqy-ping-progression"})
    urllib.request.urlopen(req, timeout=30)
    print("Envoyé sur Discord.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--du", required=True); ap.add_argument("--au", required=True)
    ap.add_argument("--discord", action="store_true", help="envoyer le podium sur Discord")
    ap.add_argument("--points-actuels", action="store_true",
                    help="ne pas estimer les points de début de période (calcul brut sur les points actuels)")
    a = ap.parse_args()
    jeunes = charger("jeunes.json", '[{"licence": "7885025", "nom": "Prénom NOM"}]')
    bareme = charger("bareme.json", '{"source": "RG 2026-2027 art. IV.205.1", "lignes": [...]}')
    classement = sorted((bilan(j, bareme, a.du, a.au, corriger=not a.points_actuels) for j in jeunes), key=lambda r: -r["total"])
    json.dump(classement, open("progression.json", "w"), ensure_ascii=False, indent=1)
    for i, r in enumerate(classement, 1):
        print(f"{i:>2}. {r['nom']:<28} {r['total']:+7.1f}  (brut {r['brut']:+6.1f}, {r['parties']} parties, {r['tournois']} en tournoi)")
    texte = message(classement, a.du, a.au, bareme)
    print("\n" + texte)
    if a.discord:
        envoyer_discord(texte)
