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
def comment(p,tid,mode):
    s=p["sqy"][tid]; ms=s["matches"]; N=sum(cb[0] for cb in s["combo"].values())
    me=p["teams"][tid]; n=p["n"]; word="le maintien" if mode=="m" else "la montée"
    cur=(1-s["down"]) if mode=="m" else s["up"]
    def oppdesc(m):
        o=p["teams"][str(m["opp"])]; r=rank(p,str(m["opp"]))
        tag=""
        if mode=="m" and r>=n-3 and abs(o["pts"]-me["pts"])<=2: tag=", rival direct pour le maintien"
        if mode=="u" and (r<=p["upn"]+1 or o["pts"]>=me["pts"]) : tag=", concurrent direct pour la 1re place" if p["upn"]==1 else ", concurrent direct pour les 2 places de montée"
        return f'{"contre" if m["home"] else "à"} <b>{nm(o["name"])}</b> (J{m["round"]}{", "+fd(m["date"]) if m["date"] else ""} ; {"1er" if r==1 else str(r)+"e"}, {o["pts"]} pts{tag})'
    def short(i): return nm(p["teams"][str(ms[i]["opp"])]["name"])
    imp=[]
    for i,m in enumerate(ms):
        v,nv=cond(s,mode,{i:"V"}); d,nd=cond(s,mode,{i:"D"})
        if v is None or d is None or nv<100 or nd<100: continue
        imp.append(dict(i=i,v=v,d=d,pw=nv/N,gap=v-d))
    if not imp: return f"<p>Plus grand-chose ne dépend des résultats de l'équipe : {word} est à {pc(cur)}.</p>"
    # poids réel : écart victoire/défaite pondéré par l incertitude de la rencontre
    imp.sort(key=lambda x:-x["gap"]*(x["pw"]*(1-x["pw"]))**0.5); k=imp[0]; out=[]
    others=[x for x in range(len(ms)) if x!=k["i"]]
    target=0.8 if mode=="m" else 0.5
    best=None
    for size in range(0,len(others)+1):
        cands=[]
        for S in itertools.combinations(others,size):
            fix={k["i"]:"D",**{x:"V" for x in S}}; pr,nn=cond(s,mode,fix)
            if pr is not None and nn>=50: cands.append((pr,S))
        if cands:
            pr,S=max(cands)
            if pr>=target: best=(pr,S); break
            last=(pr,S)
    loser=short(k["i"]); pron="le" if mode=="m" else "la"
    must=((k["d"]<0.5 and k["v"]>=0.7) if mode=="m" else (k["d"]<0.15 and k["v"]>=0.4)) and (best is None or len(best[1])==len(others))
    out.append(f'{"<b>Il faut absolument gagner</b> " if must else "La rencontre décisive se joue "}{oppdesc(ms[k["i"]])}. '
               f'Une victoire porte {word} à {pc(k["v"])}, une défaite {pron} ramène à {pc(k["d"])}'
               f' (chances de victoire estimées : {pc(k["pw"])}).')
    if best and not best[1]:
        out.append(f"Même une défaite contre {loser} ne serait pas rédhibitoire ({word} resterait à {pc(best[0])}).")
    elif best:
        names=[short(x) for x in best[1]]; lst=names[0] if len(names)==1 else ", ".join(names[:-1])+" et "+names[-1]
        out.append(f"En cas de défaite contre {loser}, il faudra battre {lst} : {word} serait alors à {pc(best[0])}.")
    else:
        allw={k["i"]:"D",**{x:"V" for x in others}}; pr,nn=cond(s,mode,allw)
        if pr is not None:
            if pr<0.01: out.append(f"En cas de défaite contre {loser}, {word} deviendrait quasi impossible, même en gagnant toutes les autres rencontres.")
            elif pr>=0.5: out.append(f"En cas de défaite contre {loser}, il faudrait gagner toutes les autres rencontres pour remonter à {pc(pr)}, et {word} dépendrait aussi des résultats des autres équipes.")
            else: out.append(f"En cas de défaite contre {loser}, même en gagnant toutes les autres rencontres, {word} ne serait qu'à {pc(pr)} et dépendrait surtout des résultats des autres équipes.")
    if len(imp)>1 and imp[1]["gap"]>=0.2:
        x=imp[1]; out.append(f"Autre rencontre qui pèse lourd : {oppdesc(ms[x['i']])}, avec {pc(x['v'])} en cas de victoire contre {pc(x['d'])} en cas de défaite.")
    easy=max(imp,key=lambda x:x["pw"])
    if easy["i"] not in (k["i"],imp[1]["i"] if len(imp)>1 and imp[1]["gap"]>=0.2 else -1) and easy["pw"]>=0.6:
        out.append(f"La rencontre la plus abordable sur le papier est {oppdesc(ms[easy['i']])}, avec {pc(easy['pw'])} de chances de victoire : à ne pas laisser filer.")
    hard=min(imp,key=lambda x:x["pw"])
    if hard["pw"]<=0.3 and hard["i"]!=k["i"]:
        out.append(f"La rencontre {oppdesc(ms[hard['i']])} s'annonce la plus difficile, avec {pc(hard['pw'])} de chances de victoire : un bon résultat y serait un bonus.")
    return "<p>"+" ".join(out)+"</p>"
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
            blocks.append(f'<article class="pt"><h3>{label(p,tid)} <span class="muted">· {html.escape(p["division"])} · {"maintien" if mode=="m" else "montée"} {pc(cur)}</span></h3>{comment(p,tid,mode)}</article>')
        else: calm.append(label(p,tid))
    calmtxt=("<p class=\"muted\">Pas d'enjeu pour " if mode=="m" else "<p class=\"muted\">Montée déjà quasi acquise ou hors de portée pour ")+", ".join(calm)+".</p>" if calm else ""
    title="Le point équipe par équipe"
    return f'<section><h2>{title}</h2><div class="pts">{"".join(blocks)}</div>{calmtxt}</section>'
CSS=".pts{display:grid;gap:10px} .pt{background:var(--surface);border:1px solid var(--line);border-radius:6px;padding:12px 14px} .pt h3{font-family:var(--display);font-size:1.2rem;font-weight:600;margin:0 0 4px} .pt h3 .muted{font-family:var(--body);font-size:.9rem;font-weight:400} .pt p{margin:0;max-width:75ch}</style>"
for f,mode in (("montees-sqy-ping.html","u"),("maintien-sqy-ping.html","m")):
    h=open(OUT+f).read()
    h=re.sub(r'<section><h2>Le point équipe par équipe</h2>.*?</section>','',h,flags=re.S)
    if ".pts{" not in h: h=h.replace("</style>",CSS,1)
    h=h.replace('<section class="notes">',section(mode)+'<section class="notes">',1)
    open(OUT+f,"w").write(h)
print("ok")
