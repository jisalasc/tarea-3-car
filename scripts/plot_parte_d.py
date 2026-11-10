#!/usr/bin/env python
"""Tabla + gráfico de la parte (d): Speedup y eficiencia en configuraciones 0 a 3 (1 nodo)."""
import argparse
import glob
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--csv", nargs="+", default=None,
                   help="Archivos CSV de configs 0..3 (por defecto busca results/cluster/config*.csv)")
    p.add_argument("--b", type=int, nargs="+", default=[512, 1024],
                   help="Valores de b a incluir (ej. 512 1024)")
    p.add_argument("--t1", type=float, default=None,
                   help="Tiempo base T(1) en segundos (si no hay fila 1x1 T=1 en los CSV)")
    p.add_argument("--out", default=os.path.join(ROOT, "informe", "figuras", "parte_d.png"))
    args = p.parse_args()

    csv_files = args.csv or sorted(glob.glob(os.path.join(ROOT, "results", "cluster", "config[0-3].csv")))
    if not csv_files:
        # Fallback con los CSV ya presentes en el repo para poder probar el script antes de correr config0..3
        csv_files = [os.path.join(ROOT, "results", "cluster", "parte_c.csv"),
                     os.path.join(ROOT, "results", "cluster", "test_2nodos.csv")]

    dfs = [pd.read_csv(f) for f in csv_files if os.path.exists(f)]
    df = pd.concat(dfs, ignore_index=True)
    df = df[(df["nodes"] == 1) & (df["b"].isin(args.b))].copy()
    N = int(df["N"].iloc[0])

    group_cols = ["b", "pr", "pc", "threads"]
    runs = (df.groupby(group_cols + ["rep"])
              .agg(t_max=("t_max", "first"), t_comp=("t_comp", "mean"), t_comm=("t_comm", "mean"))
              .reset_index())

    summary_rows = []
    for key, sub in runs.groupby(group_cols):
        b, pr, pc, T = (int(x) for x in key)
        med_t = sub["t_max"].median()
        rep_med = sub.loc[(sub["t_max"] - med_t).abs().idxmin()]
        cpus = pr * pc * T
        summary_rows.append({
            "b": b, "pr": pr, "pc": pc, "grid": f"{pr}×{pc}", "p": pr * pc, "T": T, "cpus": cpus,
            "t_max": float(med_t), "t_min": float(sub["t_max"].min()), "t_max_hi": float(sub["t_max"].max()),
            "t_comp": float(rep_med["t_comp"]), "t_comm": float(rep_med["t_comm"]),
            "gflops": 2 * N**3 / 3 / float(med_t) / 1e9,
        })

    sum_df = pd.DataFrame(summary_rows).sort_values(["b", "cpus", "p", "pr"])

    # Determinar T(1) por cada valor de b
    t1_map = {}
    for b in sum_df["b"].unique():
        base = sum_df[(sum_df["b"] == b) & (sum_df["pr"] == 1) & (sum_df["pc"] == 1) & (sum_df["T"] == 1)]
        if not base.empty:
            t1_map[b] = float(base["t_max"].iloc[0])
        elif args.t1 is not None:
            t1_map[b] = args.t1
        else:
            # Estimación de respaldo desde ~25.5 GFLOP/s (1 core de ventress medido en apuntes/cluster.txt)
            t1_map[b] = (2 * N**3 / 3) / (25.5e9)
            print(f"[aviso] No hay fila 1×1 T=1 para b={b}; usando T(1) estimado = {t1_map[b]:.3f} s (pasa --t1 o config0.csv)")

    sum_df["t1"] = sum_df["b"].map(t1_map)
    sum_df["speedup"] = sum_df["t1"] / sum_df["t_max"]
    sum_df["eficiencia"] = sum_df["speedup"] / sum_df["cpus"]

    print("| b | grid (pr×pc) | T | CPUs | t_max [s] | comp [s] | comm [s] | GFLOP/s | Speedup | Eficiencia |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for _, r in sum_df.iterrows():
        print(f"| {int(r['b'])} | {r['grid']} | {int(r['T'])} | {int(r['cpus'])} | {r['t_max']:.3f} "
              f"| {r['t_comp']:.3f} | {r['t_comm']:.3f} | {r['gflops']:.1f} | {r['speedup']:.2f}× | {100 * r['eficiencia']:.1f}% |")

    plt.rcParams.update({"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 13})
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13.5, 5.2))

    max_cpus = max(8, int(sum_df["cpus"].max()))
    ax1.plot([1, max_cpus], [1, max_cpus], ls=":", color="#888888", lw=1.5, label="ideal (S = CPUs)")
    ax2.axhline(100.0, ls=":", color="#888888", lw=1.5, label="ideal (E = 100%)")

    palette = ["#2E5A88", "#E08E2B", "#27AE60", "#8E44AD", "#C0392B", "#16A085"]
    markers = ["o", "s", "^", "D", "v", "P"]

    for idx, ((b, grid_str), gsub) in enumerate(sum_df.groupby(["b", "grid"])):
        col = palette[idx % len(palette)]
        mk = markers[idx % len(markers)]
        lbl = f"grid {grid_str} (b={int(b)})"
        ax1.plot(gsub["cpus"], gsub["speedup"], marker=mk, lw=2, ms=7, color=col, label=lbl)
        ax2.plot(gsub["cpus"], gsub["eficiencia"] * 100, marker=mk, lw=2, ms=7, color=col, label=lbl)
        for _, r in gsub.iterrows():
            offset = (0, 10) if idx % 2 == 0 else (0, -18)
            ax1.annotate(f"T={int(r['T'])} ({r['speedup']:.2f}×)", (r["cpus"], r["speedup"]),
                         textcoords="offset points", xytext=offset, ha="center", fontsize=9.5)
        
    for ax in (ax1, ax2):
        ax.set_xticks([1, 2, 4, 8])
        ax.set_xlabel("CPUs totales (pr × pc × T)")
        ax.grid(axis="y", color="#DDDDDD", lw=0.8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.legend(frameon=False, fontsize=10)

    ax1.set_ylabel("Speedup S = T(1) / T(p, T)")
    ax1.set_title("Speedup vs CPUs totales (1 nodo)")
    ax1.set_ylim(0, max_cpus * 1.1)

    ax2.set_ylabel("Eficiencia E = S / CPUs [%]")
    ax2.set_title("Eficiencia vs CPUs totales (1 nodo)")
    ax2.set_ylim(0, 115)

    fig.suptitle(f"Parte (d): Escalabilidad en 1 nodo (N = {N})", fontsize=15, y=1.02)
    fig.tight_layout()
    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print(f"\nfigura: {args.out}")


if __name__ == "__main__":
    main()