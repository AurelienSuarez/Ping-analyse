import json,re,html,datetime
site=json.load(open("site.json"))
rows=[]
for p in site:
    pts=sorted((v["pts"] for v in p["teams"].values()),reverse=True)
    for tid,s in p["sqy"].items():
        T=p["teams"][tid]; num=int(re.search(r"(\d+)\s*$",T["name"]).group(1))
        rank=1+sum(1 for x in pts if x>T["pts"]); tie=pts.count(T["pts"])>1
        rows.append(dict(p=p,s=s,T=T,num=num,fem=p["fem"],rank=rank,tie=tie,leader=pts[0]))
def pc(x):
    v=round(x*100); return "&lt;1 %" if x>0 and v==0 else (">99 %" if x<1 and v==100 else f"{v} %")
def need(s):
    k=next((b for b in s["byk"] if b["up"]>=0.5 and b["p"]>0.005),None)
    if s["up"]<0.02: return '<span class="muted">Hors de portée</span>'
    if not k: return '<span class="muted">Dépend des autres résultats</span>'
    return f'{k["k"]} victoire{"s" if k["k"]>1 else ""} sur {s["remaining"]} <span class="muted">→ {pc(k["up"])}</span>'
def bar(x): return f'<div class="bar" role="img" aria-label="{pc(x)}"><span style="width:{x*100:.1f}%"></span></div>'
def table(fem):
    rs=sorted([r for r in rows if r["fem"]==fem],key=lambda r:r["num"])
    out=[]
    for r in rs:
        lab=("1er" if r["rank"]==1 else f'{r["rank"]}e')+(" ex æquo" if r["tie"] else "")
        cls=" up" if r["rank"]==1 else ""
        gap="" if r["T"]["pts"]==r["leader"] else f' <span class="muted">(−{r["leader"]-r["T"]["pts"]})</span>'
        out.append(f'<tr><td class="strong nw">{"Dames" if fem else "SQY"} {r["num"]}</td><td>{html.escape(r["p"]["division"])} <span class="muted">· p.{r["p"]["pool"]}</span></td><td class="c nw"><span class="chip{cls}">{lab}</span>{gap}</td><td class="pcol"><div class="pv"><span class="pct">{pc(r["s"]["up"])}</span>{bar(r["s"]["up"])}</div></td><td>{need(r["s"])}</td></tr>')
    return "\n".join(out)
fav=sum(1 for r in rows if r["s"]["up"]>=0.5); course=sum(1 for r in rows if 0.1<=r["s"]["up"]<0.5)
today=datetime.date.today().strftime("%d/%m/%Y")
head='<thead><tr><th>Équipe</th><th>Division</th><th class="c">Clt (retard)</th><th>Montée</th><th>Pour monter</th></tr></thead>'
page=f'''<title>Montées SQY Ping</title>
<meta name="claude:viewport-fit-sides" content="cover">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=Source+Sans+3:wght@400;600&display=swap">
<style>
/* Layout: une colonne ; équipes triées par numéro, la barre verte porte l'information */
:root{{--bg:#f6f7f9;--surface:#ffffff;--fg:#17202b;--muted:#5d6876;--line:#dde2e8;--up:#1f7a4d;--upbg:#e3f4ea;--track:#e6eaef;
--display:"Barlow Condensed","Arial Narrow",sans-serif;--body:"Source Sans 3","Segoe UI",system-ui,sans-serif}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#11161d;--surface:#18202a;--fg:#e7ecf2;--muted:#9aa6b4;--line:#2a3542;--up:#6fd3a0;--upbg:#173528;--track:#253140;color-scheme:dark}}}}
:root[data-theme="dark"]{{--bg:#11161d;--surface:#18202a;--fg:#e7ecf2;--muted:#9aa6b4;--line:#2a3542;--up:#6fd3a0;--upbg:#173528;--track:#253140;color-scheme:dark}}
body{{background:var(--bg);color:var(--fg);font:16px/1.5 var(--body)}}
.wrap{{max-width:900px;margin:0 auto;padding-block:28px 48px;padding-left:max(16px,env(safe-area-inset-left,0px));padding-right:max(16px,env(safe-area-inset-right,0px));display:grid;gap:28px}}
h1,h2{{font-family:var(--display);font-weight:700;text-wrap:balance;margin:0;line-height:1.1}} h1{{font-size:2.4rem}} h2{{font-size:1.5rem}}
.lede{{color:var(--muted);margin:.4rem 0 0}}
.facts{{display:flex;flex-wrap:wrap;gap:8px 20px;color:var(--muted)}} .facts b{{color:var(--fg)}}
section{{display:grid;gap:12px;min-width:0}}
.tw{{overflow-x:auto;background:var(--surface);border:1px solid var(--line);border-radius:6px}}
table{{border-collapse:collapse;width:100%;font-variant-numeric:tabular-nums}}
th{{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:600;text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);white-space:nowrap}}
td{{padding:8px 10px;border-bottom:1px solid var(--line)}} tr:last-child td{{border-bottom:0}}
.c{{text-align:center}} .nw{{white-space:nowrap}} .muted{{color:var(--muted)}} .strong{{font-weight:600}}
.chip{{display:inline-block;padding:1px 8px;border-radius:999px;font-size:.84rem;font-weight:600;background:var(--line);white-space:nowrap}} .chip.up{{background:var(--upbg);color:var(--up)}}
.pcol{{min-width:150px}} .pv{{display:flex;align-items:center;gap:8px}}
.pct{{font-weight:600;min-width:3.4em;text-align:right;color:var(--up)}}
.bar{{flex:1;height:8px;border-radius:4px;background:var(--track);overflow:hidden}} .bar span{{display:block;height:100%;background:var(--up)}}
.notes{{color:var(--muted);font-size:.9rem}} .notes p{{margin:0;max-width:70ch}}
</style>
<div class="wrap">
<header><h1>Qui peut monter à SQY Ping ?</h1>
<p class="lede">Équipes seniors · championnat par équipes 2026-2027, phase 1 · après 3 journées sur 7 · données du {today}</p></header>
<div class="facts"><span><b>{fav}</b> équipes favorites pour la montée (50 % ou plus)</span><span><b>{course}</b> encore dans la course (10 à 50 %)</span></div>
<section><h2>Messieurs</h2><div class="tw"><table>{head}<tbody>{table(False)}</tbody></table></div></section>
<section><h2>Dames</h2><div class="tw"><table>{head}<tbody>{table(True)}</tbody></table></div></section>
<section class="notes"><h2>Comment c'est calculé</h2>
<p>Hypothèse : seul le 1er de la poule monte. Le nombre réel de montées dépend du règlement de chaque échelon ; à vérifier auprès de la ligue ou du comité.</p>
<p>20 000 simulations des rencontres restantes. Les chances de chaque rencontre viennent de l'écart de force entre les équipes (moyenne des points des joueurs déjà alignés), avec un aléa sur la composition. « Pour monter » donne le nombre de victoires à partir duquel la montée devient plus probable qu'improbable.</p>
<p>Source : résultats et feuilles de match de l'API FFTT qui alimente monclub.fftt.com. Ce sont des estimations.</p></section>
</div>'''
open("montees-sqy-ping.html","w").write(page)
print(fav,course)
