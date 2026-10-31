import json,re,html,itertools,datetime
OUT=""
site=json.load(open("site.json"))
JOURS=["lun.","mar.","mer.","jeu.","ven.","sam.","dim."];MOIS=["janv.","févr.","mars","avr.","mai","juin","juil.","août","sept.","oct.","nov.","déc."]
def fd(d):
    if not d: return ""
    x=datetime.date.fromisoformat(d); return f"{JOURS[x.weekday()]} {x.day} {MOIS[x.month-1]}"
def pc(x):
    v=round(x*100); return "moins de 1 %" if x>0 and v==0 else ("plus de 99 %" if x<1 and v==100 else f"{v} %")
def nm(n): return html.escape(n)
def rank(p,tid):
    pts=sorted((v["pts"] for v in p["teams"].values()),reverse=True); return 1+sum(1 for x in pts if x>p["teams"][tid]["pts"])
def label(p,tid):
    T=p["teams"][tid]; return ("Dames " if p["fem"] else "SQY ")+re.search(r"(\d+)\s*$",T["name"]).group(1)
def ok(cb,mode): return cb[1] if mode=="u" else cb[0]-cb[2]
def cond(s,mode,fix):
    n=g=0
    for k,cb in s["combo"].items():
        if all(k[i]==r for i,r in fix.items()): n+=cb[0]; g+=ok(cb,mode)
    return (g/n if n else None),n

def fmtp(x): return f"{x:,}".replace(",","\u202f")
def plist(rows,mode="reg"):
    out=[]
    for r in rows:
        extra=""
        if mode=="reg": extra="ajouté à la main : titulaire annoncé, pas encore de feuille de match" if r.get("forced") else f'{r["inT"]}/{r["J"]} renc.'
        elif mode=="ren": extra=f'joue d\'habitude en équipe {r["main"]}'
        elif mode=="burn": extra=r["why"]
        warn=' <span class="tag hard">à 1 match du brûlage</span>' if mode=="reg" and r["lower"]==1 else ""
        out.append(f'<li><b>{nm(r["name"])}</b> · {fmtp(r["points"])} pts <span class="muted">· {extra}</span>{warn}</li>')
    return "".join(out)
def compo_block(p,tid,title,open_=False,duels=None,mine=None,mylabel=""):
    c=(p.get("compo") or {}).get(str(tid))
    if not c or not c["probable"]: return ""
    avg=round(sum(r["points"] for r in c["probable"])/len(c["probable"]))
    h=f'<details class="compo"{" open" if open_ else ""}><summary>{title} <span class="muted">· moyenne {fmtp(avg)} pts</span></summary><div class="cb">'
    h+=f'<p class="lab">Composition probable</p><ul>{plist(c["probable"])}</ul>'
    if c["bench"]: h+=f'<p class="lab">Remplaçants possibles</p><ul>{plist([r for r in c["bench"] if r["inT"]])}{plist([r for r in c["bench"] if not r["inT"]],"ren")}</ul>'
    if c["burned"]: h+=f'<p class="lab">Ne peuvent plus jouer dans cette équipe</p><ul>{plist(c["burned"],"burn")}</ul>'
    if c["alerts"]: h+='<p class="note">« À 1 match du brûlage » : ce joueur a déjà disputé 1 rencontre dans une équipe de numéro inférieur. S\'il y rejoue une fois, il ne pourra plus jouer dans cette équipe.</p>'
    if duels and mine and c["probable"]:
        th="".join(f'<th class="c">{nm(r["name"].split()[-1])}<br><span class="muted">{fmtp(r["points"])}</span></th>' for r in c["probable"])
        trs=""
        for r,row in zip(mine,duels):
            cells="".join(f'<td class="c du {"g" if v>=0.6 else "b" if v<=0.4 else ""}">{round(v*100)} %</td>' for v in row)
            trs+=f'<tr><td class="nw"><b>{nm(r["name"])}</b> <span class="muted">{fmtp(r["points"])}</span></td>{cells}</tr>'
        h+=(f'<p class="lab">Duels : chances de chaque joueur de {mylabel} contre chaque adversaire probable</p>'
            f'<div class="tw"><table class="duels"><thead><tr><th></th>{th}</tr></thead><tbody>{trs}</tbody></table></div>'
            '<p class="note">Chances d\'une partie en simple, calculées sur les points FFTT actuels avec le modèle calibré (avantage à domicile compris). Sur la feuille, chaque joueur rencontre 3 des 4 adversaires selon l\'ordre choisi par les capitaines.</p>')
    return h+"</div></details>"

def comment(p,tid,mode):
    s=p["sqy"][tid]; ms=s["matches"]; N=sum(cb[0] for cb in s["combo"].values())
    me=p["teams"][tid]; n=p["n"]; upn=p.get("upn",1); down=p["down"]
    word="le maintien" if mode=="m" else "la montée"; pron="le" if mode=="m" else "la"
    cur=(1-s["down"]) if mode=="m" else s["up"]
    rk=rank(p,tid); place=lambda r:"1er" if r==1 else f"{r}e"
    tn=lambda t:nm(p["teams"][str(t)]["name"])
    pts=sorted(((v["pts"],k) for k,v in p["teams"].items()),reverse=True)
    # --- situation
    if mode=="m":
        line=n-down; lp=pts[line-1][0]; nextp=pts[line][0]
        if rk<=line:
            gap=me["pts"]-nextp
            pos=f"au-dessus de la zone de relégation, avec {gap} pt{'s' if gap>1 else ''} d'avance sur la {place(line+1)} place" if gap>0 else f"à égalité de points avec la {place(line+1)} place, la première place relégable"
        else:
            gap=lp-me["pts"]
            pos=f"dans la zone de relégation, à {gap} pt{'s' if gap>1 else ''} de la {place(line)} place, la dernière qui sauve" if gap>0 else f"dans la zone de relégation, mais à égalité de points avec la {place(line)} place"
    else:
        lp=pts[upn-1][0]; nextp=pts[upn][0]
        lab="la 1re place" if upn==1 else "la 2e place, la dernière qui fait monter"
        if me["pts"]>=lp:
            gap=me["pts"]-nextp
            pos=(f"en position de montée, avec {gap} pt{'s' if gap>1 else ''} d'avance sur la {place(upn+1)} place" if gap>0 else f"en position de montée, mais à égalité de points avec la {place(upn+1)} place")
        else:
            gap=lp-me["pts"]; pos=f"à {gap} pt{'s' if gap>1 else ''} de {lab}"
    home=sum(1 for m in ms if m["home"])
    sit=(f"{label(p,tid)} est {place(rk)} sur {n} avec {me['pts']} pts ({me['V']} victoire{'s' if me['V']>1 else ''}, {me['N']} nul{'s' if me['N']>1 else ''}, {me['D']} défaite{'s' if me['D']>1 else ''}), {pos}. "
         f"Il reste {len(ms)} rencontre{'s' if len(ms)>1 else ''}, dont {home} à domicile.")
    # --- poids de chaque rencontre
    imp=[]
    for i,m in enumerate(ms):
        v,nv=cond(s,mode,{i:"V"}); d,nd=cond(s,mode,{i:"D"})
        imp.append(dict(i=i,v=v if nv>=100 else None,d=d if nd>=100 else None,pw=m["pwin"] if True else 0,pws=nv/N,gap=(v-d) if (nv>=100 and nd>=100) else 0))
    for x in imp: x["w"]=x["gap"]*(x["pws"]*(1-x["pws"]))**0.5
    order=sorted(imp,key=lambda x:-x["w"]); k=order[0] if order and order[0]["w"]>0 else None
    def tag(x):
        if k and x["i"]==k["i"]: return '<span class="tag key">Décisive</span>'
        if x["gap"]>=0.2 and x["w"]>=0.05: return '<span class="tag imp">Importante</span>'
        if x["pws"]>=0.65: return '<span class="tag easy">Abordable</span>'
        if x["pws"]<=0.35: return '<span class="tag hard">Difficile</span>'
        return '<span class="tag">Ouverte</span>'
    rows=[]
    for x in imp:
        m=ms[x["i"]]; o=p["teams"][str(m["opp"])]; r=rank(p,str(m["opp"]))
        f=lambda y:pc(y) if y is not None else "—"
        rows.append(f'<tr><td class="nw">J{m["round"]}<br><span class="muted">{fd(m["date"])}</span></td><td>{"Dom." if m["home"] else "Ext."} · <b>{tn(m["opp"])}</b><br><span class="muted">{place(r)}, {o["pts"]} pts</span></td>'
                    f'<td class="c nw">{pc(x["pws"])}</td><td class="c nw">{f(x["v"])}</td><td class="c nw">{f(x["d"])}</td><td>{tag(x)}</td></tr>')
    cal=(f'<div class="tw"><table class="cal"><thead><tr><th>Journée</th><th>Adversaire</th><th class="c">Chances de victoire</th><th class="c">{"Maintien" if mode=="m" else "Montée"} si victoire</th><th class="c">… si défaite</th><th>Enjeu</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    # --- scénarios
    sc=[]
    allv="V"*len(ms); cbv=s["combo"].get(allv)
    if cbv and cbv[0]>=50: sc.append(f"<li><b>Tout gagner</b> ({pc(cbv[0]/N)} de chances d'y arriver) : {word} serait à {pc(ok(cbv,mode)/cbv[0])}.</li>")
    byk=[b for b in s["byk"] if b["p"]>0.005]
    goal=(next((b for b in byk if b["up"]>=0.5),None) if mode=="u" else next((b for b in byk if b["down"]<=0.1),None))
    if goal and goal["k"]<len(ms):
        val=goal["up"] if mode=="u" else 1-goal["down"]
        sc.append(f"<li><b>L'objectif : {goal['k']} victoire{'s' if goal['k']>1 else ''} sur {len(ms)}</b> ({pc(goal['p'])} de chances de finir exactement là). {word[0].upper()+word[1:]} passerait alors à {pc(val)}.</li>")
    best=None; others=[]
    if k:
        others=[x for x in range(len(ms)) if x!=k["i"]]; target=0.8 if mode=="m" else 0.5; best=None
        for size in range(0,len(others)+1):
            cands=[]
            for S in itertools.combinations(others,size):
                pr,nn=cond(s,mode,{k["i"]:"D",**{x:"V" for x in S}})
                if pr is not None and nn>=50: cands.append((pr,S))
            if cands:
                pr,S=max(cands)
                if pr>=target: best=(pr,S); break
        loser=tn(ms[k["i"]]["opp"])
        if best and not best[1]: plan=f"pas de panique, {word} resterait à {pc(best[0])}."
        elif best:
            nms=[tn(ms[x]["opp"]) for x in best[1]]; lst=nms[0] if len(nms)==1 else ", ".join(nms[:-1])+" et "+nms[-1]
            plan=f"il faudrait alors battre {lst} pour remonter à {pc(best[0])}."
        else:
            pr,nn=cond(s,mode,{k["i"]:"D",**{x:"V" for x in others}})
            plan=(f"{word} deviendrait quasi impossible, même en gagnant tout le reste." if pr is not None and pr<0.01 else
                  f"même en gagnant toutes les autres rencontres, {word} plafonnerait à {pc(pr)} et dépendrait des autres résultats." if pr is not None else "les autres résultats deviendraient déterminants.")
        sc.append(f"<li><b>En cas de défaite contre {loser}</b> : {plan}</li>")
    zero=next((b for b in s["byk"] if b["k"]==0 and b["p"]>0.005),None)
    if zero:
        val=zero["up"] if mode=="u" else 1-zero["down"]
        sc.append(f"<li><b>Aucune victoire</b> ({pc(zero['p'])} de risque) : {word} tomberait à {pc(val)}.</li>")
    # --- matchs des autres
    watch=[]
    for o in s.get("others",[]):
        a=o["res"]["1"]; b=o["res"]["-1"]
        if a[0]<200 or b[0]<200: continue
        pa=ok(a,mode)/a[0]; pb=ok(b,mode)/b[0]; diff=pa-pb
        watch.append((abs(diff),o,pa,pb))
    watch.sort(key=lambda x:-x[0]); wl=[]
    for dlt,o,pa,pb in watch[:3]:
        if dlt<0.03: break
        fav,unf,pf,pu=(o["home"],o["away"],pa,pb) if pa>pb else (o["away"],o["home"],pb,pa)
        wl.append(f'<li>J{o["round"]}{", "+fd(o["date"]) if o["date"] else ""} · {tn(o["home"])} – {tn(o["away"])} : une victoire de <b>{tn(fav)}</b> arrange {label(p,tid)} ({word} à {pc(pf)}, contre {pc(pu)} si {tn(unf)} gagne).</li>')
    # --- verdict
    if mode=="m":
        tier=("Maintien quasi acquis" if cur>=0.9 else "Bien parti" if cur>=0.7 else "Situation incertaine" if cur>=0.4 else "Situation critique")
        cls="ok" if cur>=0.9 else "mid" if cur>=0.7 else "warn" if cur>=0.4 else "bad"
    else:
        tier=("Grand favori" if cur>=0.8 else "En bonne position" if cur>=0.5 else "Dans la course" if cur>=0.2 else "Outsider")
        cls="ok" if cur>=0.8 else "mid" if cur>=0.5 else "warn" if cur>=0.2 else "bad"
    must=k and ((k["d"] is not None and k["v"] is not None) and ((k["d"]<0.5 and k["v"]>=0.7) if mode=="m" else (k["d"]<0.15 and k["v"]>=0.4))) and (best is None or len(best[1])==len(others))
    kv=""
    if k:
        mk=ms[k["i"]]
        kv=(f" Tout se jouera surtout {'contre' if mk['home'] else 'à'} {tn(mk['opp'])} le {fd(mk['date'])} : "
            f"une victoire porterait {word} à {pc(k['v'])}, une défaite {pron} ramènerait à {pc(k['d'])}."+(" <b>Il faut absolument la gagner.</b>" if must else ""))
    verdict=f'<p class="verdict"><span class="pill {cls}">{tier}</span> {word[0].upper()+word[1:]} à <b>{pc(cur)}</b>.{kv}</p>'
    own=compo_block(p,tid,f"Notre composition probable ({label(p,tid)})")
    myc=(p.get("compo") or {}).get(str(tid)) or {}
    opps="".join(compo_block(p,m["opp"],f'J{m["round"]} · {tn(m["opp"])}',duels=m.get("duels"),mine=myc.get("probable"),mylabel=label(p,tid)) for m in ms)
    html_=verdict+f"<h4>La situation</h4><p>{sit}</p>{own}<h4>Les rencontres restantes</h4>{cal}"
    if opps: html_+=f"<h4>Les compositions adverses probables</h4><div class=\"compos\">{opps}</div>"
    if sc: html_+="<h4>Les scénarios</h4><ul>"+"".join(sc)+"</ul>"
    if wl: html_+="<h4>À surveiller chez les autres</h4><ul>"+"".join(wl)+"</ul>"
    return html_
def section(mode):
    items=[];calm=[]
    for p in site:
        for tid,s in p["sqy"].items():
            num=int(re.search(r"(\d+)\s*$",p["teams"][tid]["name"]).group(1))
            open_=(s["down"]>=0.03) if mode=="m" else (0.03<=s["up"]<=0.97)
            items.append((p["fem"],num,p,tid,open_))
    items.sort(key=lambda x:(x[0],x[1]))
    blocks=[];calm=[]
    for fem,num,p,tid,open_ in items:
        if open_:
            cur=(1-p["sqy"][tid]["down"]) if mode=="m" else p["sqy"][tid]["up"]
            blocks.append(f'<article class="pt"><h3>{label(p,tid)} <span class="muted">· {html.escape(p["division"])} · poule {p["pool"]}</span></h3>{comment(p,tid,mode)}</article>')
        else: calm.append(label(p,tid))
    calmtxt=("<p class=\"muted\">Pas d'enjeu pour " if mode=="m" else "<p class=\"muted\">Montée déjà quasi acquise ou hors de portée pour ")+", ".join(calm)+".</p>" if calm else ""
    title="Le point équipe par équipe"
    return f'<section><h2>{title}</h2><div class="pts">{"".join(blocks)}</div>{calmtxt}</section>'
CSS=""":root{--warn:#94570a;--warnbg:#fbf0dc;--down:#b3372b;--downbg:#fbe7e4}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--warn:#f0b65e;--warnbg:#3a2a12;--down:#f19a8f;--downbg:#3d1e1b}}
:root[data-theme="dark"]{--warn:#f0b65e;--warnbg:#3a2a12;--down:#f19a8f;--downbg:#3d1e1b}
.pts{display:grid;gap:14px} .pt{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:14px 16px 16px;display:grid;gap:8px;min-width:0}
.pt h3{font-family:var(--display);font-size:1.45rem;font-weight:700;margin:0} .pt h3 .muted{font-family:var(--body);font-size:.95rem;font-weight:400}
.pt h4{font-size:.76rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted);margin:8px 0 0;font-weight:600}
.pt p{margin:0;max-width:75ch} .pt ul{margin:0;padding-left:1.2em;display:grid;gap:6px;max-width:75ch}
.verdict{font-size:1.05rem;line-height:1.55}
.pill{display:inline-block;padding:2px 10px;border-radius:999px;font-size:.85rem;font-weight:600;margin-right:4px;vertical-align:1px}
.pill.ok{background:var(--upbg);color:var(--up)} .pill.mid{background:var(--line);color:var(--fg)} .pill.warn{background:var(--warnbg);color:var(--warn)} .pill.bad{background:var(--downbg);color:var(--down)}
.pt .tw{background:var(--bg)} .cal td{vertical-align:top;font-size:.95rem} .cal th{white-space:normal}
.tag{display:inline-block;padding:1px 8px;border-radius:4px;font-size:.78rem;font-weight:600;background:var(--line);white-space:nowrap}
.compos{display:grid;gap:6px} .compo{border:1px solid var(--line);border-radius:6px;background:var(--bg)}
.compo summary{cursor:pointer;padding:8px 10px;font-weight:600} .compo summary:focus-visible{outline:2px solid var(--up);outline-offset:2px}
.cb{padding:0 12px 10px;display:grid;gap:4px} .cb .lab{font-size:.74rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);margin:6px 0 0}
.cb ul{list-style:none;padding:0;gap:3px} .duels td,.duels th{padding:5px 7px;font-size:.88rem} .du.g{background:var(--upbg);color:var(--up);font-weight:600} .du.b{background:var(--downbg);color:var(--down);font-weight:600} .cb .note{font-size:.88rem;color:var(--muted)}
.tag.key{background:var(--fg);color:var(--surface)} .tag.imp{background:var(--warnbg);color:var(--warn)} .tag.easy{background:var(--upbg);color:var(--up)} .tag.hard{background:var(--downbg);color:var(--down)}
</style>"""
for f,mode in (("montees-sqy-ping.html","u"),("maintien-sqy-ping.html","m")):
    h=open(OUT+f).read()
    h=re.sub(r'<section><h2>Le point équipe par équipe</h2>.*?</section>','',h,flags=re.S)
    h=re.sub(r":root\{--warn:.*?</style>","</style>",h,count=1,flags=re.S) if "--warn:" in h else re.sub(r"\.pts\{.*?</style>","</style>",h,count=1,flags=re.S)
    h=h.replace("</style>",CSS,1)
    h=h.replace('<section class="notes">',section(mode)+'<section class="notes">',1)
    open(OUT+f,"w").write(h)
print("ok")
