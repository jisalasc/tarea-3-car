#!/usr/bin/env python
"""Tabla + gráfico de la parte (f): b = N/2 vs b = N/16 por proceso en grid 2x2."""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=os.path.join(ROOT, "results", "cluster", "parte_c.csv"))
    p.add_argument("--out", default=os.path.join(ROOT, "informe", "figuras", "parte_f.png"))
    args = p.parse_args()
    df = pd.read_csv(args.csv)

    N = int(df["N"].iloc[0])
    b_targets = [N // 2, N // 16]
    seleccion = []

    for b in b_targets:
        sub = df[(df["pr"] == 2) & (df["pc"] == 2) & (df["b"] == b)]
        # Buscamos el 'rep' cuyo t_max está más cerca de la mediana de t_max
        t_por_rep = sub.groupby("rep")["t_max"].first()
        rep_med = (t_por_rep - t_por_rep.median()).abs().idxmin()
        seleccion.append(sub[sub["rep"] == rep_med].sort_values("rank"))

    med_df = pd.concat(seleccion, ignore_index=True)

    print("| b | N/b | rank | proc (r,c) | t_comp [s] | t_comm [s] | t_wall [s] | t_max [s] | comm % |")
    print("|---|---|---|---|---|---|---|---|---|")
    for _, r in med_df.iterrows():
        b = int(r["b"])
        tot = r["t_comp"] + r["t_comm"]
        comm_pct = 100 * r["t_comm"] / tot if tot > 0 else 0.0
        print(f"| {b} | {N // b} | {int(r['rank'])} | ({int(r['myrow'])},{int(r['mycol'])}) "
              f"| {r['t_comp']:.3f} | {r['t_comm']:.3f} | {r['t_wall']:.3f} | {r['t_max']:.3f} | {comm_pct:.0f}% |")

    plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 14})
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), sharey=True)
    w = 0.35

    for ax, b in zip(axes, b_targets):
        sub = med_df[med_df["b"] == b].sort_values("rank")
        xs = range(len(sub))
        labels = [f"r{int(r['rank'])}\n({int(r['myrow'])},{int(r['mycol'])})" for _, r in sub.iterrows()]
        t_max = float(sub["t_max"].iloc[0])

        ax.bar([x - w / 2 for x in xs], sub["t_comp"], w, color="#2E5A88", label="cómputo (BLAS/LAPACK)")
        ax.bar([x + w / 2 for x in xs], sub["t_comm"], w, color="#E08E2B", label="comunicación + espera (Bcast)")
        ax.axhline(t_max, color="#C0392B", ls="--", lw=1.5, label=f"t_max = {t_max:.2f} s")

        ax.set_xticks(list(xs))
        ax.set_xticklabels(labels)
        ax.set_xlabel("proceso MPI (rank y coordenada en grid 2×2)")
        ax.set_title(f"b = {b} (N/{N // b}) — {N // b}×{N // b} bloques")
        ax.grid(axis="y", color="#DDDDDD", lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, loc="upper left")

    axes[0].set_ylabel("tiempo por proceso [s]")
    axes[0].set_ylim(0, med_df["t_max"].max() * 1.18)
    fig.suptitle(f"LU distribuida en grid 2×2 (N = {N}): b = N/2 vs b = N/16", fontsize=16, y=1.02)
    fig.tight_layout()
    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print(f"\nfigura: {args.out}")

if __name__ == "__main__":
    main()
