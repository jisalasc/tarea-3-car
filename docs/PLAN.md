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
- [x] Cluster validado (9 nov): Miniconda + env `tarea3` instalados en la cuenta del grupo, `srun --mpi=pmix` funciona en 1 y 2 nodos, `--threads-per-core=1` da 8 cores físicos. Ver `slurm/README.md` y `informe/apuntes/cluster.txt`.
- [x] Parte (c) corrida (job 37838): **b = 512** (`results/cluster/parte_c.csv`, `informe/figuras/parte_c.png`, `informe/apuntes/parte_c.txt`).

## División propuesta (ajustar entre los tres)

### Persona A — núcleo (José Ignacio, partes a, b, c + validación del cluster)
1. ~~Implementar el núcleo~~ hecho (9 nov). `scripts/test_distributed.sh` pasa en 12 casos.
2. ~~Parte (a)~~ hecha (9 nov): b = 1024.
3. ~~Cluster y parte (c)~~ hecho (9 nov): b = 512.
4. Redactar (a), (b) y (c) en el informe a partir de `informe/apuntes/parte_a.txt`, `parte_b.txt`, `parte_c.txt` y `cluster.txt`.
5. Apoyar a B con el cluster y a C con los gráficos de (d)–(f).

### Persona B — cluster: partes (d), (e), (f)
1. Acceso a kraken con sus credenciales. El entorno ya está instalado en la cuenta del grupo (`~/miniconda3`, env `tarea3`, repo en `~/tarea-3-car`): sólo `cd ~/tarea-3-car && git pull`.
2. ~~Validar multi-nodo~~ hecho. Leer `slurm/README.md` (qué aprendimos: `--comment`, `--mem=4G`, `--threads-per-core=1`, nodos distintos, lanzador `srun --mpi=pmix`).
3. Con **b = 512**: `slurm/plan_jobs.sh 0 512 > slurm/queue.txt`, luego configs 1, 2, 3 (parte d), 4 y 5 (parte e), y parte (f) (grid 2×2, T=1, b=4096 y b=512, 1 nodo). `slurm/submit_next.sh` respeta la cola. Un job de config 2 tarda ~10 s por repetición; todo (d)+(e)+(f) cabe en una tarde.
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
1. ~~`mpirun` conda + SLURM multi-nodo~~ resuelto: `srun --mpi=pmix` validado en 2 nodos (9 nov).
2. Cola compartida (1 job corriendo, 15 min): planificar las corridas; (c) va en un solo job.
3. Memoria 4 GB/nodo: N=8192 float64 = 512 MB totales; con `--verify` o `gather` en N grande se revienta → verify sólo local.
4. Windows: mpi4py nativo usa MS-MPI; si da problemas, WSL2 (mismo flujo que Linux/cluster).
