"""Generador determinista de la matriz A (densa, diagonal dominante).

    A[i, j] = U(0, 1)          si i != j
    A[i, i] = U(0, 1) + N

Con esto |A[i,i]| > sum_{j!=i} |A[i,j]| (dominante por filas Y por columnas),
así lu_factor nunca necesita pivotear y la factorización es A = LU sin P.

Cada fila i se genera con su propio generador seedeado con (seed, i). Por eso
cualquier proceso MPI puede construir SOLO las filas/columnas que le tocan y
obtener exactamente los mismos números que la versión serial, sin comunicación
y sin materializar la matriz completa. Esto es lo que permite verificar
lu_distributed.py contra lu_serial.py.
"""
import numpy as np


def row(i, N, seed=0):
    """Fila i completa de A (vector de largo N)."""
    rng = np.random.default_rng([seed, i])
    r = rng.random(N)
    r[i] += N
    return r


def full_matrix(N, seed=0):
    """Matriz A completa N x N (uso serial / verificación)."""
    A = np.empty((N, N))
    for i in range(N):
        A[i] = row(i, N, seed)
    return A


def local_rows(rows, col_idx, N, seed=0):
    """Submatriz A[rows][:, col_idx] generada fila a fila.

    rows:    índices globales de fila (en el orden en que se guardan localmente)
    col_idx: índices globales de columna (idem)
    Memoria temporal: una fila (N floats), independiente de b.
    """
    out = np.empty((len(rows), len(col_idx)))
    for li, i in enumerate(rows):
        out[li] = row(i, N, seed)[col_idx]
    return out
