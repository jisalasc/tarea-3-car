# Tarea 3 — IIC3533 Computación de Alto Rendimiento (2026-2)

**Fuente de verdad: [`docs/tarea03.pdf`](tarea03.pdf).** Esto es un resumen operativo; ante cualquier duda manda el PDF.

- Grupos de **3 personas**. Pruebas iniciales en computador personal; experimentos principales en el cluster.
- **Entrega: lunes 16 de noviembre de 2026, 23:59**, por Canvas: un `.zip` con los **scripts SLURM** y un **PDF** con resultados.
- IA permitida **si se declara en el informe**. Se evalúa claridad de gráficos/tablas (títulos, labels, leyendas, tamaño de fuente).

## El problema: LU distribuida con mpi4py

Factorizar `A = LU` (A densa N×N, **diagonal dominante** ⇒ sin pivoteo, no hay `P`), L unitaria inferior, U superior, O(N³).
Implementación sobre un **grid 2D de procesos MPI** con NumPy/SciPy para el cómputo local.

### LU por bloques (serial)
A en bloques b×b, nb = N/b. Para k = 0..nb-1:
1. Factorizar bloque diagonal `A_kk = L_kk U_kk` → `scipy.linalg.lu_factor`.
2. Paneles: `U_kj = L_kk⁻¹ A_kj` (j>k) y `L_ik = A_ik U_kk⁻¹` (i>k) → `scipy.linalg.solve_triangular`.
3. Actualizar `A_ij ← A_ij − L_ik U_kj` (i,j>k) → `@` de NumPy.

Los factores se guardan sobre la misma matriz (in-place).

### Distribución bloque-cíclica
```python
pr, pc = MPI.Compute_dims(size, 2)
myrow, mycol = rank // pc, rank % pc
row_comm = comm.Split(myrow, mycol)   # procesos de mi fila del grid
col_comm = comm.Split(mycol, myrow)   # procesos de mi columna del grid
```
Bloque `A_IJ` pertenece al proceso `(I mod pr, J mod pc)` ("repartidos como cartas").
Ejemplo (Figura 1): 6×6 bloques en grid 2×3 → el proceso (0,1) guarda A01 A04 A21 A24 A41 A44.
Los bloques locales se guardan **ordenados por índice global** ⇒ la submatriz restante del paso k es un
**sub-arreglo contiguo** del arreglo local ⇒ la actualización es **una sola multiplicación**.

### Paso k distribuido (caso general), con (r, c) = (k mod pr, k mod pc) el dueño de A_kk
1. **Bloque diagonal.** (r,c) factoriza A_kk y lo difunde en su fila (`row_comm`) y en su columna (`col_comm`).
2. **Panel de U.** Procesos de la fila r calculan sus `U_kj`, j>k.
3. **Panel de L.** Procesos de la columna c calculan sus `L_ik`, i>k.
4. **Envío de paneles.** En cada fila del grid, el proceso de la columna c difunde sus `L_ik` (`row_comm`).
   En cada columna del grid, el proceso de la fila r difunde sus `U_kj` (`col_comm`).
5. **Actualización.** Todos actualizan sus `A_ij`, i,j>k, con un matmul.

Ejemplo k=2 (Figura 2, grid 2×3): A22 ∈ (0,2) → se factoriza y va a (0,0),(0,1) [fila] y (1,2) [columna].
U23,U24,U25 ∈ (0,0),(0,1),(0,2). L32,L52 ∈ (1,2) y L42 ∈ (0,2). (1,1) tiene A34 y A54, recibe L32,L52 de (1,2) y U24 de (0,1).

## Cluster (kraken)
- Docs: https://cluster.cenia.cl/ (ejemplos de `sbatch`/SLURM). Se recomienda **Miniconda**.
- Acceso (`~/.ssh/config`, `<n>` = número del grupo), luego `ssh kraken`:
  ```
  Host kraken
      HostName kraken.ing.puc.cl
      Port 33052
      User grupo<n>-iic3533
  ```
- Todo job DEBE incluir (si no, no corre):
  ```
  #SBATCH --qos=hpc-iic3533
  #SBATCH --partition=hpc-iic3533
  #SBATCH --account=default-account
  ```
- Por configuración: `--ntasks` (p = pr×pc), `--cpus-per-task` (T), `--nodes`, `--ntasks-per-node`.
- Dentro del job: `SLURM_NTASKS` (→ `mpirun -n`), `SLURM_CPUS_PER_TASK`;
  **`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` deben fijarse en `$SLURM_CPUS_PER_TASK`.**
- Nodos de la partición: `ventress`, `yodaxico`.
- **Límites por grupo:** máx **8 CPUs por nodo y 4 GB RAM**; job máx **15 min**; máx **4 jobs en cola y 1 en ejecución**.

### Configuraciones de los experimentos (T = threads por proceso)

| Config | pr×pc | T | Nodos | Procesos/nodo | CPUs totales |
|---|---|---|---|---|---|
| 0 | 1×1 | 1, 2, 4, 8 | 1 | 1 | 1, 2, 4, 8 |
| 1 | 1×2, 2×1 | 1, 2, 4 | 1 | 2 | 2, 4, 8 |
| 2 | 2×2 | 1, 2 | 1 | 4 | 4, 8 |
| 3 | 2×4, 4×2 | 1 | 1 | 8 | 8 |
| 4 | 2×4 | 1 | 2 | 4 | 8 |
| 5 | 4×4 | 1 | 2 | 8 | 16 |

## Preguntas (100 pts)

| | pts | Qué hay que hacer | Dónde | Entregable |
|---|---|---|---|---|
| (a) | 10 | `lu_serial.py`, N=2¹²=4096, **1 thread**, b ∈ {2¹²,2¹¹,…,2⁶} = {4096,…,64}. Elegir b apropiado. | PC personal | tabla/gráfico + b elegido |
| (b) | 20 | Implementar `lu_distributed.py(N, b, pr, pc)`; medir **por separado** cómputo y comunicación **de cada proceso**. Explicar qué colectiva usa cada paso, en qué comunicador y con qué raíz. **Verificar correctitud vs serial** y explicar cómo. Cuidado con **oversubscription**. | PC → cluster | código + explicación |
| (c) | 10 | N=2¹³=8192, repetir barrido de b de (a) en **config 2 con T=2**. ¿Sigue siendo el mejor b de (a)? | cluster | tabla/gráfico |
| (d) | 20 | N=2¹³, con los b de (a) y (c), **configs 0 a 3**. Speedup y eficiencia; **justificar la elección de T(1)**. ¿Mejor config? ¿Afecta la forma del grid? | cluster | tabla/gráfico |
| (e) | 15 | N=2¹³, b de (a) y (c), **configs 4 y 5**. Comparar config 4 vs config 3 (mismo grid 2×4, 1 nodo) separando cómputo y comunicación; relacionar con **latencia y ancho de banda** intra vs inter nodo. | cluster | tabla/gráfico |
| (f) | 15 | Grid **2×2**, comparar **b=N/2** y **b=N/16**, separando cómputo y comunicación **de cada proceso**. Explicar. | cluster | tabla/gráfico |
| (g) | 10 | Modelo de costo (α, β, γ): costo total en función de N, b, pr, pc. ¿Qué términos explican el b óptimo? ¿Cuál es el cuello de botella según las mediciones? | papel | derivación + contraste con datos |

## Dependencias entre partes
- (a) es independiente (sólo serial).
- (b) es el **camino crítico**: (c), (d), (e), (f) necesitan `lu_distributed.py` correcto.
- (c) fija el b del cluster que usan (d) y (e). (f) y (g) usan las mediciones de cómputo/comunicación por proceso.
