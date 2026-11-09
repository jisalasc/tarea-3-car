# Plan de trabajo

Integrantes: José Ignacio Salas + 2 compañeros (completar nombres). Computadores: 2 Mac + 1 Windows.
Entrega: **lunes 16 de noviembre 23:59**. Hoy (sábado 7) queda el repo inicializado.

## Estado actual (lo que ya está)
- [x] Entorno reproducible (`environment.yml`: numpy, scipy, mpi4py, matplotlib, pandas). Probado en Mac (Open MPI 5).
- [x] `src/lu_serial.py`: **archivo del curso sin modificar** (copia en `docs/lu_serial_original.py`). Su `matrix_entries(rows, cols, N)` genera cualquier bloque desde índices globales → el distribuido genera sólo sus bloques sin comunicación.
- [x] `scripts/parte_a.py`: wrapper de la parte (a) (1 thread, repeticiones, CSV + metadata del entorno).
- [x] `src/layout.py` + `tests/test_layout.py`: distribución bloque-cíclica validada contra las Figuras 1 y 2 del PDF.
- [x] `src/lu_distributed.py`: **parte (b) implementada y verificada** (`scripts/test_distributed.sh`: 12 grids, diff = 0 vs serial).
- [x] Parte (a) corrida en el Mac de José: mejor b = 1024 (`results/parte_a_mac_jose.csv`, `informe/apuntes/parte_a.txt`).
- [x] Scripts SLURM con los campos obligatorios, planificador de jobs y envío respetando la cola.
- [ ] Nada corrido aún en el cluster. Nadie ha validado todavía `mpirun` multi-nodo en kraken.

## División propuesta (ajustar entre los tres)

### Persona A — núcleo (José Ignacio, parte b + a)
1. ~~Implementar el núcleo~~ hecho (9 nov). `scripts/test_distributed.sh` pasa en 12 casos.
2. ~~Parte (a)~~ hecha (9 nov): b = 1024.
3. Redactar (a) y (b) en el informe a partir de `informe/apuntes/parte_a.txt` y `parte_b.txt`.
4. Apoyar a B con el cluster y a C con los gráficos de (d)–(f).

### Persona B — cluster (configurar temprano, es el riesgo mayor)
1. Acceso a kraken (`ssh kraken`), Miniconda, `conda env create -f environment.yml`, `git clone` del repo.
2. **Validar el primer día**: `sbatch` de `--layout-only` con 1 nodo y con 2 nodos (`--nodes=2`). Si `mpirun` del env conda no levanta procesos en el segundo nodo, probar `srun --mpi=pmix` o el MPI del sistema. Documentar en `slurm/README.md`.
3. Cuando (b) esté listo: `sweep_b.slurm` (parte c) → fijar b del cluster → `plan_jobs.sh` para configs 0–3 (d), 4–5 (e), y parte (f) (grid 2×2, b=4096 y b=512, T=1).
4. Subir los CSV a `results/cluster/` con commits frecuentes. Guardar los `.out` relevantes.

### Persona C — análisis, modelo de costo e informe
1. Parte (g) desde ya (no depende del código): costo en función de N, b, pr, pc con el modelo α (latencia), β (1/ancho de banda), γ (flop). Contar por paso k: 1 Bcast de b² en fila y columna, Bcast de paneles de tamaño (N−kb)·b/pr y b·(N−kb)/pc, flops de lu_factor (2/3 b³), triangulares (b²·(N−kb)/pr, /pc) y matmul (2·b·(N−kb)²/(pr·pc)). Sumar sobre k.
2. Script de gráficos (`scripts/plot.py`, matplotlib) que lea `results/*.csv` y produzca figuras con título, labels, leyenda y fuente grande. Usar **mediana** de las repeticiones. Para (d): speedup = T(1)/T(p), eficiencia = speedup/CPUs totales.
3. `informe/informe.md` → PDF (pandoc o reportlab como en la Tarea 2). Declaración de uso de IA.
4. Revisión cruzada final y `scripts/make_zip.sh`.

## Cronograma
| Fecha | Hito |
|---|---|
| sáb 7 | repo inicializado (hecho) |
| dom 8 – mar 10 | A: (b) con verify PASS + (a). B: cluster listo y multi-nodo validado. C: (g) teórico + plot.py |
| mié 11 – vie 13 | B corre (c) → (d) → (e) → (f). C grafica a medida que llegan CSV. A apoya y arregla bugs |
| sáb 14 – dom 15 | informe completo, revisión cruzada, regenerar figuras |
| lun 16 | zip + PDF a Canvas (no dejar para la noche; 1 job corriendo a la vez) |

## Decisiones de diseño (para que los tres hablemos el mismo idioma)
- **Matriz:** la del curso: `A[i,j] = sin(1e-3·i·j + 0.3·i + 0.7·j)` fuera de la diagonal, `A[i,i] = N`. Dominante por filas y columnas ⇒ `lu_factor` no pivotea (el `assert` del curso lo verifica). Cada proceso llama `matrix_entries(rows, cols, N)` con sus índices globales.
- **Layout local:** un solo arreglo 2D `(nlr·b) × (nlc·b)`, bloque local (i,j) = global `(myrow + i·pr, mycol + j·pc)`. En el paso k la parte restante es `Aloc[i_start·b:, j_start·b:]`.
- **Medición:** `t_comp` = lu_factor + solve_triangular + matmul; `t_comm` = tiempo dentro de los `Bcast` (incluye espera por desbalance; decirlo en el informe). Tiempo del job = máx wall entre procesos tras un `Barrier`.
- **Verificación:** gather de los bloques a rank 0 y comparación elemento a elemento contra `lu_serial.lu_blocked` con la misma A y el mismo b, más residuo `||A − LU||/||A||`. Sólo para N chico (≤ 2048).
- **CSV:** una fila por proceso y repetición (ver `results/README.md`). Nunca borrar resultados; anexar.
- **Oversubscription:** `pr·pc·T ≤ cores físicos`. Local siempre `T=1`. En el cluster T = `$SLURM_CPUS_PER_TASK`.

## Convenciones git
- Ramas por persona/feature (`feat/lu-core`, `feat/cluster`, `feat/informe`), merge a `main` cuando esté probado. Commits chicos y frecuentes; `git pull --rebase` antes de `push`.
- `.gitattributes` fuerza LF (importante para el Windows). En Windows además: `git config --global core.autocrlf input`.
- No subir claves privadas (`.gitignore` ya las excluye). Los `.pub` sí pueden ir.
- `results/` se versiona (son los datos del informe). `slurm/logs/` no.

## Riesgos
1. `mpirun` conda + SLURM multi-nodo (configs 4 y 5). Mitigación: validar el día 1 con `--layout-only`.
2. Cola compartida (1 job corriendo, 15 min): planificar las corridas; (c) va en un solo job.
3. Memoria 4 GB/nodo: N=8192 float64 = 512 MB totales; con `--verify` o `gather` en N grande se revienta → verify sólo local.
4. Windows: mpi4py nativo usa MS-MPI; si da problemas, WSL2 (mismo flujo que Linux/cluster).
