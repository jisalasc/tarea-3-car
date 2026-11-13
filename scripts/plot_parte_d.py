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
                   help="Archivos CSV de configs 0..3 (por defecto busca results/cluster/config[0-3].csv)")
    p.add_argument("--b", type=int, nargs="+", default=[512, 1024],
                   help="Valores de b a incluir (ej. 512 1024)")
    p.add_argument("--t1", type=float, default=None,
                   help="Tiempo base T(1) en segundos (si no hay fila 1x1 T=1 en los CSV)")
    p.add_argument("--out", default=os.path.join(ROOT, "informe", "figuras", "parte_d.png"))
    args = p.parse_args()

    csv_files = args.csv or sorted(glob.glob(os.path.join(ROOT, "results", "cluster", "config[0-3].csv")))
    if not csv_files:
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

    cfg_map = {(1, 1): 0, (1, 2): 1, (2, 1): 1, (2, 2): 2, (2, 4): 3, (4, 2): 3}
    summary_rows = []
    for key, sub in runs.groupby(group_cols):
        b, pr, pc, T = (int(x) for x in key)
        med_t = sub["t_max"].median()
        rep_med = sub.loc[(sub["t_max"] - med_t).abs().idxmin()]
        cpus = pr * pc * T
        summary_rows.append({
            "b": b, "cfg": cfg_map.get((pr, pc), -1), "pr": pr, "pc": pc, "grid": f"{pr}×{pc}",
            "p": pr * pc, "T": T, "cpus": cpus,
            "t_max": float(med_t), "t_min": float(sub["t_max"].min()), "t_max_hi": float(sub["t_max"].max()),
            "t_comp": float(rep_med["t_comp"]), "t_comm": float(rep_med["t_comm"]),
            "gflops": 2 * N**3 / 3 / float(med_t) / 1e9,
        })

    sum_df = pd.DataFrame(summary_rows).sort_values(["b", "cfg", "pr", "T"])

    # Determinar T(1) por cada valor de b (desde 1x1 T=1 en config0.csv)
    t1_map = {}
    for b in sum_df["b"].unique():
        base = sum_df[(sum_df["b"] == b) & (sum_df["pr"] == 1) & (sum_df["pc"] == 1) & (sum_df["T"] == 1)]
        if not base.empty:
            t1_map[b] = float(base["t_max"].iloc[0])
        elif args.t1 is not None:
            t1_map[b] = args.t1
        else:
            t1_map[b] = (2 * N**3 / 3) / (25.5e9)

    sum_df["t1"] = sum_df["b"].map(t1_map)
    sum_df["speedup"] = sum_df["t1"] / sum_df["t_max"]
    sum_df["eficiencia"] = sum_df["speedup"] / sum_df["cpus"]

    print("| b | config | grid (pr×pc) | T | CPUs | t_max [s] | comp [s] | comm [s] | GFLOP/s | Speedup | Eficiencia |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for _, r in sum_df.iterrows():
        print(f"| {int(r['b'])} | {int(r['cfg'])} | {r['grid']} | {int(r['T'])} | {int(r['cpus'])} | {r['t_max']:.3f} "
              f"| {r['t_comp']:.3f} | {r['t_comm']:.3f} | {r['gflops']:.1f} | {r['speedup']:.2f}× | {100 * r['eficiencia']:.1f}% |")

    b_list = sorted(sum_df["b"].unique())
    nrows = len(b_list)
    plt.rcParams.update({"font.size": 12, "axes.titlesize": 13.5, "axes.labelsize": 12.5})
    fig, axes = plt.subplots(nrows, 2, figsize=(13.5, 4.8 * nrows), squeeze=False)

    grid_styles = {
        "1×1": ("#2E5A88", "o", "-"),
        "1×2": ("#E08E2B", "s", "-"),
        "2×1": ("#D35400", "^", "--"),
        "2×2": ("#27AE60", "D", "-"),
        "2×4": ("#8E44AD", "v", "-"),
        "4×2": ("#C0392B", "P", "--"),
    }

    for row_idx, b in enumerate(b_list):
        ax1, ax2 = axes[row_idx]
        bsub = sum_df[sum_df["b"] == b]
        t1_val = t1_map[b]

        ax1.plot([1, 8], [1, 8], ls=":", color="#888888", lw=1.5, label="ideal (S = CPUs)")
        ax2.axhline(100.0, ls=":", color="#888888", lw=1.5, label="ideal (E = 100%)")

        for grid_str in ["1×1", "1×2", "2×1", "2×2", "2×4", "4×2"]:
            gsub = bsub[bsub["grid"] == grid_str].sort_values("cpus")
            if gsub.empty:
                continue
            col, mk, ls = grid_styles.get(grid_str, ("#333333", "o", "-"))
            cfg_num = int(gsub["cfg"].iloc[0])
            lbl = f"C{cfg_num}: {grid_str}"
            ax1.plot(gsub["cpus"], gsub["speedup"], marker=mk, ls=ls, lw=2, ms=7, color=col, label=lbl)
            ax2.plot(gsub["cpus"], gsub["eficiencia"] * 100, marker=mk, ls=ls, lw=2, ms=7, color=col, label=lbl)

        for ax in (ax1, ax2):
            ax.set_xticks([1, 2, 4, 8])
            ax.set_xlabel("CPUs totales (pr × pc × T)")
            ax.grid(axis="y", color="#DDDDDD", lw=0.8)
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(frameon=False, fontsize=10, ncol=2)

        ax1.set_ylabel("Speedup S = T(1) / T(p, T)")
        ax1.set_title(f"Speedup vs CPUs — b = {b} (T(1) = {t1_val:.2f} s)")
        ax1.set_ylim(0, 8.5)

        ax2.set_ylabel("Eficiencia E = S / CPUs [%]")
        ax2.set_title(f"Eficiencia vs CPUs — b = {b}")
        ax2.set_ylim(0, 110)

    fig.suptitle(f"Parte (d): Escalabilidad en 1 nodo ventress (N = {N}, Configuraciones 0 a 3)", fontsize=15, y=1.01)
    fig.tight_layout()
    fig.savefig(args.out, dpi=160, bbox_inches="tight")
    print(f"\nfigura: {args.out}")


if __name__ == "__main__":
    main()
