#!/usr/bin/env python
"""Tabla + gráfico de la parte (e): Config 3 (1 nodo, 2x4) vs Config 4 (2 nodos, 2x4) y Config 5 (2 nodos, 4x4)."""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", nargs="+", default=[os.path.join(ROOT, "results", "cluster", "test_2nodos.csv")],
                   help="Uno o más CSV (ej. results/cluster/config3.csv results/cluster/config4.csv results/cluster/config5.csv)")
    p.add_argument("--out", default=os.path.join(ROOT, "informe", "figuras", "parte_e.png"))
    args = p.parse_args()

    dfs = [pd.read_csv(f) for f in args.csv if os.path.exists(f)]
    df = pd.concat(dfs, ignore_index=True)
    N = int(df["N"].iloc[0])

    # Clave única de cada experimento: (b, pr, pc, nodes, threads)
    group_cols = ["b", "pr", "pc", "nodes", "threads"]
    runs = (df.groupby(group_cols + ["rep"])
              .agg(t_max=("t_max", "first"), t_comp=("t_comp", "mean"), t_comm=("t_comm", "mean"))
              .reset_index())

    print("### Resumen por configuración (mediana sobre repeticiones)\n")
    print("| b | grid | nodos | CPUs | t_max med [s] | min [s] | max [s] | comp prom [s] | comm prom [s] | comm % | GFLOP/s |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")

    med_rows = []
    for key, sub_runs in runs.groupby(group_cols):
        b, pr, pc, nodes, T = (int(x) for x in key)
        med_t = sub_runs["t_max"].median()
        rep_med = sub_runs.loc[(sub_runs["t_max"] - med_t).abs().idxmin(), "rep"]

        sub_proc = df[(df["b"] == b) & (df["pr"] == pr) & (df["pc"] == pc) &
                      (df["nodes"] == nodes) & (df["threads"] == T) & (df["rep"] == rep_med)].sort_values("rank")
        med_rows.append(sub_proc)

        comp_m = sub_proc["t_comp"].mean()
        comm_m = sub_proc["t_comm"].mean()
        pct = 100 * comm_m / (comp_m + comm_m)
        gflops = 2 * N**3 / 3 / med_t / 1e9
        print(f"| {b} | {pr}×{pc} | {nodes} | {pr * pc * T} | {med_t:.3f} | {sub_runs['t_max'].min():.3f} "
              f"| {sub_runs['t_max'].max():.3f} | {comp_m:.3f} | {comm_m:.3f} | {pct:.0f}% | {gflops:.1f} |")

    med_df = pd.concat(med_rows, ignore_index=True)

    print("\n### Desglose por nodo (host) en la repetición mediana\n")
    print("| b | grid | nodos | host | procesos (ranks) | comp prom [s] | comm prom [s] | t_max [s] |")
    print("|---|---|---|---|---|---|---|---|")
    for (b, pr, pc, nodes, host), hsub in med_df.groupby(["b", "pr", "pc", "nodes", "host"]):
        ranks = ",".join(str(int(r)) for r in hsub["rank"])
        print(f"| {int(b)} | {int(pr)}×{int(pc)} | {int(nodes)} | {host} | {ranks} "
              f"| {hsub['t_comp'].mean():.3f} | {hsub['t_comm'].mean():.3f} | {hsub['t_max'].iloc[0]:.3f} |")

    plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 13})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.2))
    w = 0.35

    # Panel 1: Resumen por configuración (comp prom, comm prom y t_max)
    cfg_summary = (med_df.groupby(group_cols)
                         .agg(t_max=("t_max", "first"), t_comp=("t_comp", "mean"), t_comm=("t_comm", "mean"))
                         .reset_index())
    xs1 = range(len(cfg_summary))
    labels1 = [f"{int(r['pr'])}×{int(r['pc'])}\n{int(r['nodes'])} nodo(s)\n(b={int(r['b'])})"
               for _, r in cfg_summary.iterrows()]

    ax1.bar([x - w / 2 for x in xs1], cfg_summary["t_comp"], w, color="#2E5A88", label="cómputo prom.")
    ax1.bar([x + w / 2 for x in xs1], cfg_summary["t_comm"], w, color="#E08E2B", label="comunicación + espera prom.")
    ax1.scatter(list(xs1), cfg_summary["t_max"], color="#C0392B", s=70, zorder=5, label="t_max (tiempo total)")
    for x, tmax in zip(xs1, cfg_summary["t_max"]):
        ax1.annotate(f"{tmax:.2f} s", (x, tmax), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=11)

    ax1.set_xticks(list(xs1))
    ax1.set_xticklabels(labels1)
    ax1.set_ylabel("tiempo [s]")
    ax1.set_title("Comparación entre configuraciones (1 vs 2 nodos)")
    ax1.set_ylim(0, cfg_summary["t_max"].max() * 1.25)
    ax1.grid(axis="y", color="#DDDDDD", lw=0.8)
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.legend(frameon=False, loc="upper left")

    # Panel 2: Por proceso en grid 2x4 (1 nodo vs 2 nodos)
    sub_2x4 = med_df[(med_df["pr"] == 2) & (med_df["pc"] == 4)]
    b_ref = int(sub_2x4["b"].iloc[0]) if not sub_2x4.empty else int(med_df["b"].iloc[0])
    sub_2x4 = sub_2x4[sub_2x4["b"] == b_ref]

    for nodes_val, marker, ls, col_c, col_m in [(1, "o", "--", "#1B4F72", "#B9770E"),
                                                (2, "s", "-", "#2E86C1", "#F39C12")]:
        s = sub_2x4[sub_2x4["nodes"] == nodes_val].sort_values("rank")
        if s.empty:
            continue
        ax2.plot(s["rank"], s["t_comp"], marker=marker, ls=ls, lw=2, color=col_c,
                 label=f"{nodes_val} nodo(s): cómputo")
        ax2.plot(s["rank"], s["t_comm"], marker=marker, ls=ls, lw=2, color=col_m,
                 label=f"{nodes_val} nodo(s): comm + espera")

    ax2.axvline(3.5, color="#888888", ls=":", lw=1.2)
    ax2.set_xticks(range(8))
    ax2.set_xticklabels([f"r{r}\n({r // 4},{r % 4})" for r in range(8)])
    ax2.set_xlabel("proceso MPI (r0–r3: ventress | r4–r7: ventress en 1n, yodaxico en 2n)")
    ax2.set_ylabel("tiempo por proceso [s]")
    ax2.set_title(f"Grid 2×4 por proceso (b = {b_ref}): 1 nodo vs 2 nodos")
    ax2.set_ylim(0, sub_2x4[["t_comp", "t_comm"]].max().max() * 1.35)
    ax2.grid(axis="y", color="#DDDDDD", lw=0.8)
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.legend(frameon=False, ncol=2, fontsize=10, loc="upper left")

    fig.suptitle(f"LU distribuida (N = {N}): Efecto de 1 nodo vs 2 nodos", fontsize=15, y=1.02)
    fig.tight_layout()
    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print(f"\nfigura: {args.out}")

if __name__ == "__main__":
    main()