"""Onglet « Équipes » : une fiche courte par équipe SQY (situation, prochain match, compositions probables)."""
import json, re, html, datetime

site = json.load(open("site.json"))
JOURS = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

def fd(d):
    if not d: return "date à fixer"
    x = datetime.date.fromisoformat(d); return f"{JOURS[x.weekday()]} {x.day} {MOIS[x.month - 1]}"
def pc(x):
    v = round(x * 100)
    return "plus de 99 %" if x < 1 and v == 100 else ("moins de 1 %" if x > 0 and v == 0 else f"{v} %")
def fp(x): return f"{round(x):,}".replace(",", " ")
def esc(s): return html.escape(str(s))
def place(r): return "1er" if r == 1 else f"{r}e"
def rank(p, tid):
    pts = sorted((v["pts"] for v in p["teams"].values()), reverse=True)
    return 1 + sum(1 for x in pts if x > p["teams"][tid]["pts"])

def lineup(c):
    if not c or not c.get("probable"): return '<span class="muted">composition inconnue</span>', None
    rows = c["probable"]
    avg = sum(r["points"] for r in rows) / len(rows)
    names = ", ".join(f'{esc(r["name"])} <span class="muted">{fp(r["points"])}</span>' for r in rows)
    return names, avg

cards = []
for p in site:
    for tid, s in p["sqy"].items():
        T = p["teams"][tid]; num = int(re.search(r"(\d+)\s*$", T["name"]).group(1))
        lab = ("Dames " if p["fem"] else "SQY ") + str(num)
        rk = rank(p, tid); n = p["n"]; upn = p.get("upn", 1)
        if s["up"] >= 0.5: stake, cls = f"En course pour la montée ({pc(s['up'])})", "ok"
        elif s["down"] >= 0.3: stake, cls = f"Maintien en danger (descente {pc(s['down'])})", "bad"
        elif s["up"] >= 0.1: stake, cls = f"Peut encore viser la montée ({pc(s['up'])})", "mid"
        elif s["down"] >= 0.1: stake, cls = f"Doit encore assurer le maintien (descente {pc(s['down'])})", "warn"
        else: stake, cls = "Phase sans grand enjeu : milieu de tableau", "mid"
        mine, myavg = lineup((p.get("compo") or {}).get(tid))
        c = (p.get("compo") or {}).get(tid) or {}
        lines = [f'<p><b>Notre équipe probable</b> : {mine}' + (f' <span class="muted">· moyenne {fp(myavg)}</span>' if myavg else "") + "</p>"]
        al = [esc(r["name"]) for r in c.get("alerts", [])]
        if al: lines.append(f'<p class="warnline">À 1 match du brûlage : {", ".join(al)}. Une rencontre de plus dans une équipe au-dessus et il ne pourra plus jouer ici.</p>')
        if s["matches"]:
            m = s["matches"][0]; opp = str(m["opp"]); O = p["teams"][opp]
            theirs, theiravg = lineup((p.get("compo") or {}).get(opp))
            oc = (p.get("compo") or {}).get(opp) or {}
            lines.insert(0, f'<p><b>Prochain match</b> : J{m["round"]}, {fd(m["date"])}, {"contre" if m["home"] else "à"} <b>{esc(O["name"])}</b> '
                            f'<span class="muted">({place(rank(p, opp))}, {O["pts"]} pts)</span> · <b>{pc(m["pwin"])}</b> de chances de victoire</p>')
            lines.append(f'<p><b>Leur équipe probable</b> : {theirs}' + (f' <span class="muted">· moyenne {fp(theiravg)}</span>' if theiravg else "") + "</p>")
            br = [esc(r["name"]) + f' <span class="muted">{fp(r["points"])}</span>' for r in oc.get("burned", [])]
            if br: lines.append(f'<p class="muted">Ne peuvent plus jouer chez eux (brûlés) : {", ".join(br)}</p>')
            if len(s["matches"]) > 1:
                rest = " · ".join(f'J{x["round"]} {"contre" if x["home"] else "à"} {esc(p["teams"][str(x["opp"])]["name"])} ({pc(x["pwin"])})' for x in s["matches"][1:])
                lines.append(f'<p class="muted">Ensuite : {rest}</p>')
        else:
            lines.insert(0, "<p><b>Phase terminée</b> pour cette équipe.</p>")
        cards.append(((p["fem"], num), f'''<article class="tc" id="eq-{"f" if p["fem"] else "m"}{num}">
<header><h3>{lab} <span class="muted">· {esc(p["division"])} · poule {esc(p["pool"])}</span></h3>
<div class="tcpills"><span class="pill mid">{place(rk)} / {n} · {T["pts"]} pts ({T["V"]}V {T["N"]}N {T["D"]}D)</span><span class="pill {cls}">{stake}</span></div></header>
{"".join(lines)}
</article>'''))

cards.sort(key=lambda x: x[0])
men = "".join(c for k, c in cards if not k[0]); women = "".join(c for k, c in cards if k[0])
section = f'''<header><h1>Les équipes de SQY Ping</h1>
<p class="lede">Une fiche par équipe : situation, prochain match et compositions probables (règles de brûlage FFTT appliquées). Le détail des scénarios est dans les onglets Montée et Descente.</p></header>
<section><h2>Messieurs</h2><div class="tcs">{men}</div></section>
<section><h2>Dames</h2><div class="tcs">{women}</div></section>'''
CSS = """.tcs{display:grid;gap:12px} .tc{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px;display:grid;gap:6px;min-width:0}
.tc h3{font-family:var(--display);font-size:1.35rem;font-weight:700;margin:0} .tc h3 .muted{font-family:var(--body);font-size:.92rem;font-weight:400}
.tc p{margin:0;max-width:80ch} .tcpills{display:flex;flex-wrap:wrap;gap:6px;margin-top:4px} .tc header{display:grid;gap:2px}
.warnline{color:var(--warn)}"""
json.dump(dict(html=section, css=CSS), open("team_cards.json", "w"), ensure_ascii=False)
print(len(cards), "fiches")
