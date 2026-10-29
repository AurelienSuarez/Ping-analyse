import json,collections
data=json.load(open("sqy_data.json"))
others=collections.Counter(e["contest"]+" | "+(e["division"] or "") for e in data if not e["matches"] and "quipes" not in e["contest"])
res=[]
for e in data:
    if "quipes" not in e["contest"]: continue
    st={int(tid):dict(name=n,J=0,V=0,N=0,D=0,F=0,pts=0,gp=0,gc=0) for tid,n in e["teams"].items()}
    pending=0; last=0
    for m in e["matches"]:
        if m["home"] is None or m["away"] is None: continue
        if m["homePoints"] is None and m["winner"] is None and not m["draw"]: pending+=1; continue
        last=max(last,m["roundNumber"] or 0)
        for me,op,side in ((m["home"],m["away"],"home"),(m["away"],m["home"],"away")):
            s=st[me]; o="away" if side=="home" else "home"
            s["J"]+=1; s["pts"]+=m[side+"Points"] or 0
            s["gp"]+=m[side+"GamePoints"] or 0; s["gc"]+=m[o+"GamePoints"] or 0
            if m["draw"]: s["N"]+=1
            elif m["winner"]==side: s["V"]+=1
            else:
                s["D"]+=1
                if m["forfeit"] or m["penalty"]: s["F"]+=1
    rows=sorted(st.values(),key=lambda s:(-s["pts"],-(s["gp"]-s["gc"]),s["name"]))
    res.append(dict(division=e["division"],contest=e["contest"],pool=e["poolName"],round=last,pending=pending,rows=rows))
json.dump(res,open("standings.json","w"),ensure_ascii=False)
for r in res:
    sq=[(i+1,x["name"],x["pts"],x["V"],x["N"],x["D"]) for i,x in enumerate(r["rows"]) if "SQY" in x["name"].upper()]
    print(f'{r["division"]:<38} P{r["pool"]:<3} J{r["round"]} pend={r["pending"]} n={len(r["rows"])}', sq)
print("\nAutres compétitions (non traitées):"); [print(" ",k,v) for k,v in others.items()]
