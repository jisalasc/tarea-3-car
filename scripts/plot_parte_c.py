#!/usr/bin/env python
"""Tabla + gráfico de la parte (c): barrido de b en el cluster (grid 2x2, T=2, N=2^13).

Uso: python scripts/plot_parte_c.py [--csv results/cluster/parte_c.csv]
Imprime la tabla en Markdown (mediana de t_max sobre reps, y promedio por proceso de
t_comp / t_comm en la repetición mediana) y genera informe/figuras/parte_c.png.
"""
import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", default=os.path.join(ROOT, "results", "cluster", "parte_c.csv"))
    p.add_argument("--out", default=os.path.join(ROOT, "informe", "figuras", "parte_c.png"))
    args = p.parse_args()
    df = pd.read_csv(args.csv)
    N, pr, pc, T = (int(df[c].iloc[0]) for c in ("N", "pr", "pc", "threads"))
    P = pr * pc
    # una fila por (b, rep): t_max es igual en todos los procesos; comp/comm promedio por proceso
    runs = df.groupby(["b", "rep"]).agg(t_max=("t_max", "first"), comp=("t_comp", "mean"),
                                        comm=("t_comm", "mean"), comm_max=("t_comm", "max")).reset_index()
    g = runs.groupby("b").t_max.agg(mediana="median", min="min", max="max", n="count").sort_index(ascending=False)
    # repetición mediana de cada b para desglosar comp/comm
    med = runs.loc[runs.groupby("b").t_max.apply(lambda s: (s - s.median()).abs().idxmin())].set_index("b")
    g["comp"] = med["comp"]; g["comm"] = med["comm"]
    g["GFLOP/s"] = 2 * N**3 / 3 / g["mediana"] / 1e9
    g["vs. mejor"] = g["mediana"] / g["mediana"].min()
    best = int(g["mediana"].idxmin())
    hosts = sorted(df.host.unique())
    print(f"N={N}, grid={pr}x{pc} (p={P}), T={T}, nodos={hosts}, reps={int(g.n.iloc[0])}, mejor b={best}\n")
    print("| b | N/b | t_max mediana [s] | min | max | comp/proc [s] | comm/proc [s] | comm % | GFLOP/s | vs. mejor |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for b, r in g.iterrows():
        print(f"| {b} | {N // b} | {r['mediana']:.3f} | {r['min']:.3f} | {r['max']:.3f} | {r['comp']:.3f} | "
              f"{r['comm']:.3f} | {100 * r['comm'] / (r['comp'] + r['comm']):.0f}% | {r['GFLOP/s']:.1f} | {r['vs. mejor']:.2f}× |")

    plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 14})
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    xs = g.index.values
    ax.plot(xs, g["mediana"], color="#2E5A88", lw=2, marker="o", ms=7, zorder=3, label="t_max (mediana)")
    ax.fill_between(xs, g["min"], g["max"], color="#2E5A88", alpha=0.15, lw=0, label="min–max")
    for b, t in zip(xs, g["mediana"]):
        ax.annotate(f"{t:.2f}", (b, t), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=11)
    ax.scatter([best], [g.loc[best, "mediana"]], s=160, facecolor="none", edgecolor="#C0392B", lw=2, zorder=4,
               label=f"mejor: b = {best}")
    ax.set_xscale("log", base=2); ax.set_xticks(xs); ax.set_xticklabels([str(b) for b in xs])
    ax.set_xlabel("tamaño de bloque b"); ax.set_ylabel("tiempo [s]")
    ax.set_title(f"LU distribuida, N = {N}, grid {pr}×{pc}, T = {T}")
    ax.set_ylim(0, g["max"].max() * 1.15)
    ax.grid(axis="y", color="#DDDDDD", lw=0.8); ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center")

    w = 0.35
    g2 = g.sort_index()  # mismo orden (b creciente) que el panel izquierdo
    idx = range(len(g2))
    ax2.bar([i - w / 2 for i in idx], g2["comp"], w, color="#2E5A88", label="cómputo (BLAS/LAPACK)")
    ax2.bar([i + w / 2 for i in idx], g2["comm"], w, color="#E08E2B", label="comunicación (Bcast)")
    ax2.set_xticks(list(idx)); ax2.set_xticklabels([str(b) for b in g2.index])
    ax2.set_xlabel("tamaño de bloque b"); ax2.set_ylabel("tiempo promedio por proceso [s]")
    ax2.set_title("desglose en la repetición mediana")
    ax2.grid(axis="y", color="#DDDDDD", lw=0.8); ax2.spines[["top", "right"]].set_visible(False)
    ax2.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(args.out, dpi=160)
    print(f"\nfigura: {args.out}")


if __name__ == "__main__":
    main()
