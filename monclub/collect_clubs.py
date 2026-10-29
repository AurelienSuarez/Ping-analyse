import json,glob,os,time,urllib.request,collections,datetime,sys,re
from concurrent.futures import ThreadPoolExecutor
CACHE="cache"; TODAY=datetime.date.today().isoformat()
def g(p):
    f=os.path.join(CACHE,p.replace("/","_").replace("?","_")[:200]+".json")
    if os.path.exists(f): return json.load(open(f))
    r=urllib.request.Request("https://apiv2.fftt.com"+p,headers={"Accept":"application/ld+json"})
    for i in range(4):
        try: d=json.load(urllib.request.urlopen(r,timeout=90)); break
        except Exception as e:
            if i==3: raise
            time.sleep(5*(i+1))
    time.sleep(0.15); json.dump(d,open(f,"w")); return d
def num(name):
    m=re.findall(r"(\d+)",name or ""); return int(m[-1]) if m else 99
# numéro max utile par club et par genre : équipe présente dans une poule SQY, +1 pour les renforts
need=collections.defaultdict(int)
for p in json.load(open("sqy_pools.json"))["hydra:member"]:
    f=f"cache/_api_sport_matches_pool.id={p['id']}&itemsPerPage=100.json"
    if not os.path.exists(f): continue
    for m in json.load(open(f))["hydra:member"]:
        c=m["division"]["contest"]["name"]
        if "quipes" not in c: continue
        gnd="F" if "Féminin" in c else "M"
        for sd in ("homeOpponent","awayOpponent"):
            t=((m.get(sd) or {}).get("team")) or {}
            for cl in t.get("clubs",[]): need[(cl["id"],gnd)]=max(need[(cl["id"],gnd)],num(t["name"])+1)
clubs=sorted({c for c,_ in need})
# appearances[club][contestGender][licence] = list of (date, round, teamPosition, teamId, poolId)
out={}
def work(args):
    ci,cid=args
    pools=g(f"/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=100&poolOpponents.opponent.team.clubs.id={cid}")["hydra:member"]
    rec={"teams":{},"apps":[]}
    for pl in pools:
        lst=g(f"/api/sport_matches?pool.id={pl['id']}&itemsPerPage=100")["hydra:member"]
        if not lst: continue
        contest=lst[0]["division"]["contest"]["name"]
        if "quipes" not in contest: continue
        gender="F" if "Féminin" in contest else "M"
        for m in lst:
            for side in ("homeOpponent","awayOpponent"):
                t=((m.get(side) or {}).get("team")) or {}
                if any(c["id"]==cid for c in t.get("clubs",[])):
                    rec["teams"][t["id"]]=dict(name=t["name"],gender=gender,pool=pl["id"],division=lst[0]["division"]["name"])
            if (m.get("date") or "9")[:10]>TODAY: continue
            mine=[s for s in ("homeOpponent","awayOpponent") if any(c["id"]==cid for c in ((((m.get(s) or {}).get("team")) or {}).get("clubs",[])))
                  and num((((m.get(s) or {}).get("team")) or {}).get("name"))<=need.get((cid,gender),0)]
            if not mine: continue
            d=g(m["@id"])
            for side in mine:
                t=d[side]["team"]; sheet="homeSheetMatches" if side=="homeOpponent" else "awaySheetMatches"
                for sp in d.get(sheet) or []:
                    p=sp.get("player")
                    if not p: continue
                    per=p.get("person") or {}
                    rec["apps"].append(dict(lic=p["identifier"],name=f'{per.get("givenName","")} {per.get("familyName","")}'.strip(),
                        points=p.get("points") or 0,date=(d.get("date") or "")[:10],round=d.get("roundNumber"),team=t["id"],gender=gender,pool=pl["id"]))
    return cid,rec

with ThreadPoolExecutor(3) as ex:
    for cid,rec in ex.map(work,list(enumerate(clubs))):
        out[cid]=rec
        print(f"club {cid}: {len(rec['teams'])} équipes, {len(rec['apps'])} participations",flush=True)
json.dump(out,open("clubs_apps.json","w"),ensure_ascii=False)
print("FINI")
