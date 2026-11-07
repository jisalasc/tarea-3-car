"""Verifica la distribución bloque-cíclica contra las Figuras 1 y 2 del enunciado.

Correr:  python tests/test_layout.py      (también funciona con pytest)
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
from layout import BlockCyclic  # noqa: E402

PR, PC, NB, B = 2, 3, 6, 4  # Figura 1: 6x6 bloques en un grid 2x3
N = NB * B


def test_figura1_proceso_01():
    bc = BlockCyclic(N, B, PR, PC, myrow=0, mycol=1)
    assert bc.blocks() == [(0, 1), (0, 4), (2, 1), (2, 4), (4, 1), (4, 4)]
    assert bc.local_shape() == (3 * B, 2 * B)


def test_todos_los_bloques_tienen_un_unico_dueno():
    seen = {}
    for r in range(PR):
        for c in range(PC):
            for blk in BlockCyclic(N, B, PR, PC, r, c).blocks():
                assert blk not in seen, f"bloque {blk} repetido"
                seen[blk] = (r, c)
    assert len(seen) == NB * NB
    for (I, J), who in seen.items():
        assert who == BlockCyclic.owner(I, J, PR, PC)


def test_figura2_paso_k2():
    k = 2
    assert BlockCyclic.owner(k, k, PR, PC) == (0, 2)                      # A22 -> (0,2)
    assert [BlockCyclic.owner(k, j, PR, PC) for j in (3, 4, 5)] == [(0, 0), (0, 1), (0, 2)]   # U23 U24 U25
    assert BlockCyclic.owner(3, k, PR, PC) == (1, 2) and BlockCyclic.owner(5, k, PR, PC) == (1, 2)  # L32 L52
    assert BlockCyclic.owner(4, k, PR, PC) == (0, 2)                      # L42
    # proceso (1,1) tiene A34 y A54 en la submatriz restante
    bc = BlockCyclic(N, B, PR, PC, 1, 1)
    i0, j0 = bc.first_local_row_after(k), bc.first_local_col_after(k)
    rest = [(I, J) for I in bc.block_rows[i0:] for J in bc.block_cols[j0:]]
    assert rest == [(3, 4), (5, 4)]
    # y el sub-arreglo restante es contiguo: filas locales desde i0*b, columnas desde j0*b
    assert (i0, j0) == (1, 1)


def test_i_start_es_igual_en_toda_la_fila_del_grid():
    for k in range(NB):
        for r in range(PR):
            vals = {BlockCyclic(N, B, PR, PC, r, c).first_local_row_after(k) for c in range(PC)}
            assert len(vals) == 1
        for c in range(PC):
            vals = {BlockCyclic(N, B, PR, PC, r, c).first_local_col_after(k) for r in range(PR)}
            assert len(vals) == 1


def test_indices_globales():
    bc = BlockCyclic(N, B, PR, PC, 0, 1)
    rows = bc.global_row_indices().tolist()
    assert rows == list(range(0, B)) + list(range(2 * B, 3 * B)) + list(range(4 * B, 5 * B))
    cols = bc.global_col_indices().tolist()
    assert cols == list(range(B, 2 * B)) + list(range(4 * B, 5 * B))


if __name__ == "__main__":
    g = dict(globals())
    for name, fn in g.items():
        if name.startswith("test_") and callable(fn):
            fn()
            print("OK ", name)
    print("Todos los tests de layout pasaron.")
