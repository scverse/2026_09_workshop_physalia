import sys, numpy as np, pandas as pd, scanpy as sc, anndata as ad, squidpy as sq, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
sys.path.insert(0, "/Users/tim.treis/Documents/GitHub/2026_09_workshop_physalia")
import paths
INK="#1A1A1A"; GREY="#767676"; BORD="#D8D8D8"; RED="#C0605A"; TEAL="#4C9A8F"; SLATE="#7A8FA6"; ORANGE="#E8912A"; STEEL="#4A7BA7"
OUT="/Users/tim.treis/Desktop/physalia_slide_assets/"

def main():
    plt.rcParams.update({"font.family":"DejaVu Sans","text.color":INK,"axes.labelcolor":INK,
        "xtick.color":GREY,"ytick.color":GREY,"axes.edgecolor":BORD,
        "figure.facecolor":"white","axes.facecolor":"white"})
    sc.settings.verbosity=0
    a=ad.read_h5ad(paths.OUT/"xenium_qc_filtered.h5ad")
    a.layers["counts"]=a.X.copy(); sc.pp.normalize_total(a); sc.pp.log1p(a)
    sc.pp.pca(a,n_comps=30); sc.pp.neighbors(a)
    sc.tl.leiden(a,resolution=0.5,key_added="leiden",flavor="igraph",n_iterations=2,directed=False)
    a.obs["cell_type"]=a.obs["leiden"].map({"0":"Epithelial","1":"Epithelial","2":"Proliferating",
                                            "3":"Myeloid","4":"Fibroblast"}).astype("category")
    cats=list(a.obs["cell_type"].cat.categories); n=a.obs["cell_type"].value_counts()
    sq.gr.spatial_neighbors_delaunay(a)
    sq.gr.nhood_enrichment(a,cluster_key="cell_type",seed=0)
    z=pd.DataFrame(a.uns["cell_type_nhood_enrichment"]["zscore"],index=cats,columns=cats)
    sq.gr.co_occurrence(a,cluster_key="cell_type")
    oc=a.uns["cell_type_co_occurrence"]; occ,iv=oc["occ"],oc["interval"]

    # ---------- FIG A : named types give a real answer ----------
    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12.6,4.9),gridspec_kw={"width_ratios":[1,1.12]})
    div=LinearSegmentedColormap.from_list("d",[RED,"#FFFFFF",TEAL])
    v=np.abs(z.values).max()
    im=ax1.imshow(z.values,cmap=div,norm=TwoSlopeNorm(vcenter=0,vmin=-v,vmax=v))
    ax1.set_xticks(range(len(cats))); ax1.set_xticklabels(cats,rotation=20,ha="right",fontsize=9.5,color=INK)
    ax1.set_yticks(range(len(cats))); ax1.set_yticklabels(cats,fontsize=9.5,color=INK)
    for i in range(len(cats)):
        for j in range(len(cats)):
            val=z.values[i,j]
            ax1.text(j,i,f"{val:+.0f}",ha="center",va="center",fontsize=10,
                     color="white" if abs(val)>.62*v else INK,
                     fontweight="bold" if abs(val)>.62*v else "normal")
    ax1.set_xticks(np.arange(-.5,len(cats),1),minor=True); ax1.set_yticks(np.arange(-.5,len(cats),1),minor=True)
    ax1.grid(which="minor",color="white",lw=1.6); ax1.tick_params(which="minor",length=0); ax1.tick_params(length=0)
    ax1.set_title("Neighbourhood enrichment (z)",fontsize=11.5,loc="left",pad=10,color=INK)
    cb=fig.colorbar(im,ax=ax1,fraction=.042,pad=.02); cb.outline.set_edgecolor(BORD)
    cb.ax.tick_params(labelsize=8.5,color=GREY)
    cb.set_label("segregated  ←   z   →  co-localised",fontsize=8.5,color=GREY)

    mi,ei=cats.index("Myeloid"),cats.index("Epithelial")
    fi=cats.index("Fibroblast")
    k=occ.shape[2]
    ax2.axhline(1.0,color=INK,lw=1,ls="-",zorder=1)
    ax2.plot(iv[:k],occ[mi,ei,:],lw=2,color=RED,marker="o",ms=5,zorder=3,
             label="Myeloid near Epithelial")
    ax2.plot(iv[:k],occ[mi,fi,:],lw=2,color=TEAL,marker="o",ms=5,zorder=3,
             label="Myeloid near Fibroblast")
    ax2.text(iv[k//2]*0.72,1.06,"no preference",ha="left",va="bottom",fontsize=8.5,color=GREY)
    ax2.set_xlabel("distance r  (µm)",fontsize=10); ax2.set_ylabel("p(Myeloid | cond, r) / p(Myeloid)",fontsize=10)
    ax2.set_title("Myeloid cells avoid tumour at every distance",fontsize=11.5,loc="left",pad=10,color=INK)
    for s in ("top","right"): ax2.spines[s].set_visible(False)
    ax2.grid(color=BORD,lw=.7); ax2.set_axisbelow(True)
    ax2.legend(frameon=False,fontsize=9,labelcolor=GREY,loc="center right")
    fig.text(.5,.015,"Xenium breast, 6,472 cells  ·  Epithelial 3,914 · Proliferating 1,192 · Fibroblast 688 · Myeloid 678  ·  Delaunay graph, 1,000 label permutations",
             ha="center",fontsize=8.8,color=GREY)
    fig.tight_layout(rect=[0,.05,1,1]); fig.savefig(OUT+"S3_A_named_types_immune_exclusion.png",dpi=200,facecolor="white")
    print("wrote S3_A_named_types_immune_exclusion.png")

    # ---------- FIG B : the two statistics with no null ----------
    sq.gr.centrality_scores(a,cluster_key="cell_type")
    cdf=a.uns["cell_type_centrality_scores"].copy(); cdf["n_cells"]=[n[i] for i in cdf.index]
    sq.gr.ripley(a,cluster_key="cell_type",mode="L",n_simulations=50)
    rip=a.uns["cell_type_ripley_L"]["L_stat"]
    xy=np.asarray(a.obsm["spatial"]); W,H=np.ptp(xy[:,0]),np.ptp(xy[:,1])

    fig,(ax1,ax2)=plt.subplots(1,2,figsize=(12.6,4.9))
    r=np.corrcoef(cdf["degree_centrality"],cdf["n_cells"])[0,1]
    ax1.scatter(cdf["n_cells"],cdf["degree_centrality"],s=110,color=STEEL,zorder=3)
    for i,row in cdf.iterrows():
        ax1.annotate(i,(row["n_cells"],row["degree_centrality"]),textcoords="offset points",
                     xytext=(9,-3),fontsize=9.5,color=INK)
    m,b=np.polyfit(cdf["n_cells"],cdf["degree_centrality"],1)
    xs=np.linspace(cdf["n_cells"].min()*.8,cdf["n_cells"].max()*1.08,50)
    ax1.plot(xs,m*xs+b,color=ORANGE,lw=1.8,ls="--",zorder=2)
    ax1.set_xlabel("cells in the cluster",fontsize=10); ax1.set_ylabel("degree centrality",fontsize=10)
    ax1.set_title(f"Centrality is cluster size  (r = {r:+.2f})",fontsize=11.5,loc="left",pad=10,color=INK)
    ax1.set_xlim(0,cdf["n_cells"].max()*1.25)
    for s in ("top","right"): ax1.spines[s].set_visible(False)
    ax1.grid(color=BORD,lw=.7); ax1.set_axisbelow(True)
    ax1.text(.03,.95,"no null model, no p-value\n(slide 21)",transform=ax1.transAxes,fontsize=9,color=GREY,va="top")

    for c,col in zip(cats,[SLATE,TEAL,ORANGE,STEEL]):
        s=rip[rip["cell_type"]==c].sort_values("bins")
        ax2.plot(s["bins"],s["stats"]-s["bins"],lw=1.9,color=col,label=c)
    ax2.axhline(0,color=INK,lw=1)
    for rr,lbl in ((100,"39%"),(200,"69%"),(342,"97%")):
        ax2.axvline(rr,color=BORD,lw=1,ls=":")
        ax2.text(rr,ax2.get_ylim()[0]*.06,f" {lbl}",fontsize=8,color=GREY,rotation=90,va="bottom")
    ax2.set_xlabel("radius r  (µm)",fontsize=10); ax2.set_ylabel("L(r) − r",fontsize=10)
    ax2.set_title("Ripley: every type 'dispersed' — it is the edge",fontsize=11.5,loc="left",pad=10,color=INK)
    for s in ("top","right"): ax2.spines[s].set_visible(False)
    ax2.grid(color=BORD,lw=.7); ax2.set_axisbelow(True)
    ax2.legend(frameon=False,fontsize=9,labelcolor=GREY,loc="lower left")
    ax2.text(.97,.95,f"section is {W:.0f} × {H:.0f} µm\ndotted = % of area within r of a border",
             transform=ax2.transAxes,ha="right",va="top",fontsize=8.5,color=GREY)
    fig.text(.5,.015,"Both panels contradict nhood_enrichment, which puts Myeloid self-enrichment at z = +69.2 — a statistic without a null cannot tell you it is reporting a nuisance",
             ha="center",fontsize=8.8,color=GREY)
    fig.tight_layout(rect=[0,.05,1,1]); fig.savefig(OUT+"S3_B_no_null_diagnostics.png",dpi=200,facecolor="white")
    print("wrote S3_B_no_null_diagnostics.png")

if __name__=="__main__":
    main()
