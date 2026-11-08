"""Render the results chart.

Usage: python analysis/chart.py results/results.json results/bird_auto_ontology_results.png
"""
import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
import sys
r=json.load(open(sys.argv[1] if len(sys.argv)>1 else "results/results.json"))
groups=[("All 500","ALL"),("Simple\n(148)","simple"),("Moderate\n(250)","moderate"),("Challenging\n(102)","challenging")]
C,T="#eb6834","#2a78d6"; ink="#0b0b0b"; ink2="#52514e"; surf="#fcfcfb"
plt.rcParams.update({"font.family":"DejaVu Sans"})
fig,ax=plt.subplots(figsize=(10,6.2),dpi=200); fig.patch.set_facecolor(surf); ax.set_facecolor(surf)
w=0.36; gap=0.02
for i,(lab,k) in enumerate(groups):
    g=r[k]; cv=g["c"]/g["n"]*100; tv=g["t"]/g["n"]*100
    for x,v,col in ((i-w/2-gap/2,cv,C),(i+w/2+gap/2,tv,T)):
        ax.add_patch(FancyBboxPatch((x-w/2,0),w,v,boxstyle="round,pad=0,rounding_size=0.03",mutation_aspect=40,fc=col,ec="none"))
        ax.text(x,v+1.2,f"{v:.1f}%",ha="center",va="bottom",fontsize=11,color=ink)
    d=tv-cv
    ax.text(i,max(cv,tv)+7.5,f"{d:+.1f} pts",ha="center",fontsize=11.5,fontweight="bold",color=ink if d>0 else ink2)
ax.set_xlim(-0.6,3.6); ax.set_ylim(0,92)
ax.set_xticks(range(4)); ax.set_xticklabels([g[0] for g in groups],fontsize=11,color=ink)
ax.set_yticks([0,25,50,75]); ax.set_yticklabels([f"{v}%" for v in [0,25,50,75]],fontsize=10,color=ink2)
ax.yaxis.grid(True,color="#e4e3df",lw=0.8); ax.set_axisbelow(True)
for s in ("top","right","left"): ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#c9c8c2"); ax.tick_params(length=0)
ax.set_ylabel("Execution accuracy",fontsize=10.5,color=ink2)
fig.text(0.07,0.955,"NVIDIA Auto Ontology vs. schema-only prompting on BIRD Mini-Dev",fontsize=15,fontweight="bold",color=ink)
fig.text(0.07,0.915,"500 text-to-SQL questions, 11 databases, same model (Claude Haiku 5.5) in both arms",fontsize=11,color=ink2)
from matplotlib.lines import Line2D
h=[Line2D([0],[0],marker="s",ls="",ms=11,mfc=C,mec="none"),Line2D([0],[0],marker="s",ls="",ms=11,mfc=T,mec="none")]
fig.legend(h,["Schema only (1 LLM call, $0.0006/question)","Auto Ontology agent (~16 LLM calls, $0.014/question)"],loc="upper left",bbox_to_anchor=(0.062,0.895),frameon=False,fontsize=10.5,ncol=2,labelcolor=ink,columnspacing=1.5,handletextpad=0.4)
fig.text(0.07,0.025,"Overall: +3.8 pts, 95% CI [0.0, +7.6], McNemar p = 0.06 (56 questions fixed, 37 broken).  Independent run, Nov 2026.",fontsize=9.5,color=ink2)
plt.subplots_adjust(left=0.07,right=0.98,top=0.80,bottom=0.13)
fig.savefig(sys.argv[2] if len(sys.argv)>2 else "results/bird_auto_ontology_results.png",facecolor=surf)
