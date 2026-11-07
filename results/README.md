# Resultados

Nunca se sobreescriben: los scripts **anexan** filas. Usar la **mediana** por configuración en el informe.

| Archivo | Origen |
|---|---|
| `parte_a_<host>.csv` | `scripts/run_parte_a.sh` (serial, PC personal) |
| `cluster/serial.csv` | `slurm/lu_serial.slurm` (base T(1)) |
| `cluster/parte_c.csv` | `slurm/sweep_b.slurm` |
| `cluster/config{0..5}.csv` | `slurm/plan_jobs.sh` + `submit_next.sh` |
| `cluster/parte_f.csv` | grid 2×2, b=4096 y b=512 |

## Columnas de `lu_serial.py`
`N, b, threads, rep, time_s, residual, host, ts`

## Columnas de `lu_distributed.py` (una fila por proceso y repetición)
`N, b, pr, pc, threads, nodes, tasks_per_node, rank, myrow, mycol, host, rep, t_comp, t_comm, t_wall, t_max, job`

- `t_comp`: segundos en lu_factor / solve_triangular / matmul del proceso.
- `t_comm`: segundos dentro de los Bcast del proceso (incluye espera).
- `t_wall`: wall del proceso; `t_max`: máximo de `t_wall` entre procesos (= tiempo de la corrida).
