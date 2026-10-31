"""Simulation partie par partie des fins de phase, avec compositions (brûlage) et départage officiel FFTT.

- Chaque rencontre restante est jouée partie par partie selon la feuille de la poule
  (14 parties à 4 joueurs, 10 parties à 3 joueurs), doubles compris.
- Probabilité de gagner une partie : 1 / (1 + 10^(-écart/D)), écart = points du joueur
  (ou moyenne de la paire) - points de l'adversaire, + avantage à domicile.
  D et l'avantage à domicile sont calibrés sur les parties de la phase (calibrate.py).
- Départage des ex æquo : règlements sportifs FFTT, art. I.202.1
  (rencontres entre équipes à égalité : points-rencontres, puis quotient des parties,
  puis quotient des manches ; la procédure recommence pour les équipes encore à égalité).
"""
import json, random, statistics, collections, os, sys
import lineup

N = int(os.environ.get("NSIM", 20000))
CAL = json.load(open("calibration.json"))
D_S, D_D, HOME_S, HOME_D = CAL["D_simple"], CAL["D_double"], CAL["home_simple"], CAL["home_double"]
FORM = CAL.get("form_sigma", 0)
random.seed(7)

def p_single(a, b, home, f=0): return 1 / (1 + 10 ** (-((a - b) + f + (HOME_S if home else -HOME_S)) / D_S))
def p_double(a, b, home, f=0): return 1 / (1 + 10 ** (-((a - b) + f + (HOME_D if home else -HOME_D)) / D_D))

raw = json.load(open("site_raw.json"))
PLAYERS, TEAMS = lineup.build(json.load(open("clubs_apps.json")))
OVR = json.load(open("overrides.json"))["joueurs_ajoutes"]

def sheet_lines(pool_id):
    d = json.load(open(f"cache/_api_pools_{pool_id}.json"))
    return [(l["homePlayer"], l["awayPlayer"]) for l in d["playerOppositionSheet"]["lines"]]

def play_match(hl, al, lines, rnd):
    """hl, al : points des joueurs domicile / extérieur. Renvoie (parties dom, parties ext)."""
    letters_h, letters_a = "ABCD"[:len(hl)], ("WXYZ" if len(hl) == 4 else "XYZ")[:len(al)]
    H = dict(zip(letters_h, rnd.sample(hl, len(hl))))   # ordre sur la feuille inconnu : tiré au hasard
    A = dict(zip(letters_a, rnd.sample(al, len(al))))
    hw = aw = 0
    ndouble = sum(1 for l in lines if l[0] == "*")
    hp, ap = hl[:], al[:]; rnd.shuffle(hp); rnd.shuffle(ap)
    pairs_h = [hp[0:2], hp[2:4]] if len(hp) == 4 else [hp[0:2]]
    pairs_a = [ap[0:2], ap[2:4]] if len(ap) == 4 else [ap[0:2]]
    di = 0
    f = rnd.gauss(0, FORM) if FORM else 0   # forme du jour, commune à toute la rencontre
    for h, a in lines:
        if h == "*":
            ph, pa = pairs_h[di % len(pairs_h)], pairs_a[di % len(pairs_a)]; di += 1
            p = p_double(sum(ph) / 2, sum(pa) / 2, True, f)
        else:
            p = p_single(H[h], A[a], True, f)
        if rnd.random() < p: hw += 1
        else: aw += 1
    return hw, aw

def tiebreak(group, results, rnd):
    """Art. I.202.1 : classe un groupe d'équipes à égalité de points-rencontres."""
    if len(group) <= 1: return list(group)
    g = set(group)
    rp = collections.Counter(); pw = collections.Counter(); pl = collections.Counter(); mw = collections.Counter(); ml = collections.Counter()
    for h, a, hp, ap, hg, ag, hm, am in results:
        if h in g and a in g:
            rp[h] += hp; rp[a] += ap
            pw[h] += hg; pl[h] += ag; pw[a] += ag; pl[a] += hg
            mw[h] += hm; ml[h] += am; mw[a] += am; ml[a] += hm
    q = lambda w, l: (w / l) if l else (float("inf") if w else 0)
    for key in (lambda t: rp[t], lambda t: q(pw[t], pl[t]), lambda t: q(mw[t], ml[t])):
        vals = collections.defaultdict(list)
        for t in group: vals[key(t)].append(t)
        if len(vals) > 1:
            out = []
            for v in sorted(vals, reverse=True):
                sub = vals[v]
                out += tiebreak(sub, results, rnd) if len(sub) < len(group) else sub
            return out
    group = list(group); rnd.shuffle(group)   # tirage au sort en dernier recours
    return group

def final_order(teams, pts, results, rnd):
    by = collections.defaultdict(list)
    for t in teams: by[pts[t]].append(t)
    out = []
    for v in sorted(by, reverse=True): out += tiebreak(by[v], results, rnd)
    return out

def played_detail(mid):
    d = json.load(open(f"cache/_api_sport_matches_{mid}.json"))
    games = [g for g in d.get("games") or [] if g.get("winner") in ("home", "away")]
    hg = sum(1 for g in games if g["winner"] == "home"); ag = sum(1 for g in games if g["winner"] == "away")
    return hg, ag, d.get("homeGamePoints") or 0, d.get("awayGamePoints") or 0

site = []
for P in raw:
    teams = {int(k): v for k, v in P["teams"].items()}
    k = P["nplay"]; lines = sheet_lines(P["pool"])
    compo = {t: lineup.candidates(t, PLAYERS, TEAMS, k, [o for o in OVR if o["equipe"] == teams[t] and o["genre"] == ("F" if P["fem"] else "M")]) for t in teams}
    strength = {}
    for t in teams:
        c = compo[t]
        strength[t] = statistics.mean(r["points"] for r in c["probable"]) if c and len(c["probable"]) == k else None
    known = [v for v in strength.values() if v]
    for t in teams:
        if strength[t] is None: strength[t] = statistics.mean(known)
    base = {t: dict(pts=0, J=0, V=0, N=0, D=0) for t in teams}
    played_res = []
    for m in P["played"]:
        hg, ag, hm, am = played_detail(m["id"])
        played_res.append((m["home"], m["away"], m["hp"], m["ap"], hg, ag, hm, am))
        for me, side in ((m["home"], "h"), (m["away"], "a")):
            b = base[me]; b["J"] += 1; b["pts"] += m[side + "p"]
            if m["draw"]: b["N"] += 1
            elif m["winner"] == ("home" if side == "h" else "away"): b["V"] += 1
            else: b["D"] += 1
    n = len(teams); down = 2; upn = 2 if "Pré-Régionale" in P["division"] else 1
    sqys = [t for t in teams if "SQY" in teams[t].upper()]
    fut = P["future"]
    myf = {t: [i for i, m in enumerate(fut) if t in (m["home"], m["away"])] for t in sqys}
    myset = {t: set(v) for t, v in myf.items()}
    res = {t: dict(up=0, down=0, ranks=collections.Counter(), byk=collections.defaultdict(lambda: [0, 0, 0]),
                   combo=collections.defaultdict(lambda: [0, 0, 0]), others=collections.defaultdict(lambda: [0, 0, 0]),
                   mw=collections.Counter()) for t in sqys}
    draws = 0; nm = 0
    for _ in range(N):
        lu = {}
        for t in teams:
            c = compo[t]
            if c and c["regulars"]:
                s = lineup.sample(c, random)
                lu[t] = [r["points"] for r in s] if len(s) == k else [strength[t]] * k
            else: lu[t] = [strength[t]] * k
        pts = {t: base[t]["pts"] for t in teams}; wins = collections.Counter(); results = list(played_res); outc = []
        for i, m in enumerate(fut):
            hg, ag = play_match(lu[m["home"]], lu[m["away"]], lines, random)
            if hg > ag: hp, ap, r = 3, 1, 1; wins[m["home"]] += 1
            elif hg < ag: hp, ap, r = 1, 3, -1; wins[m["away"]] += 1
            else: hp, ap, r = 2, 2, 0; draws += 1
            nm += 1
            pts[m["home"]] += hp; pts[m["away"]] += ap
            results.append((m["home"], m["away"], hp, ap, hg, ag, 0, 0)); outc.append((m["home"], r))
        order = final_order(list(teams), pts, results, random)
        for t in sqys:
            rk = order.index(t) + 1; R = res[t]; R["ranks"][rk] += 1
            u = rk <= upn; d = rk > n - down
            R["up"] += u; R["down"] += d
            bk = R["byk"][wins[t]]; bk[0] += 1; bk[1] += u; bk[2] += d
            key = "".join({1: "V", 0: "N", -1: "D"}[r if h == t else -r] for h, r in (outc[i] for i in myf[t]))
            cb = R["combo"][key]; cb[0] += 1; cb[1] += u; cb[2] += d
            for i, (h, r) in enumerate(outc):
                if i in myset[t]: R["mw"][(i, (r if h == t else -r))] += 1
                else:
                    o = R["others"][f"{i}:{r}"]; o[0] += 1; o[1] += u; o[2] += d
    def slim(rows): return [dict(name=r["name"], points=r["points"], inT=r["inT"], J=r["J"], lower=r["lower"], main=r["main"],
                                 why=r.get("why", ""), forced=r.get("forced"), note=r.get("note", "")) for r in rows]
    pool = dict(pool=P["poolName"], division=P["division"], fem=P["fem"], n=n, down=down, upn=upn, nopp=P["nopp"],
                teams={t: dict(name=teams[t], strength=round(strength[t]), **base[t]) for t in teams},
                played=[{kk: m[kk] for kk in ("date", "round", "home", "away", "hp", "ap", "winner", "draw", "forfeit")} for m in P["played"]],
                future=[{kk: m[kk] for kk in ("date", "round", "home", "away")} for m in fut],
                players={int(t): sorted(v.values(), key=lambda x: (-x["n"], -x["points"])) for t, v in P["players"].items()},
                compo={t: (None if not compo[t] else {kk: slim(compo[t][kk]) for kk in ("probable", "bench", "burned", "alerts", "renforts", "up")}) for t in teams},
                draw_rate=draws / max(1, nm), sqy={})
    for t in sqys:
        R = res[t]; nf = len(myf[t])
        mts = []
        for i in myf[t]:
            m = fut[i]; opp = m["away"] if m["home"] == t else m["home"]
            mts.append(dict(opp=opp, home=m["home"] == t, date=m["date"], round=m["round"],
                            pwin=R["mw"][(i, 1)] / N, pdraw=R["mw"][(i, 0)] / N))
        # feuille de duels pour chaque rencontre : chances de chaque joueur SQY contre chaque adversaire probable
        duels = []
        for mt in mts:
            mine = (compo[t] or {}).get("probable") or []; theirs = (compo[mt["opp"]] or {}).get("probable") or []
            duels.append([[round(p_single(a["points"], b["points"], mt["home"]), 3) for b in theirs] for a in mine])
        for mt, du in zip(mts, duels): mt["duels"] = du
        pool["sqy"][t] = dict(up=R["up"] / N, down=R["down"] / N, remaining=nf,
                              ranks={r: c / N for r, c in sorted(R["ranks"].items())},
                              combo={kk: v for kk, v in R["combo"].items()},
                              others=[dict(i=i, home=fut[i]["home"], away=fut[i]["away"], round=fut[i]["round"], date=fut[i]["date"],
                                           res={r: R["others"].get(f"{i}:{r}", [0, 0, 0]) for r in (1, 0, -1)}) for i in range(len(fut)) if i not in myset[t]],
                              byk=[dict(k=kk, p=v[0] / N, up=v[1] / v[0], down=v[2] / v[0]) for kk, v in sorted(R["byk"].items())],
                              matches=mts)
        print(f'{teams[t]:<14}{P["division"]:<26} up {R["up"]/N:5.0%} down {R["down"]/N:5.0%} nuls {draws/max(1,nm):4.0%}', flush=True)
    site.append(pool)
json.dump(site, open("site.json", "w"), ensure_ascii=False)
