import json,random,re,statistics,collections
raw=json.load(open("site_raw.json"))
D=300; N=20000; random.seed(7)
def pwin(a,b): return 1/(1+10**((b-a)/D))
site=[]
for P in raw:
    teams={int(k):v for k,v in P["teams"].items()}
    k=P["nplay"]
    # force d'une équipe : moyenne des k meilleurs joueurs alignés, sur ses rencontres
    lin=collections.defaultdict(list)
    for m in P["played"]:
        for side,pts in m.get("lineup",{}).items():
            pts=sorted(pts,reverse=True)[:k]
            if pts: lin[int(side)].append(sum(pts)/len(pts))
    allv=[v for l in lin.values() for v in l] or [1000]
    strength={t:(statistics.mean(lin[t]) if lin[t] else statistics.mean(allv)) for t in teams}
    base={t:dict(pts=0,J=0,V=0,N=0,D=0) for t in teams}
    for m in P["played"]:
        for me,side,o in ((m["home"],"h","a"),(m["away"],"a","h")):
            b=base[me]; b["J"]+=1; b["pts"]+=m[side+"p"]
            if m["draw"]: b["N"]+=1
            elif m["winner"]==("home" if side=="h" else "away"): b["V"]+=1
            else: b["D"]+=1
    n=len(teams); down=2
    sqys=[t for t in teams if "SQY" in teams[t].upper()]
    fut=P["future"]
    def play(h,a,S):
        pw=pwin(S[h],S[a]); pd=0.15*(1-abs(2*pw-1)) if P["nopp"]%2==0 else 0
        r=random.random()
        if r<pw-pd/2: return 3,1,1
        if r<pw+pd/2: return 2,2,0
        return 1,3,-1
    res={t:dict(up=0,down=0,ranks=collections.Counter(),byk=collections.defaultdict(lambda:[0,0,0])) for t in sqys}
    for _ in range(N):
        pts={t:base[t]["pts"] for t in teams}; wins=collections.Counter()
        S={t:strength[t]+random.gauss(0,80) for t in teams}
        for m in fut:
            hp,ap,r=play(m["home"],m["away"],S); pts[m["home"]]+=hp; pts[m["away"]]+=ap
            if r==1: wins[m["home"]]+=1
            elif r==-1: wins[m["away"]]+=1
        order=sorted(teams,key=lambda t:(-pts[t],random.random()))
        for t in sqys:
            rk=order.index(t)+1; R=res[t]; R["ranks"][rk]+=1
            u=rk==1; d=rk>n-down
            R["up"]+=u; R["down"]+=d
            bk=R["byk"][wins[t]]; bk[0]+=1; bk[1]+=u; bk[2]+=d
    pool=dict(pool=P["poolName"],division=P["division"],fem=P["fem"],n=n,down=down,nopp=P["nopp"],
        teams={t:dict(name=teams[t],strength=round(strength[t]),**base[t]) for t in teams},
        played=[{k:m[k] for k in ("date","round","home","away","hp","ap","winner","draw","forfeit")} for m in P["played"]],
        future=[{k:m[k] for k in ("date","round","home","away")} for m in fut],
        players={int(t):sorted(v.values(),key=lambda x:(-x["n"],-x["points"])) for t,v in P["players"].items()},
        sqy={})
    for t in sqys:
        R=res[t]; nf=sum(1 for m in fut if t in (m["home"],m["away"]))
        pool["sqy"][t]=dict(up=R["up"]/N,down=R["down"]/N,remaining=nf,
            ranks={r:c/N for r,c in sorted(R["ranks"].items())},
            byk=[dict(k=k,p=v[0]/N,up=v[1]/v[0],down=v[2]/v[0]) for k,v in sorted(R["byk"].items())],
            matches=[dict(opp=(m["away"] if m["home"]==t else m["home"]),home=m["home"]==t,date=m["date"],round=m["round"],
                pwin=round(pwin(strength[t],strength[m["away"] if m["home"]==t else m["home"]]),3)) for m in fut if t in (m["home"],m["away"])])
        print(f'{teams[t]:<14}{P["division"]:<26} up {R["up"]/N:5.0%} down {R["down"]/N:5.0%} restant {nf}')
    site.append(pool)
json.dump(site,open("site.json","w"),ensure_ascii=False)
