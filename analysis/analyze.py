"""Paired analysis of the two arms: accuracy, bootstrap CI, exact McNemar, cost.

Usage: python analysis/analyze.py results/summary.json results/results.json
"""
import json,math,random,sys
from collections import defaultdict
d=json.load(open(sys.argv[1]))
n=len(d)
def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den; return c-h,c+h
def mcnemar_exact(b,c):
    m=b+c; k=min(b,c)
    p=sum(math.comb(m,i) for i in range(k+1))/2**m*2
    return min(p,1.0)
def boot(rows,B=10000,seed=0):
    r=random.Random(seed); diffs=[]
    for _ in range(B):
        s=[rows[r.randrange(len(rows))] for _ in rows]
        diffs.append(sum(x["t_ok"]-x["c_ok"] for x in s)/len(s))
    diffs.sort(); return diffs[int(.025*B)],diffs[int(.975*B)]
def report(rows,label):
    n=len(rows); c=sum(x["c_ok"] for x in rows); t=sum(x["t_ok"] for x in rows)
    b=sum(x["t_ok"] and not x["c_ok"] for x in rows); br=sum(x["c_ok"] and not x["t_ok"] for x in rows)
    lo,hi=boot(rows,2000)
    print(f"{label:24s} n={n:3d} ctrl={c/n:6.1%} treat={t/n:6.1%} diff={(t-c)/n*100:+5.1f}pt CI[{lo*100:+.1f},{hi*100:+.1f}] fixed={b:3d} broken={br:3d} p={mcnemar_exact(b,br):.3f}")
    return dict(n=n,c=c,t=t,fixed=b,broken=br,lo=lo,hi=hi,p=mcnemar_exact(b,br))
res={}
res["ALL"]=report(d,"ALL")
c=sum(x["c_ok"] for x in d); t=sum(x["t_ok"] for x in d)
print("wilson ctrl",wilson(c,n),"treat",wilson(t,n))
for k in ("simple","moderate","challenging"):
    res[k]=report([x for x in d if x["difficulty"]==k],k)
dbs=defaultdict(list)
for x in d: dbs[x["db_id"]].append(x)
res["db"]={}
for k,v in sorted(dbs.items(),key=lambda kv: -(sum(x["t_ok"]-x["c_ok"] for x in kv[1])/len(kv[1]))):
    res["db"][k]=report(v,k)
print("no sql ctrl",sum(not x["c_sql"] for x in d),"treat",sum(not x["t_sql"] for x in d))
from collections import Counter
print("fail kinds ctrl",Counter(x["c_fail"] for x in d),"treat",Counter(x["t_fail"] for x in d))
ti=sum(x.get("t_in",0) for x in d); to=sum(x.get("t_out",0) for x in d); calls=[x.get("t_calls",0) for x in d]
ci=sum(x["c_in"] or 0 for x in d); co=sum(x["c_out"] or 0 for x in d)
tc=(ti*0.1+to*0.5)/1e6; cc=(ci*0.1+co*0.5)/1e6
print(f"treat tokens in={ti/n:.0f}/q out={to/n:.0f}/q cost=${tc:.2f} (${tc/n:.4f}/q) calls mean={sum(calls)/n:.1f} median={sorted(calls)[n//2]} max={max(calls)}")
print(f"ctrl tokens in={ci/n:.0f}/q out={co/n:.0f}/q cost=${cc:.2f} (${cc/n:.5f}/q)")
print(f"cost per correct: ctrl ${cc/c:.5f} treat ${tc/t:.4f}; marginal cost per extra correct ${(tc-cc)/(t-c):.3f}")
res["cost"]=dict(t=tc,c=cc,calls=sum(calls)/n,tin=ti/n,tout=to/n)
json.dump(res,open(sys.argv[2] if len(sys.argv)>2 else "results.json","w"),indent=1)
