import json,os,time,datetime
import fftt_api
CACHE="cache"
def g(p,cache=True):
    f=os.path.join(CACHE,p.replace("/","_").replace("?","_")[:200]+".json")
    if cache and os.path.exists(f): return json.load(open(f))
    d=fftt_api.get(p,retries=2)
    time.sleep(0.15)
    if cache: json.dump(d,open(f,"w"))
    return d
pools=json.load(open("sqy_pools.json"))["hydra:member"]
today=datetime.date.today().isoformat()
out=[]
for pl in pools:
    ms=g(f"/api/sport_matches?pool.id={pl['id']}&itemsPerPage=100")["hydra:member"]
    if not ms: continue
    div=ms[0]["division"]; 
    contest=div.get("contest",{}).get("name","")
    entry={"pool":pl["id"],"poolName":pl.get("name"),"division":div.get("name"),"contest":contest,"teams":{},"matches":[]}
    for m in ms:
        for side in ("homeOpponent","awayOpponent"):
            t=(m.get(side) or {}).get("team") or {}
            if t: entry["teams"][t["id"]]=t["name"]
    if "Equipes" not in contest and "équipes" not in contest.lower():
        out.append(entry); continue
    for m in ms:
        if m.get("date","9")[:10] > today: continue
        d=g(m["@id"])
        h=((d.get("homeOpponent") or {}).get("team") or {}).get("id"); a=((d.get("awayOpponent") or {}).get("team") or {}).get("id")
        entry["matches"].append({k:d.get(k) for k in ("date","roundNumber","homePoints","awayPoints","homeGamePoints","awayGamePoints","winner","draw","forfeit","penalty","abandonment")}|{"home":h,"away":a})
    out.append(entry)
    print(len(out), contest, "|", div.get("name"), "| matches:", len(entry["matches"]), flush=True)
json.dump(out,open("sqy_data.json","w"),ensure_ascii=False,indent=1)
