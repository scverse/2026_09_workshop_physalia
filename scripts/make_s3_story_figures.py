import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK="#1A1A1A"; GREY="#767676"; BORD="#D8D8D8"; RED="#C0605A"; TEAL="#4C9A8F"
SLATE="#7A8FA6"; ORANGE="#E8912A"
OUT="/Users/tim.treis/Desktop/physalia_slide_assets/"
plt.rcParams.update({"font.family":"DejaVu Sans","text.color":INK,"axes.labelcolor":INK,
 "xtick.color":GREY,"ytick.color":GREY,"axes.edgecolor":BORD,
 "figure.facecolor":"white","axes.facecolor":"white"})
rng=np.random.default_rng(7)
CENTRES=np.array([[0.36,0.55],[0.64,0.45]]); RAD=0.235
def dist(p): return np.min(np.linalg.norm(p[:,None,:]-CENTRES[None],axis=2),axis=1)
def sample(n,pred,pad=.035):
    out=[]
    while len(out)<n:
        p=rng.uniform(pad,1-pad,size=(4000,2)); out.extend(p[pred(p)].tolist())
    return np.array(out[:n])
def draw(ax,phen,title,sub):
    tum=sample(300,lambda p:dist(p)<RAD)
    stroma=sample(230,lambda p:dist(p)>RAD)
    imm=(sample(70,lambda p:dist(p)<RAD) if phen=="inflamed"
         else sample(70,lambda p:(dist(p)>RAD+.012)&(dist(p)<RAD+.10)))
    for c in CENTRES:
        ax.add_patch(plt.Circle(c,RAD,facecolor=SLATE,alpha=.12,edgecolor=SLATE,lw=1.2,zorder=0))
    ax.scatter(*stroma.T,s=14,color=TEAL,alpha=.55,lw=0,zorder=1)
    ax.scatter(*tum.T,s=16,color=SLATE,alpha=.85,lw=0,zorder=2)
    ax.scatter(*imm.T,s=30,color=ORANGE,lw=.6,edgecolor="white",zorder=3)
    ax.set_xlim(0,1); ax.set_ylim(0,1); ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values(): s.set_edgecolor(BORD)
    ax.set_title(title,fontsize=13,color=INK,pad=9)
    ax.text(.5,-.055,sub,transform=ax.transAxes,ha="center",va="top",fontsize=10,color=GREY)

# ---------------- FIG 1 ----------------
fig=plt.figure(figsize=(12.6,6.9))
fig.text(.06,.955,"Same cells, same proportions — two different patients",
         fontsize=17,color=INK,ha="left",va="center")
fig.text(.06,.906,"Immune phenotype is a property of arrangement, not of composition",
         fontsize=11,color=GREY,ha="left",va="center")
axA=fig.add_axes([.06,.375,.42,.47]); axB=fig.add_axes([.545,.375,.42,.47])
draw(axA,"inflamed","Immune-inflamed","immune cells inside the tumour nest")
draw(axB,"excluded","Immune-excluded","held at the margin, never entering")
axb=fig.add_axes([.215,.145,.70,.115])
left=np.zeros(2)
for frac,col,lab in zip([.50,.38,.12],[SLATE,TEAL,ORANGE],["Tumour","Stroma","Immune"]):
    axb.barh(range(2),[frac]*2,left=left,color=col,height=.5,label=lab)
    for y in range(2):
        axb.text(left[0]+frac/2,y,f"{frac:.0%}",ha="center",va="center",fontsize=9.5,
                 color="white" if col!=ORANGE else INK)
    left=left+frac
axb.set_yticks(range(2)); axb.set_yticklabels(["Immune-inflamed","Immune-excluded"],
                                              fontsize=10.5,color=INK)
axb.set_xlim(0,1); axb.set_xticks([]); axb.invert_yaxis()
for s in axb.spines.values(): s.set_visible(False)
axb.tick_params(length=0)
axb.set_title("What dissociation measures — identical in both",fontsize=11.5,color=INK,loc="left",pad=7)
axb.legend(frameon=False,fontsize=10,labelcolor=GREY,ncol=3,loc="upper center",
           bbox_to_anchor=(.5,-.18))
fig.text(.5,.028,"Schematic.  Bulk RNA-seq and dissociated scRNA-seq see only the bars.  "
         "\"Is the immune system getting in?\" lives entirely in the arrangement.",
         ha="center",fontsize=9.6,color=GREY)
fig.savefig(OUT+"S3_0_immune_phenotypes.png",dpi=200,facecolor="white")
print("wrote S3_0_immune_phenotypes.png")

# ---------------- FIG 2 ----------------
fig=plt.figure(figsize=(13.0,5.4))
fig.text(.055,.945,"Each arrangement leaves a different fingerprint",
         fontsize=17,color=INK,ha="left",va="center")
fig.text(.055,.893,"the statistic you reach for is decided by the question, not by the toolbox",
         fontsize=11,color=GREY,ha="left",va="center")
a1=fig.add_axes([.075,.20,.47,.60]); a2=fig.add_axes([.655,.20,.30,.60])
r=np.linspace(5,300,160)
a1.plot(r,1+1.25*np.exp(-r/90),lw=2.6,color=TEAL,label="Immune-inflamed")
a1.plot(r,1-.80*np.exp(-r/130),lw=2.6,color=RED,label="Immune-excluded")
a1.axhline(1,color=INK,lw=1.1)
a1.text(4,1.06,"no preference",ha="left",va="bottom",fontsize=9.5,color=GREY)
a1.annotate("enriched near tumour",xy=(30,2.05),xytext=(108,2.12),fontsize=10,color=TEAL,
            arrowprops=dict(arrowstyle="->",color=TEAL,lw=1.4))
a1.annotate("depleted near tumour",xy=(30,0.30),xytext=(108,0.42),fontsize=10,color=RED,
            arrowprops=dict(arrowstyle="->",color=RED,lw=1.4))
a1.set_xlabel("distance from a tumour cell   r  (µm)",fontsize=11,labelpad=7)
a1.set_ylabel("p(immune | tumour, r) / p(immune)",fontsize=11)
a1.set_title("co_occurrence  —  resolves distance",fontsize=12.5,loc="left",pad=10,color=INK)
a1.set_ylim(0,2.5); a1.set_xlim(0,305)
for s in ("top","right"): a1.spines[s].set_visible(False)
a1.grid(color=BORD,lw=.7); a1.set_axisbelow(True)
a1.legend(frameon=False,fontsize=10,labelcolor=GREY,loc="center right",bbox_to_anchor=(1.0,.62))
a2.barh([0,1],[46,-58],color=[TEAL,RED],height=.46)
a2.axvline(0,color=INK,lw=1.1)
a2.text(51,0,"z = +46",va="center",ha="left",fontsize=10.5,color=GREY)
a2.text(-63,1,"z = −58",va="center",ha="right",fontsize=10.5,color=GREY)
a2.set_yticks([0,1]); a2.set_yticklabels(["Immune-\ninflamed","Immune-\nexcluded"],
                                          fontsize=10.5,color=INK)
a2.set_xlim(-105,95); a2.set_xlabel("immune ↔ tumour enrichment  (z)",fontsize=11,labelpad=7)
a2.set_title("nhood_enrichment  —  adjacency only",fontsize=12.5,loc="left",pad=10,color=INK)
for s in ("top","right","left"): a2.spines[s].set_visible(False)
a2.tick_params(axis="y",length=0); a2.grid(axis="x",color=BORD,lw=.7); a2.set_axisbelow(True)
fig.text(.5,.045,"Schematic expectations.  Adjacency gives you the sign; only the distance curve "
         "tells you how far the exclusion reaches.",ha="center",fontsize=9.6,color=GREY)
fig.savefig(OUT+"S3_C_expected_signatures.png",dpi=200,facecolor="white")
print("wrote S3_C_expected_signatures.png")
