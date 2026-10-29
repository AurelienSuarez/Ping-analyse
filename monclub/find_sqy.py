import json,urllib.request,urllib.parse
def g(p):
    r=urllib.request.Request("https://apiv2.fftt.com"+p,headers={"Accept":"application/ld+json"})
    return json.load(urllib.request.urlopen(r,timeout=90))
base="/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=1&"
d=g(base+"poolOpponents.opponent.team.clubs.id=12920018"); print("test malakoff",d["hydra:totalItems"])
found={}
for start in range(0,2000,100):
    q="&".join(f"poolOpponents.opponent.team.clubs.id[]={12780000+i}" for i in range(start,start+100))
    d=g("/api/pools?group.tour.division.contest.season.current=true&itemsPerPage=30&"+q)
    for m in d["hydra:member"]:
        p=g(m["@id"])
        for po in p.get("poolOpponents",[]):
            for c in ((po.get("opponent") or {}).get("team") or {}).get("clubs",[]):
                if "SQY" in c["name"].upper() or "QUENTIN" in c["name"].upper():
                    found[c["identifier"]]=(c["id"],c["name"])
    if found: break
print(found)
