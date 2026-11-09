#!/usr/bin/env python
"""Gráfico + tabla de la parte (a) desde results/parte_a_<tag>.csv.

Uso: python scripts/plot_parte_a.py --tag mac_jose
Genera informe/figuras/parte_a_<tag>.png y imprime la tabla (mediana, min, max) en Markdown.
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
    p.add_argument("--tag", required=True)
    args = p.parse_args()
    df = pd.read_csv(os.path.join(ROOT, "results", f"parte_a_{args.tag}.csv"))
    N = int(df.N.iloc[0])
    g = df.groupby("b").time_s.agg(mediana="median", min="min", max="max", n="count").sort_index(ascending=False)
    g["GFLOP/s (mediana)"] = 2 * N**3 / 3 / g["mediana"] / 1e9
    g["vs. mejor"] = g["mediana"] / g["mediana"].min()
    best = int(g["mediana"].idxmin())
    print(f"N={N}, threads={int(df.threads.iloc[0])}, repeticiones por b={int(g.n.iloc[0])}, mejor b={best}\n")
    print("| b | N/b | mediana [s] | min [s] | max [s] | GFLOP/s | vs. mejor |")
    print("|---|---|---|---|---|---|---|")
    for b, r in g.iterrows():
        print(f"| {b} | {N // b} | {r['mediana']:.3f} | {r['min']:.3f} | {r['max']:.3f} | {r['GFLOP/s (mediana)']:.1f} | {r['vs. mejor']:.2f}× |")

    plt.rcParams.update({"font.size": 13, "axes.titlesize": 15, "axes.labelsize": 14})
    fig, ax = plt.subplots(figsize=(8, 5))
    xs = g.index.values
    ax.plot(xs, g["mediana"], color="#2E5A88", lw=2, marker="o", ms=7, zorder=3, label="mediana")
    ax.fill_between(xs, g["min"], g["max"], color="#2E5A88", alpha=0.15, lw=0, label="min–max")
    for b, t in zip(xs, g["mediana"]):
        ax.annotate(f"{t:.2f} s", (b, t), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=11)
    ax.scatter([best], [g.loc[best, "mediana"]], s=160, facecolor="none", edgecolor="#C0392B", lw=2, zorder=4,
               label=f"mejor: b = {best}")
    ax.set_xscale("log", base=2)
    ax.set_xticks(xs)
    ax.set_xticklabels([f"{b}\n(N/{N // b})" for b in xs])
    ax.set_xlabel("tamaño de bloque b")
    ax.set_ylabel("tiempo de factorización [s]")
    ax.set_title(f"LU por bloques serial, N = {N}, 1 thread ({int(g.n.iloc[0])} repeticiones)")
    ax.set_ylim(0, g["max"].max() * 1.15)
    ax.grid(axis="y", color="#DDDDDD", lw=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, loc="upper center")
    fig.tight_layout()
    out = os.path.join(ROOT, "informe", "figuras", f"parte_a_{args.tag}.png")
    fig.savefig(out, dpi=160)
    print(f"\nfigura: {out}")


if __name__ == "__main__":
    main()
