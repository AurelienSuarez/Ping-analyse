import json,os,glob,random,re,datetime,collections,urllib.request,time
CACHE="cache"; TODAY=datetime.date.today().isoformat()
def g(p):
    f=os.path.join(CACHE,p.replace("/","_").replace("?","_")[:200]+".json")
    if os.path.exists(f): return json.load(open(f))
    r=urllib.request.Request("https://apiv2.fftt.com"+p,headers={"Accept":"application/ld+json"})
    d=json.load(urllib.request.urlopen(r,timeout=90)); time.sleep(0.15)
    json.dump(d,open(f,"w")); return d
pools=json.load(open("sqy_pools.json"))["hydra:member"]
def lvl(d):
    d=d.replace("FED_","").replace("L08_","").replace("D78_","")
    d=re.sub(r"\s*[Pp]hase 1","",d).replace("Pre-Regionale","Pré-Régionale").replace("Departementale","Départementale").replace("R1","Régionale 1")
    return d.strip()
out=[]
for pl in pools:
    lst=g(f"/api/sport_matches?pool.id={pl['id']}&itemsPerPage=100")["hydra:member"]
    if not lst: continue
    div=lst[0]["division"]; contest=div["contest"]["name"]
    if "quipes" not in contest: continue
    fem="Féminin" in contest
    pd=g(f"/api/pools/{pl['id']}")
    nopp=(pd.get("playerOppositionSheet") or {}).get("oppositionCount") or 14
    nplay=(pd.get("playerOppositionSheet") or {}).get("opponentCount") or 4
    teams={}
    for m in lst:
        for s in ("homeOpponent","awayOpponent"):
            t=((m.get(s) or {}).get("team")) or {}
            if t: teams[t["id"]]=t["name"]
    played=[];future=[]
    players=collections.defaultdict(dict)  # team -> licence -> info
    for m in lst:
        h=((m.get("homeOpponent") or {}).get("team") or {}).get("id"); a=((m.get("awayOpponent") or {}).get("team") or {}).get("id")
        if not h or not a: continue
        base=dict(id=m["id"],date=(m.get("date") or "")[:10],round=m.get("roundNumber"),home=h,away=a)
        f=os.path.join(CACHE,m["@id"].replace("/","_")+".json")
        d=json.load(open(f)) if os.path.exists(f) else None
        if d and (d.get("homePoints") is not None or d.get("winner")):
            base.update(hp=d.get("homePoints") or 0,ap=d.get("awayPoints") or 0,hg=d.get("homeGamePoints") or 0,ag=d.get("awayGamePoints") or 0,winner=d.get("winner"),draw=bool(d.get("draw")),forfeit=bool(d.get("forfeit")))
            lineup={}
            for side,sheet in ((h,"homeSheetMatches"),(a,"awaySheetMatches")):
                pts=[]
                for sp in d.get(sheet) or []:
                    p=sp.get("player")
                    if not p: continue
                    per=p.get("person") or {}
                    lic=p["identifier"]; info=players[side].setdefault(lic,dict(name=f'{per.get("givenName","")} {per.get("familyName","")}'.strip(),points=p.get("points") or 0,n=0,last=""))
                    info["n"]+=1; info["last"]=max(info["last"],base["date"]); info["points"]=p.get("points") or info["points"]
                    pts.append(p.get("points") or 0)
                lineup[side]=pts
            base["lineup"]=lineup
            played.append(base)
        else: future.append(base)
    out.append(dict(pool=pl["id"],poolName=pl["name"],division=lvl(div["name"]),fem=fem,nopp=nopp,nplay=nplay,teams=teams,played=played,future=future,players={k:v for k,v in players.items()}))
    print(lvl(div["name"]),pl["name"],len(played),len(future),nopp,nplay)
json.dump(out,open("site_raw.json","w"),ensure_ascii=False)
