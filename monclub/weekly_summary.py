"""Archive les chances de chaque équipe SQY et produit l'encadré « Ce qui a changé cette semaine »."""
import json, os, re, glob, datetime, html

HIST = "history"
site = json.load(open("site.json"))
today = datetime.date.today()

def label(p, tid):
    num = re.search(r"(\d+)\s*$", p["teams"][tid]["name"]).group(1)
    return ("Dames " if p["fem"] else "SQY ") + num

snap = {}
for p in site:
    for tid, s in p["sqy"].items():
        snap[label(p, tid)] = dict(up=s["up"], down=s["down"], division=p["division"])

os.makedirs(HIST, exist_ok=True)
prev_files = sorted(f for f in glob.glob(f"{HIST}/*.json") if os.path.basename(f) < f"{today.isoformat()}.json")
json.dump(snap, open(f"{HIST}/{today.isoformat()}.json", "w"), ensure_ascii=False, indent=1)

def pc(x):
    v = round(x * 100)
    return "plus de 99 %" if x < 1 and v == 100 else ("moins de 1 %" if x > 0 and v == 0 else f"{v} %")
items = []
if prev_files:
    prev = json.load(open(prev_files[-1]))
    since = datetime.date.fromisoformat(os.path.basename(prev_files[-1])[:10])
    moves = []
    for k, v in snap.items():
        if k not in prev: continue
        du = v["up"] - prev[k]["up"]; dd = v["down"] - prev[k]["down"]
        if abs(du) >= 0.05: moves.append((abs(du), f"<li><b>{k}</b> ({html.escape(v['division'])}) : montée {pc(prev[k]['up'])} → <b>{pc(v['up'])}</b></li>"))
        if abs(dd) >= 0.05: moves.append((abs(dd), f"<li><b>{k}</b> ({html.escape(v['division'])}) : descente {pc(prev[k]['down'])} → <b>{pc(v['down'])}</b></li>"))
    moves.sort(key=lambda x: -x[0])
    head = f"Depuis le {since.day}/{since.month:02d}"
    items.append(f"<p class=\"lab\">{head} : les plus gros changements</p>" +
                 ("<ul>" + "".join(m for _, m in moves[:6]) + "</ul>" if moves else "<p>Aucun changement de plus de 5 points.</p>"))

# rencontres des 7 prochains jours qui pèsent le plus
nxt = []
for p in site:
    for tid, s in p["sqy"].items():
        for m in s["matches"]:
            if not m["date"]: continue
            d = datetime.date.fromisoformat(m["date"])
            if today <= d <= today + datetime.timedelta(days=7):
                opp = html.escape(p["teams"][str(m["opp"])]["name"])
                stake = "la montée" if s["up"] >= 0.1 else ("le maintien" if s["down"] >= 0.1 else "")
                if stake and 0.15 <= m["pwin"] <= 0.85:
                    nxt.append((abs(m["pwin"] - 0.5), f"<li>{d.day}/{d.month:02d} · <b>{label(p, tid)}</b> {'contre' if m['home'] else 'à'} {opp} : {pc(m['pwin'])} de chances de victoire, l'équipe joue {stake}</li>"))
nxt.sort()
if nxt:
    items.append("<p class=\"lab\">Les rencontres indécises des 7 prochains jours, pour les équipes qui jouent la montée ou le maintien</p><ul>" + "".join(x for _, x in nxt[:8]) + "</ul>")

box = ""
if items:
    title = "Ce qui a changé cette semaine" if prev_files else "Cette semaine"
    box = (f"<section class=\"week\"><h2>{title}</h2>" + "".join(items) + "</section>")
open("weekly_box.html", "w").write(box)
print("résumé :", len(items), "bloc(s)")
