"""Distribución bloque-cíclica 2D (sin MPI, para poder testearla en serio).

Grid de pr x pc procesos. El bloque A_IJ (de b x b) pertenece al proceso
(I mod pr, J mod pc). Cada proceso guarda sus bloques ordenados por índice
global en UN arreglo local 2D de (nlr*b) x (nlc*b), donde el bloque local
(i, j) es el global (myrow + i*pr, mycol + j*pc).

Consecuencia clave (Figura 2 del enunciado): en el paso k, los bloques de la
submatriz restante (I > k, J > k) forman un sub-arreglo CONTIGUO del arreglo
local: Aloc[i_start*b:, j_start*b:]. La actualización es un solo matmul.
"""
import numpy as np


class BlockCyclic:
    def __init__(self, N, b, pr, pc, myrow, mycol):
        if N % b != 0:
            raise ValueError(f"N={N} debe ser múltiplo de b={b}")
        self.N, self.b, self.pr, self.pc = N, b, pr, pc
        self.myrow, self.mycol = myrow, mycol
        self.nb = N // b                                   # bloques por lado
        self.block_rows = list(range(myrow, self.nb, pr))  # índices globales I que tengo
        self.block_cols = list(range(mycol, self.nb, pc))  # índices globales J que tengo
        self.nlr, self.nlc = len(self.block_rows), len(self.block_cols)

    # --- propiedad / dueños -------------------------------------------------
    @staticmethod
    def owner(I, J, pr, pc):
        return (I % pr, J % pc)

    def owns_block_row(self, I):
        return I % self.pr == self.myrow

    def owns_block_col(self, J):
        return J % self.pc == self.mycol

    # --- índices locales ----------------------------------------------------
    def local_block_row(self, I):
        """Índice local i del bloque-fila global I (requiere owns_block_row)."""
        assert self.owns_block_row(I)
        return (I - self.myrow) // self.pr

    def local_block_col(self, J):
        assert self.owns_block_col(J)
        return (J - self.mycol) // self.pc

    def first_local_row_after(self, k):
        """Cantidad de bloques-fila locales con I <= k. Es el i_start del paso k:
        los bloques-fila locales con I > k son los i >= i_start.
        Es el MISMO valor para todos los procesos de mi fila del grid."""
        return len(range(self.myrow, k + 1, self.pr))

    def first_local_col_after(self, k):
        return len(range(self.mycol, k + 1, self.pc))

    # --- índices globales de filas/columnas que guardo (para matgen) -------
    def global_row_indices(self):
        b = self.b
        return np.concatenate([np.arange(I * b, (I + 1) * b) for I in self.block_rows]) \
            if self.nlr else np.zeros(0, dtype=int)

    def global_col_indices(self):
        b = self.b
        return np.concatenate([np.arange(J * b, (J + 1) * b) for J in self.block_cols]) \
            if self.nlc else np.zeros(0, dtype=int)

    def local_shape(self):
        return (self.nlr * self.b, self.nlc * self.b)

    def blocks(self):
        """Lista [(I, J), ...] de bloques globales que tengo, en orden local."""
        return [(I, J) for I in self.block_rows for J in self.block_cols]

    def __repr__(self):
        return (f"BlockCyclic(N={self.N}, b={self.b}, grid={self.pr}x{self.pc}, "
                f"proc=({self.myrow},{self.mycol}), rows={self.block_rows}, cols={self.block_cols})")
