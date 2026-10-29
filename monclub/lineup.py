"""Compositions probables selon les règles de brûlage FFTT 2026-2027 (art. II.112.1).

Règles appliquées :
  - Un joueur ayant disputé 2 rencontres de la phase dans des équipes de numéro
    inférieur à X ne peut plus jouer en équipe X (brûlé).
  - Deux équipes d'un même club dans une même poule : un joueur qui a joué pour
    l'une ne peut plus jouer pour l'autre.
  - Brûlage séparé entre championnat masculin et féminin (II.112.3).
"""
import re, collections

def team_num(name):
    m = re.findall(r"(\d+)", name or "")
    return int(m[-1]) if m else None

def build(clubs_apps):
    """Index : (club, genre) -> joueurs avec leurs participations, et équipe -> (club, genre, numéro, poule)."""
    players = {}   # (cid, gender) -> lic -> dict(name, points, last, apps=[(teamId, num, round)])
    teams = {}     # teamId -> dict(cid, gender, num, pool, name)
    for cid, rec in clubs_apps.items():
        for tid, t in rec["teams"].items():
            teams[int(tid)] = dict(cid=cid, gender=t["gender"], num=team_num(t["name"]), pool=t["pool"], name=t["name"])
        seen = set()
        for a in sorted(rec["apps"], key=lambda a: a["date"]):
            key = (a["lic"], a["team"], a["round"], a["date"])
            if key in seen: continue
            seen.add(key)
            P = players.setdefault((cid, a["gender"]), {}).setdefault(a["lic"], dict(name=a["name"], points=a["points"], last="", apps=[]))
            P["apps"].append((a["team"], team_num(rec["teams"].get(str(a["team"]), {}).get("name")), a["round"]))
            if a["date"] >= P["last"]: P["last"], P["points"] = a["date"], a["points"]
    return players, teams

def status(P, tid, num, pool, teams):
    """Renvoie (qualifié, nb de rencontres dans des équipes de numéro inférieur, raison)."""
    lower = sum(1 for t, n, r in P["apps"] if n is not None and num is not None and n < num)
    if lower >= 2:
        return False, lower, "brûlé (2 rencontres en équipe de numéro inférieur)"
    for t, n, r in P["apps"]:
        if t != tid and teams.get(t, {}).get("pool") == pool:
            return False, lower, "a déjà joué pour l'autre équipe du club dans cette poule"
    return True, lower, ""

def candidates(tid, players, teams, k):
    T = teams.get(tid)
    if not T or T["num"] is None: return None
    club = players.get((T["cid"], T["gender"]), {})
    played_rounds = {r for P in club.values() for t, n, r in P["apps"] if t == tid}
    J = max(1, len(played_rounds))
    reg, up, down, burned = [], [], [], []
    for lic, P in club.items():
        inT = sum(1 for t, n, r in P["apps"] if t == tid)
        ok, lower, why = status(P, tid, T["num"], T["pool"], teams)
        nums = [n for t, n, r in P["apps"] if n is not None]
        row = dict(lic=lic, name=P["name"], points=P["points"], inT=inT, J=J, lower=lower,
                   main=collections.Counter(nums).most_common(1)[0][0] if nums else None)
        if not ok:
            if inT: burned.append(dict(row, why=why))
            continue
        if inT: reg.append(row)
        elif row["main"] is not None and row["main"] > T["num"]: down.append(row)   # joue habituellement plus bas : renfort possible
        elif row["main"] is not None and row["main"] < T["num"]: up.append(row)     # joue plus haut, encore qualifié
    reg.sort(key=lambda r: (-r["inT"], -r["points"]))
    down.sort(key=lambda r: -r["points"]); up.sort(key=lambda r: -r["points"])
    probable = reg[:k]
    if len(probable) < k: probable += down[:k - len(probable)]
    bench = [r for r in reg[k:]] + [r for r in down if r not in probable][:3]
    # à 1 rencontre du brûlage : une apparition de plus dans une équipe plus haute et il ne pourra plus jouer ici
    alerts = [r for r in probable if r["lower"] == 1]
    return dict(J=J, k=k, probable=probable, bench=bench[:4], up=up[:3], burned=burned, alerts=alerts, regulars=reg, renforts=down[:3])

def sample(c, rnd):
    """Tire une composition : chaque habitué est présent selon sa fréquence ; on complète avec les renforts."""
    k = c["k"]; present = []
    for r in c["regulars"]:
        if rnd.random() < min(0.95, r["inT"] / c["J"] + 0.05): present.append(r)
    present.sort(key=lambda r: (-r["inT"], rnd.random()))
    team = present[:k]
    pool = [r for r in c["renforts"] + c["regulars"] if r not in team]
    while len(team) < k and pool:
        team.append(pool.pop(0))
    return team
