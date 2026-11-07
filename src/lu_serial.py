#!/usr/bin/env python
"""LU por bloques, serial, in-place, sin pivoteo (A diagonal dominante). Parte (a).

Uso:
    python src/lu_serial.py --N 4096 --b 256 --threads 1 [--reps 3] [--check] [--out results/parte_a.csv]

Algoritmo (enunciado, sección "LU por bloques"), con nb = N/b bloques por lado:
    para k = 0 .. nb-1:
        1. A_kk = L_kk U_kk                       -> scipy.linalg.lu_factor
        2. U_kj = L_kk^{-1} A_kj  (j > k)         -> scipy.linalg.solve_triangular
           L_ik = A_ik U_kk^{-1}  (i > k)         -> scipy.linalg.solve_triangular
        3. A_ij <- A_ij - L_ik U_kj  (i, j > k)   -> producto @ de NumPy
Los factores quedan sobre A: L estricta bajo la diagonal (diag implícita = 1), U en y sobre la diagonal.
"""
import argparse
import csv
import os
import platform
import sys
import time


def _set_blas_threads_early():
    """Fija los threads de BLAS ANTES de importar numpy (después ya no tiene efecto)."""
    t = None
    for i, a in enumerate(sys.argv):
        if a == "--threads" and i + 1 < len(sys.argv):
            t = sys.argv[i + 1]
        elif a.startswith("--threads="):
            t = a.split("=", 1)[1]
    if t is not None:
        for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[v] = str(t)


_set_blas_threads_early()

import numpy as np  # noqa: E402
from scipy.linalg import lu_factor, solve_triangular  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import matgen  # noqa: E402


def lu_blocked(A, b):
    """Factoriza A in-place por bloques de b x b. Devuelve A (con L y U encima)."""
    N = A.shape[0]
    if N % b != 0:
        raise ValueError(f"N={N} debe ser múltiplo de b={b}")
    nb = N // b
    for k in range(nb):
        k0, k1 = k * b, (k + 1) * b
        # 1. bloque diagonal
        lu, piv = lu_factor(A[k0:k1, k0:k1], check_finite=False)
        if not np.array_equal(piv, np.arange(b)):
            raise RuntimeError(f"lu_factor pivoteó en el paso k={k}: la matriz no es diagonal dominante")
        A[k0:k1, k0:k1] = lu
        if k1 == N:
            break
        # 2. paneles. U_kj = L_kk^{-1} A_kj  (L_kk unitaria inferior, está en 'lu')
        A[k0:k1, k1:] = solve_triangular(lu, A[k0:k1, k1:], lower=True, unit_diagonal=True, check_finite=False)
        #    L_ik = A_ik U_kk^{-1}  <=>  U_kk^T L_ik^T = A_ik^T   (trans='T' resuelve con la traspuesta)
        A[k1:, k0:k1] = solve_triangular(lu, A[k1:, k0:k1].T, lower=False, trans="T", check_finite=False).T
        # 3. actualización de la submatriz restante
        A[k1:, k1:] -= A[k1:, k0:k1] @ A[k0:k1, k1:]
    return A


def split_lu(LU):
    """Separa L (unitaria inferior) y U (superior) del arreglo in-place."""
    L = np.tril(LU, -1) + np.eye(LU.shape[0])
    U = np.triu(LU)
    return L, U


def residual(A0, LU):
    """||A0 - L U||_F / ||A0||_F"""
    L, U = split_lu(LU)
    return float(np.linalg.norm(A0 - L @ U) / np.linalg.norm(A0))


def blas_threads_in_use():
    try:
        from threadpoolctl import threadpool_info
        infos = [i for i in threadpool_info() if i.get("user_api") == "blas"]
        return max((i["num_threads"] for i in infos), default=-1)
    except Exception:  # pragma: no cover
        return -1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--N", type=int, required=True)
    p.add_argument("--b", type=int, required=True)
    p.add_argument("--threads", type=int, default=None, help="threads de BLAS (fija OMP/OPENBLAS/MKL_NUM_THREADS)")
    p.add_argument("--reps", type=int, default=1, help="repeticiones (se reportan todas; usar mediana en el informe)")
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--check", action="store_true", help="calcula el residuo ||A-LU||/||A|| (costo O(N^3) extra)")
    p.add_argument("--out", default=None, help="CSV al que se anexa una fila por repetición")
    args = p.parse_args()

    threads = blas_threads_in_use()
    A0 = matgen.full_matrix(args.N, args.seed)
    for rep in range(args.reps):
        A = A0.copy()
        t0 = time.perf_counter()
        lu_blocked(A, args.b)
        t = time.perf_counter() - t0
        res = residual(A0, A) if args.check else float("nan")
        rowd = {
            "N": args.N, "b": args.b, "threads": threads, "rep": rep, "time_s": f"{t:.6f}",
            "residual": f"{res:.3e}", "host": platform.node(), "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
        }
        print(" ".join(f"{k}={v}" for k, v in rowd.items()), flush=True)
        if args.out:
            os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
            new = not os.path.exists(args.out)
            with open(args.out, "a", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rowd))
                if new:
                    w.writeheader()
                w.writerow(rowd)


if __name__ == "__main__":
    main()
