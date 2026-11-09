#!/usr/bin/env python
"""LU por bloques distribuida sobre un grid pr x pc de procesos MPI. Parte (b).

Uso:
    mpirun -n 4 python src/lu_distributed.py --N 1024 --b 128 --pr 2 --pc 2 --threads 1 --verify
    mpirun -n 6 python src/lu_distributed.py --N 24 --b 4 --pr 2 --pc 3 --layout-only   # Figura 1
    mpirun -n $SLURM_NTASKS python src/lu_distributed.py --N 8192 --b 256 --pr 2 --pc 2 \
        --threads $SLURM_CPUS_PER_TASK --out results/cluster/config2.csv

ESTADO: infraestructura lista (grid, comunicadores, distribución bloque-cíclica,
generación local de A, cronómetros cómputo/comunicación, verificación contra
lu_serial.py, salida CSV). El NÚCLEO del paso k está marcado con TODO en
lu_distributed(). Ver docs/ENUNCIADO.md ("Paso k distribuido") y docs/PLAN.md.

Convención de medición (hay que explicarla en el informe):
    t_comp: tiempo en lu_factor / solve_triangular / @ (cómputo local).
    t_comm: tiempo dentro de las operaciones colectivas (Bcast). Incluye la
            espera por desbalance de carga, así que es "comunicación + espera".
    Cada proceso reporta sus propios t_comp y t_comm; el tiempo total del job
    es el máximo del wall-time entre procesos (hay un Barrier antes de partir).
"""
import argparse
import csv
import os
import platform
import sys


def _set_blas_threads_early():
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
from mpi4py import MPI  # noqa: E402
from scipy.linalg import lu_factor, solve_triangular  # noqa: E402,F401

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import BlockCyclic  # noqa: E402
from lu_serial import matrix_entries  # noqa: E402  (archivo del curso: misma matriz que la versión serial)


# ----------------------------------------------------------------------------
# Grid de procesos y comunicadores (tal cual el enunciado)
# ----------------------------------------------------------------------------
class Grid:
    def __init__(self, comm, pr=None, pc=None):
        self.comm = comm
        self.rank, self.size = comm.Get_rank(), comm.Get_size()
        if pr is None or pc is None:
            pr, pc = MPI.Compute_dims(self.size, 2)
        if pr * pc != self.size:
            raise ValueError(f"pr*pc={pr}*{pc} != número de procesos {self.size}")
        self.pr, self.pc = pr, pc
        self.myrow, self.mycol = self.rank // pc, self.rank % pc
        # row_comm: los pc procesos de mi fila del grid; mi rank ahí es mycol.
        # col_comm: los pr procesos de mi columna del grid; mi rank ahí es myrow.
        self.row_comm = comm.Split(self.myrow, self.mycol)
        self.col_comm = comm.Split(self.mycol, self.myrow)


class Timers:
    """Acumula tiempo de cómputo y de comunicación con MPI.Wtime()."""

    def __init__(self):
        self.comp = 0.0
        self.comm = 0.0

    class _Section:
        def __init__(self, timers, attr):
            self.timers, self.attr = timers, attr

        def __enter__(self):
            self.t0 = MPI.Wtime()

        def __exit__(self, *exc):
            setattr(self.timers, self.attr, getattr(self.timers, self.attr) + MPI.Wtime() - self.t0)

    def computing(self):
        return Timers._Section(self, "comp")

    def communicating(self):
        return Timers._Section(self, "comm")


# ----------------------------------------------------------------------------
# Núcleo: paso k distribuido
# ----------------------------------------------------------------------------
def lu_distributed(Aloc, bc, grid, tm):
    """Factoriza in-place el arreglo local Aloc según la distribución bc.

    Al terminar, cada bloque local contiene su L_IJ (I > J), U_IJ (I < J) o
    L_II / U_II empaquetados (I == J), igual que lu_serial.lu_blocked.
    """
    b, nb = bc.b, bc.nb
    for k in range(nb):
        r, c = k % grid.pr, k % grid.pc           # proceso dueño de A_kk
        in_row_r, in_col_c = grid.myrow == r, grid.mycol == c
        i_start = bc.first_local_row_after(k)     # bloques-fila locales con I > k: i >= i_start
        j_start = bc.first_local_col_after(k)     # bloques-col locales con J > k: j >= j_start
        # Offsets (en elementos) dentro de Aloc:
        #   bloque A_kk local (sólo si in_row_r and in_col_c): [lk*b:(lk+1)*b, lc*b:(lc+1)*b]
        #   panel U (fila r): Aloc[lk*b:(lk+1)*b, j_start*b:]       (b x (nlc-j_start)*b)
        #   panel L (col c):  Aloc[i_start*b:, lc*b:(lc+1)*b]       ((nlr-i_start)*b x b)
        #   restante:         Aloc[i_start*b:, j_start*b:]
        lk = bc.local_block_row(k) if in_row_r else None
        lc = bc.local_block_col(k) if in_col_c else None

        # TODO(parte b) 1. Bloque diagonal: (r,c) factoriza A_kk (lu_factor, verificar
        #    piv == arange) y lo difunde: row_comm.Bcast(Akk, root=c) entre los procesos
        #    de la fila r; col_comm.Bcast(Akk, root=r) entre los de la columna c.
        #    Los procesos que no están ni en la fila r ni en la columna c no lo necesitan.
        #    (Ojo: Bcast es colectivo sobre TODO el comunicador; row_comm de la fila r
        #    sólo contiene procesos de esa fila, así que sólo ellos lo llaman.)
        #
        # TODO(parte b) 2. Panel de U (procesos de la fila r, con bloques J > k):
        #    U_kj = L_kk^{-1} A_kj  -> solve_triangular(Akk, panel, lower=True, unit_diagonal=True)
        #    sobre Aloc[lk*b:(lk+1)*b, j_start*b:] en UNA llamada.
        #
        # TODO(parte b) 3. Panel de L (procesos de la columna c, con bloques I > k):
        #    L_ik = A_ik U_kk^{-1}  -> solve_triangular(Akk, panel.T, lower=False, trans='T').T
        #    sobre Aloc[i_start*b:, lc*b:(lc+1)*b] en UNA llamada.
        #
        # TODO(parte b) 4. Envío de paneles:
        #    - En cada fila del grid, el proceso de la columna c difunde su panel L
        #      (bloques L_ik con I > k, apilados): row_comm.Bcast(Lpanel, root=c).
        #      Todos los procesos de la misma fila tienen el MISMO i_start (test_layout),
        #      así que el receptor sabe el tamaño: ((nlr - i_start)*b, b).
        #    - En cada columna del grid, el proceso de la fila r difunde su panel U:
        #      col_comm.Bcast(Upanel, root=r). Tamaño (b, (nlc - j_start)*b).
        #    Si el panel es vacío (i_start == nlr), Bcast de un arreglo de 0 elementos.
        #
        # TODO(parte b) 5. Actualización (todos): Aloc[i_start*b:, j_start*b:] -= Lpanel @ Upanel
        #
        # Envolver 1,2,3,5 en `with tm.computing():` y los Bcast en `with tm.communicating():`.
        raise NotImplementedError("Parte (b): implementar los pasos 1-5 del paso k (ver TODOs)")
    return Aloc


# ----------------------------------------------------------------------------
# Utilidades: construcción local, gather global, verificación, salida
# ----------------------------------------------------------------------------
def build_local(bc):
    """Bloques locales generados directamente desde los índices globales (sin comunicación)."""
    rows, cols = bc.global_row_indices(), bc.global_col_indices()
    return matrix_entries(rows, cols, bc.N)


def gather_global(Aloc, bc, grid):
    """Reconstruye la matriz N x N en rank 0 (sólo para N chico / verificación)."""
    pieces = grid.comm.gather((bc.block_rows, bc.block_cols, Aloc), root=0)
    if grid.rank != 0:
        return None
    b = bc.b
    G = np.empty((bc.N, bc.N))
    for brows, bcols, A in pieces:
        for i, I in enumerate(brows):
            for j, J in enumerate(bcols):
                G[I * b:(I + 1) * b, J * b:(J + 1) * b] = A[i * b:(i + 1) * b, j * b:(j + 1) * b]
    return G


def verify(Aloc, bc, grid, tol=1e-8):
    """Compara contra lu_serial.lu_blocked (archivo del curso) con la MISMA matriz y el MISMO b."""
    from lu_serial import lu_blocked, residual
    G = gather_global(Aloc, bc, grid)
    ok = None
    if grid.rank == 0:
        idx = np.arange(bc.N)
        A0 = matrix_entries(idx, idx, bc.N)
        LU_ser = A0.copy()
        lu_blocked(LU_ser, bc.b)
        diff = float(np.max(np.abs(G - LU_ser)) / np.max(np.abs(LU_ser)))
        res = residual(A0, G)
        ok = diff < tol and res < tol
        print(f"[verify] max|dist-serial|/max|serial| = {diff:.2e}   ||A-LU||/||A|| = {res:.2e}   "
              f"-> {'PASS' if ok else 'FAIL'}", flush=True)
    return grid.comm.bcast(ok, root=0)


def print_layout(bc, grid):
    lines = grid.comm.gather(f"rank {grid.rank} = proc ({grid.myrow},{grid.mycol}): bloques {bc.blocks()}  "
                             f"shape local {bc.local_shape()}", root=0)
    if grid.rank == 0:
        print(f"N={bc.N} b={bc.b} nb={bc.nb} grid={grid.pr}x{grid.pc}")
        print("\n".join(lines), flush=True)


def write_csv(path, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        if new:
            w.writeheader()
        w.writerows(rows)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--N", type=int, required=True)
    p.add_argument("--b", type=int, required=True)
    p.add_argument("--pr", type=int, default=None)
    p.add_argument("--pc", type=int, default=None)
    p.add_argument("--threads", type=int, default=None, help="threads de BLAS por proceso (T)")
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--verify", action="store_true", help="compara con lu_serial (sólo N chico)")
    p.add_argument("--layout-only", action="store_true", help="imprime la distribución y sale")
    p.add_argument("--out", default=None, help="CSV: una fila por proceso y repetición")
    args = p.parse_args()

    grid = Grid(MPI.COMM_WORLD, args.pr, args.pc)
    bc = BlockCyclic(args.N, args.b, grid.pr, grid.pc, grid.myrow, grid.mycol)
    if args.layout_only:
        print_layout(bc, grid)
        return

    T = int(os.environ.get("OMP_NUM_THREADS", args.threads or -1))
    nodes = int(os.environ.get("SLURM_JOB_NUM_NODES", 1))
    tpn = int(os.environ.get("SLURM_NTASKS_PER_NODE", grid.size))
    A0 = build_local(bc)

    for rep in range(args.reps):
        Aloc = A0.copy()
        tm = Timers()
        grid.comm.Barrier()
        t0 = MPI.Wtime()
        lu_distributed(Aloc, bc, grid, tm)
        t_wall = MPI.Wtime() - t0
        t_max = grid.comm.allreduce(t_wall, op=MPI.MAX)

        if args.verify and rep == 0:
            if not verify(Aloc, bc, grid):
                grid.comm.Abort(1)

        row = {
            "N": args.N, "b": args.b, "pr": grid.pr, "pc": grid.pc, "threads": T, "nodes": nodes,
            "tasks_per_node": tpn, "rank": grid.rank, "myrow": grid.myrow, "mycol": grid.mycol,
            "host": platform.node(), "rep": rep, "t_comp": f"{tm.comp:.6f}", "t_comm": f"{tm.comm:.6f}",
            "t_wall": f"{t_wall:.6f}", "t_max": f"{t_max:.6f}", "job": os.environ.get("SLURM_JOB_ID", ""),
        }
        rows = grid.comm.gather(row, root=0)
        if grid.rank == 0:
            print(f"N={args.N} b={args.b} grid={grid.pr}x{grid.pc} T={T} rep={rep} t_max={t_max:.4f}s  "
                  + "  ".join(f"r{r['rank']}:comp={float(r['t_comp']):.3f}/comm={float(r['t_comm']):.3f}" for r in rows),
                  flush=True)
            if args.out:
                write_csv(args.out, rows)


if __name__ == "__main__":
    main()
