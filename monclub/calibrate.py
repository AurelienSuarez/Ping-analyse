"""Calibre le modèle partie par partie sur les feuilles de match de la phase et vérifie sa fiabilité.

Sorties :
  calibration.json        paramètres utilisés par simulate_v3.py
  calibration_report.json comparaison prévu / réalisé, affichée sur le site
"""
import json, glob, math, random, collections

def load_games():
    rows = []    # (écart, domicile gagne, double)
    matches = [] # rencontres jouées : compositions, feuille, résultat
    for f in glob.glob("cache/_api_sport_matches_[0-9]*.json"):
        m = json.load(open(f))
        pts = {}
        for sh in ("homeSheetMatches", "awaySheetMatches"):
            for sp in m.get(sh) or []:
                p = sp.get("player")
                if p and p.get("points"): pts[p["identifier"]] = p["points"]
        games = m.get("games") or []
        ok_match = bool(games) and not m.get("penalty") and not m.get("forfeit")
        hw = aw = 0; glist = []
        for g in games:
            if g.get("forfeit") or g.get("penalty") or g.get("abandonment") or g.get("notCounted") or g["winner"] not in ("home", "away"):
                ok_match = False; continue
            idf = lambda *ks: [(g.get(x) or {}).get("identifier") for x in ks if g.get(x)]
            h = idf("homePlayer", "homeTeammatePlayer"); a = idf("awayPlayer", "awayTeammatePlayer")
            if not h or not a or any(i not in pts for i in h + a):
                ok_match = False; continue
            ph = sum(pts[i] for i in h) / len(h); pa = sum(pts[i] for i in a) / len(a)
            dbl = bool(g.get("doubleOpposition"))
            rows.append((ph - pa, 1 if g["winner"] == "home" else 0, dbl))
            glist.append((ph - pa, dbl))
            hw += g["winner"] == "home"; aw += g["winner"] == "away"
        if ok_match and glist and hw + aw == len(games):
            matches.append(dict(games=glist, hw=hw, aw=aw))
    return rows, matches

def fit(sub):
    def ll(D, h):
        s = 0
        for d, w, _ in sub:
            p = 1 / (1 + 10 ** (-(d + h) / D)); p = min(max(p, 1e-6), 1 - 1e-6)
            s += math.log(p if w else 1 - p)
        return s
    D = max(range(150, 801, 5), key=lambda D: ll(D, 0))
    h = max(range(-40, 41, 1), key=lambda h: ll(D, h))
    D = max(range(150, 801, 5), key=lambda D: ll(D, h))
    return D, h

rows, matches = load_games()
Ds, hs = fit([r for r in rows if not r[2]])
Dd, hd = fit([r for r in rows if r[2]])
cal = dict(D_simple=Ds, home_simple=hs, D_double=Dd, home_double=hd, n_simple=sum(1 for r in rows if not r[2]), n_double=sum(1 for r in rows if r[2]))
json.dump(cal, open("calibration.json", "w"), indent=1)

# Forme du jour : décalage commun à toutes les parties d'une rencontre (les parties d'une même soirée ne sont pas indépendantes)
def p(d, dbl, f=0): return 1 / (1 + 10 ** (-(d + f + (hd if dbl else hs)) / (Dd if dbl else Ds)))
def sim(m, sig, R=600, rnd=random.Random(3)):
    w = dr = 0; n = len(m["games"])
    for _ in range(R):
        f = rnd.gauss(0, sig) if sig else 0
        hw = sum(rnd.random() < p(d, dbl, f) for d, dbl in m["games"])
        w += hw > n - hw; dr += hw == n - hw
    return w / R, dr / R
def loglik(sig):
    s = 0
    for m in matches:
        pw, pd = sim(m, sig); real = "w" if m["hw"] > m["aw"] else ("d" if m["hw"] == m["aw"] else "l")
        s += math.log(max({"w": pw, "d": pd, "l": 1 - pw - pd}[real], 1e-4))
    return s
sigma = max((0, 40, 60, 80, 100, 120), key=loglik)
cal["form_sigma"] = sigma
json.dump(cal, open("calibration.json", "w"), indent=1)

buckets = collections.defaultdict(lambda: [0, 0, 0.0])
draws_real = draws_pred = 0.0
for m in matches:
    pw, pd = sim(m, sigma)
    real = 1 if m["hw"] > m["aw"] else 0
    draws_real += m["hw"] == m["aw"]; draws_pred += pd
    b = min(9, int(pw * 10)); B = buckets[b]; B[0] += 1; B[1] += real; B[2] += pw
report = dict(cal, n_matches=len(matches), draw_real=draws_real / len(matches), draw_pred=draws_pred / len(matches),
              buckets=[dict(lo=b / 10, hi=(b + 1) / 10, n=v[0], real=v[1] / v[0], pred=v[2] / v[0]) for b, v in sorted(buckets.items())])
json.dump(report, open("calibration_report.json", "w"), indent=1)
print(json.dumps(cal))
print(f"{len(matches)} rencontres complètes ; nuls réels {report['draw_real']:.1%} / prévus {report['draw_pred']:.1%}")
for b in report["buckets"]:
    print(f"  prévu {b['lo']:.0%}-{b['hi']:.0%}  n={b['n']:4}  prévu moyen {b['pred']:5.1%}  réalisé {b['real']:5.1%}")
