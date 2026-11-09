#!/usr/bin/env python
"""Parte (a): barrido de b con lu_serial.py (archivo del curso, SIN modificar), N=2^12, 1 thread.

Uso:
    python scripts/parte_a.py                       # N=4096, b=4096..64, 3 repeticiones, 1 thread
    python scripts/parte_a.py --reps 5 --check      # --check calcula el residuo (1 vez por b)
Salida: results/parte_a_<host>.csv (anexa) y results/parte_a_<host>_meta.json (entorno).
Las repeticiones son el loop EXTERNO (rep0: todos los b, rep1: todos los b, ...) para que el
calentamiento/throttling no castigue siempre al mismo b.
"""
import argparse
import csv
import json
import os
import platform
import socket
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def _threads_early():
    t = "1"
    for i, a in enumerate(sys.argv):
        if a == "--threads" and i + 1 < len(sys.argv):
            t = sys.argv[i + 1]
        elif a.startswith("--threads="):
            t = a.split("=", 1)[1]
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
        os.environ[v] = t


_threads_early()

import numpy as np  # noqa: E402
import scipy  # noqa: E402
from threadpoolctl import threadpool_info  # noqa: E402

sys.path.insert(0, os.path.join(ROOT, "src"))
from lu_serial import lu_blocked, matrix_entries, residual  # noqa: E402


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--N", type=int, default=4096)
    p.add_argument("--b", type=int, nargs="+", default=[4096, 2048, 1024, 512, 256, 128, 64])
    p.add_argument("--reps", type=int, default=3)
    p.add_argument("--threads", type=int, default=1)
    p.add_argument("--check", action="store_true")
    p.add_argument("--tag", default=socket.gethostname().split(".")[0])
    args = p.parse_args()

    blas = [i for i in threadpool_info() if i.get("user_api") == "blas"]
    blas_threads = max((i["num_threads"] for i in blas), default=-1)
    out = os.path.join(ROOT, "results", f"parte_a_{args.tag}.csv")
    meta = os.path.join(ROOT, "results", f"parte_a_{args.tag}_meta.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(meta, "w") as f:
        json.dump({"host": platform.node(), "platform": platform.platform(), "machine": platform.machine(),
                   "cpu_count_logical": os.cpu_count(), "python": platform.python_version(),
                   "numpy": np.__version__, "scipy": scipy.__version__, "blas": blas,
                   "env_threads": {k: os.environ.get(k) for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
                   "N": args.N, "b_list": args.b, "reps": args.reps, "ts": time.strftime("%Y-%m-%dT%H:%M:%S")},
                  f, indent=2, default=str)
    print(f"N={args.N} threads(BLAS)={blas_threads} reps={args.reps} -> {out}", flush=True)

    idx = np.arange(args.N)
    A0 = matrix_entries(idx, idx, args.N)
    fields = ["N", "b", "threads", "rep", "time_s", "gflops", "checksum", "residual", "host", "ts"]
    new = not os.path.exists(out)
    with open(out, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        if new:
            w.writeheader()
        for rep in range(args.reps):
            for b in args.b:
                A = A0.copy()
                t0 = time.perf_counter()
                lu_blocked(A, b)
                t = time.perf_counter() - t0
                res = residual(A0, A) if (args.check and rep == 0) else float("nan")
                row = {"N": args.N, "b": b, "threads": blas_threads, "rep": rep, "time_s": f"{t:.6f}",
                       "gflops": f"{2 * args.N**3 / 3 / t / 1e9:.2f}", "checksum": f"{A.sum():.6e}",
                       "residual": f"{res:.3e}", "host": platform.node(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S")}
                w.writerow(row)
                f.flush()
                print(" ".join(f"{k}={v}" for k, v in row.items() if k not in ("host",)), flush=True)


if __name__ == "__main__":
    main()
