import json,re,html
res=json.load(open("standings.json"))
def lvl(d):
    d=d.replace("FED_","").replace("L08_","").replace("D78_","")
    d=re.sub(r"\s*[Pp]hase 1","",d).replace("Pre-Regionale","Pré-Régionale").replace("Departementale","Départementale")
    d=d.replace("R1","Régionale 1")
    return d.strip()
ORDER=["Nationale 2","Nationale 3","Régionale 1","Pré-Régionale","Départementale 1","Départementale 2","Départementale 3","Départementale 4"]
teams=[]
for r in res:
    fem="Féminin" in r["contest"]
    n=len(r["rows"])
    for i,x in enumerate(r["rows"]):
        if "SQY" in x["name"].upper():
            num=int(re.search(r"(\d+)\s*$",x["name"]).group(1))
            rk=1+sum(1 for y in r["rows"] if y["pts"]>x["pts"]); tie=sum(1 for y in r["rows"] if y["pts"]==x["pts"])>1
            teams.append(dict(r=r,fem=fem,num=num,rank=rk,tie=tie,n=n,row=x,div=lvl(r["division"])))
teams.sort(key=lambda t:(t["fem"],t["num"]))
def chip(t):
    lab=("1er" if t["rank"]==1 else f'{t["rank"]}e')+(" ex æquo" if t["tie"] else "")
    cls=" up" if t["rank"]==1 else (" down" if t["rank"]>=t["n"]-1 else "")
    return f'<span class="chip{cls}">{lab}</span>'
def rows_summary(fem):
    out=[]
    for t in [t for t in teams if t["fem"]==fem]:
        x=t["row"]; anchor=f'{"f" if fem else "m"}{t["num"]}'
        out.append(f'<tr><td class="team"><a href="#{anchor}">{"Dames" if fem else "SQY"} {t["num"]}</a></td><td>{html.escape(t["div"])} <span class="muted">· poule {t["r"]["pool"]}</span></td><td class="c">{chip(t)}<span class="muted"> / {t["n"]}</span></td><td class="c num">{x["pts"]}</td><td class="c num">{x["V"]}-{x["N"]}-{x["D"]}</td></tr>')
    return "\n".join(out)
def pool_block(t):
    r=t["r"]; anchor=f'{"f" if t["fem"] else "m"}{t["num"]}'
    trs=[]
    for i,x in enumerate(r["rows"]):
        me=' class="me"' if "SQY" in x["name"].upper() else ""
        rk=1+sum(1 for y in r["rows"] if y["pts"]>x["pts"])
        trs.append(f'<tr{me}><td class="c num">{rk}</td><td>{html.escape(x["name"])}</td><td class="c num">{x["J"]}</td><td class="c num">{x["V"]}</td><td class="c num">{x["N"]}</td><td class="c num">{x["D"]}</td><td class="c num strong">{x["pts"]}</td></tr>')
    title=f'{"SQY Ping " + str(t["num"]) + " (dames)" if t["fem"] else t["row"]["name"].title().replace("Sqy","SQY")}'
    return f'''<details id="{anchor}"><summary><span class="st">{html.escape(title)}</span><span class="sd">{html.escape(t["div"])} · poule {r["pool"]} · {chip(t)}</span></summary>
<div class="tw"><table class="pool"><thead><tr><th class="c">Clt</th><th>Équipe</th><th class="c">J</th><th class="c">V</th><th class="c">N</th><th class="c">D</th><th class="c">Pts</th></tr></thead><tbody>{"".join(trs)}</tbody></table></div></details>'''
leaders=sum(1 for t in teams if t["rank"]==1)
unbeaten=sum(1 for t in teams if t["row"]["D"]==0)
bottom=sum(1 for t in teams if t["rank"]>=t["n"]-1)
page=f'''<title>Classements SQY Ping</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Source+Sans+3:wght@400;600&display=swap">
<style>
/* Layout: une colonne lisible — synthèse en tête, puis une poule dépliable par équipe */
:root{{--bg:#f6f7f9;--surface:#ffffff;--fg:#17202b;--muted:#5d6876;--line:#dde2e8;--accent:#1d5fd1;--me:#e8f0fd;--up:#1f7a4d;--upbg:#e3f4ea;--down:#b3372b;--downbg:#fbe7e4;
--display:"Barlow Condensed","Arial Narrow",sans-serif;--body:"Source Sans 3","Segoe UI",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#11161d;--surface:#18202a;--fg:#e7ecf2;--muted:#9aa6b4;--line:#2a3542;--accent:#7aa8f5;--me:#1e3050;--up:#6fd3a0;--upbg:#173528;--down:#f19a8f;--downbg:#3d1e1b;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#11161d;--surface:#18202a;--fg:#e7ecf2;--muted:#9aa6b4;--line:#2a3542;--accent:#7aa8f5;--me:#1e3050;--up:#6fd3a0;--upbg:#173528;--down:#f19a8f;--downbg:#3d1e1b;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:16px/1.5 var(--body)}}
.wrap{{max-width:860px;margin:0 auto;padding-block:28px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}}
h1,h2{{font-family:var(--display);font-weight:700;letter-spacing:.01em;text-wrap:balance;margin:0;line-height:1.1}}
h1{{font-size:2.4rem}} h2{{font-size:1.5rem}}
.lede{{color:var(--muted);margin:.4rem 0 0}}
.facts{{display:flex;flex-wrap:wrap;gap:8px 20px;color:var(--muted);font-size:.95rem}}
.facts b{{color:var(--fg);font-variant-numeric:tabular-nums}}
section{{display:grid;gap:12px;min-width:0}}
.tw{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th{{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}}
td{{padding:8px 10px;border-bottom:1px solid var(--line)}} tr:last-child td{{border-bottom:0}}
.c{{text-align:center}} .num{{white-space:nowrap}} .strong{{font-weight:600}} .muted{{color:var(--muted)}}
.team a{{color:var(--accent);font-weight:600;text-decoration:none;white-space:nowrap}} .team a:hover{{text-decoration:underline}}
.chip{{display:inline-block;min-width:2.2em;padding:1px 7px;border-radius:999px;font-size:.85rem;font-weight:600;background:var(--line);color:var(--fg);text-align:center}}
.chip.up{{background:var(--upbg);color:var(--up)}} .chip.down{{background:var(--downbg);color:var(--down)}}
tr.me td{{background:var(--me);font-weight:600}}
details{{background:var(--surface);border:1px solid var(--line);border-radius:6px}}
details+details{{margin-top:8px}}
summary{{cursor:pointer;padding:10px 12px;display:flex;flex-wrap:wrap;gap:4px 12px;align-items:baseline}}
summary:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.st{{font-family:var(--display);font-size:1.2rem;font-weight:600}} .sd{{color:var(--muted);font-size:.92rem}}
details .tw{{border:0;border-top:1px solid var(--line);border-radius:0}}
.notes{{color:var(--muted);font-size:.9rem;display:grid;gap:6px}} .notes p{{margin:0;max-width:68ch}}
</style>
<div class="wrap">
<header><h1>Classements SQY Ping</h1>
<p class="lede">Championnat de France par équipes 2026-2027, phase 1 · après la 3e journée (4 rencontres pour la N2) · données au {__import__("datetime").date.today().strftime("%d/%m/%Y")}</p></header>
<div class="facts"><span><b>{len(teams)}</b> équipes engagées</span><span><b>{leaders}</b> en tête de poule, égalités comprises</span><span><b>{unbeaten}</b> invaincues</span><span><b>{bottom}</b> dans les deux dernières places, égalités comprises</span></div>
<section><h2>Messieurs</h2><div class="tw"><table><thead><tr><th>Équipe</th><th>Division</th><th class="c">Clt</th><th class="c">Pts</th><th class="c">V-N-D</th></tr></thead><tbody>
{rows_summary(False)}
</tbody></table></div></section>
<section><h2>Dames</h2><div class="tw"><table><thead><tr><th>Équipe</th><th>Division</th><th class="c">Clt</th><th class="c">Pts</th><th class="c">V-N-D</th></tr></thead><tbody>
{rows_summary(True)}
</tbody></table></div></section>
<section><h2>Détail des poules</h2><div>
{"".join(pool_block(t) for t in teams)}
</div></section>
<section class="notes"><h2>Comment c'est calculé</h2>
<p>Scores des rencontres lus dans l'API de la FFTT (apiv2.fftt.com), qui alimente monclub.fftt.com. Points FFTT : victoire 3, nul 2, défaite 1, forfait 0.</p>
<p>Le classement est recalculé à partir de ces scores. Les équipes à égalité de points sont affichées ex æquo : la FFTT les départage par les confrontations directes, que ce récap ne recalcule pas.</p>
<p>Non inclus : le championnat des jeunes (30 poules) et l'équipe Dames 1, introuvable parmi les poules du club pour cette phase.</p>
</section>
</div>'''
open("classements-sqy-ping.html","w").write(page)
print(len(teams),leaders,unbeaten,bottom)
