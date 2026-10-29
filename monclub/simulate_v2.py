import json,random,re,statistics,collections
import lineup
raw=json.load(open("site_raw.json"))
PLAYERS,TEAMS=lineup.build(json.load(open("clubs_apps.json")))
D=300; N=20000; random.seed(7)
def pwin(a,b): return 1/(1+10**((b-a)/D))
site=[]; DIFF=[]
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
    old_strength={t:(statistics.mean(lin[t]) if lin[t] else statistics.mean(allv)) for t in teams}
    # force = composition habituelle : les k joueurs les plus souvent alignés (à égalité, les mieux classés)
    strength={}
    for t in teams:
        pl=sorted((P["players"].get(str(t)) or {}).values(),key=lambda x:(-x["n"],-x["points"]))[:k]
        strength[t]=statistics.mean([x["points"] for x in pl]) if len(pl)==k else old_strength[t]
    # compositions possibles selon le brûlage ; la force devient celle de la composition probable
    compo={t:lineup.candidates(t,PLAYERS,TEAMS,k) for t in teams}
    for t in teams:
        c=compo[t]
        if c and len(c["probable"])==k:
            new=statistics.mean(r["points"] for r in c["probable"])
            if "SQY" in teams[t].upper() or abs(new-strength[t])>=60: DIFF.append((P["division"],teams[t],round(strength[t]),round(new)))
            strength[t]=new
    base={t:dict(pts=0,J=0,V=0,N=0,D=0) for t in teams}
    for m in P["played"]:
        for me,side,o in ((m["home"],"h","a"),(m["away"],"a","h")):
            b=base[me]; b["J"]+=1; b["pts"]+=m[side+"p"]
            if m["draw"]: b["N"]+=1
            elif m["winner"]==("home" if side=="h" else "away"): b["V"]+=1
            else: b["D"]+=1
    n=len(teams); down=2; upn=2 if "Pré-Régionale" in P["division"] else 1
    sqys=[t for t in teams if "SQY" in teams[t].upper()]
    fut=P["future"]
    def play(h,a,S):
        pw=pwin(S[h],S[a]); pd=0.15*(1-abs(2*pw-1)) if P["nopp"]%2==0 else 0
        r=random.random()
        if r<pw-pd/2: return 3,1,1
        if r<pw+pd/2: return 2,2,0
        return 1,3,-1
    res={t:dict(up=0,down=0,ranks=collections.Counter(),byk=collections.defaultdict(lambda:[0,0,0]),combo=collections.defaultdict(lambda:[0,0,0]),others=collections.defaultdict(lambda:[0,0,0])) for t in sqys}
    myf={t:[i for i,m in enumerate(fut) if t in (m['home'],m['away'])] for t in sqys}
    myset={t:set(v) for t,v in myf.items()}
    for _ in range(N):
        pts={t:base[t]["pts"] for t in teams}; wins=collections.Counter()
        S={}
        for t in teams:
            c=compo[t]
            if c and c["regulars"]:
                lu=lineup.sample(c,random)
                S[t]=(statistics.mean(r["points"] for r in lu) if len(lu)==k else strength[t])+random.gauss(0,40)
            else: S[t]=strength[t]+random.gauss(0,80)
        outc=[None]*len(fut)
        for i,m in enumerate(fut):
            hp,ap,r=play(m["home"],m["away"],S); outc[i]=(m["home"],r); pts[m["home"]]+=hp; pts[m["away"]]+=ap
            if r==1: wins[m["home"]]+=1
            elif r==-1: wins[m["away"]]+=1
        order=sorted(teams,key=lambda t:(-pts[t],random.random()))
        for t in sqys:
            rk=order.index(t)+1; R=res[t]; R["ranks"][rk]+=1
            u=rk<=upn; d=rk>n-down
            R["up"]+=u; R["down"]+=d
            bk=R["byk"][wins[t]]; bk[0]+=1; bk[1]+=u; bk[2]+=d
            key="".join({1:"V",0:"N",-1:"D"}[r if h==t else -r] for h,r in (outc[i] for i in myf[t]))
            cb=R["combo"][key]; cb[0]+=1; cb[1]+=u; cb[2]+=d
            for i,(h,r) in enumerate(outc):
                if i in myset[t]: continue
                o=R["others"][f"{i}:{r}"]; o[0]+=1; o[1]+=u; o[2]+=d
    pool=dict(pool=P["poolName"],division=P["division"],fem=P["fem"],n=n,down=down,upn=upn,nopp=P["nopp"],
        teams={t:dict(name=teams[t],strength=round(strength[t]),**base[t]) for t in teams},
        played=[{k:m[k] for k in ("date","round","home","away","hp","ap","winner","draw","forfeit")} for m in P["played"]],
        future=[{k:m[k] for k in ("date","round","home","away")} for m in fut],
        players={int(t):sorted(v.values(),key=lambda x:(-x["n"],-x["points"])) for t,v in P["players"].items()},
        sqy={},
        compo={t:(None if not compo[t] else {kk:[dict(name=r["name"],points=r["points"],inT=r["inT"],J=r["J"],lower=r["lower"],main=r["main"],why=r.get("why","")) for r in compo[t][kk]] for kk in ("probable","bench","burned","alerts","renforts","up")}) for t in teams})
    for t in sqys:
        R=res[t]; nf=sum(1 for m in fut if t in (m["home"],m["away"]))
        pool["sqy"][t]=dict(up=R["up"]/N,down=R["down"]/N,remaining=nf,
            ranks={r:c/N for r,c in sorted(R["ranks"].items())},
            combo={k:v for k,v in R["combo"].items()},
            others=[dict(i=i,home=fut[i]["home"],away=fut[i]["away"],round=fut[i]["round"],date=fut[i]["date"],
                res={r:R["others"].get(f"{i}:{r}",[0,0,0]) for r in (1,0,-1)}) for i in range(len(fut)) if i not in myset[t]],
            byk=[dict(k=k,p=v[0]/N,up=v[1]/v[0],down=v[2]/v[0]) for k,v in sorted(R["byk"].items())],
            matches=[dict(opp=(m["away"] if m["home"]==t else m["home"]),home=m["home"]==t,date=m["date"],round=m["round"],
                pwin=round(pwin(strength[t],strength[m["away"] if m["home"]==t else m["home"]]),3)) for m in fut if t in (m["home"],m["away"])])
        print(f'{teams[t]:<14}{P["division"]:<26} up {R["up"]/N:5.0%} down {R["down"]/N:5.0%} restant {nf}')
    site.append(pool)
json.dump(site,open("site.json","w"),ensure_ascii=False)
print("\nÉcarts de force (habituel -> compo probable avec brûlage):")
for d in DIFF: print("  ",*d)
