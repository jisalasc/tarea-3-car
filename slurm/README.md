# Scripts SLURM

Todos incluyen los campos obligatorios del enunciado (`--qos`, `--partition`, `--account`) y
fijan `OMP/OPENBLAS/MKL_NUM_THREADS=$SLURM_CPUS_PER_TASK` vía `env.sh`.

| Archivo | Para qué |
|---|---|
| `env.sh` | activa el env conda `tarea3` y fija threads de BLAS (ajustar `CONDA_BASE`) |
| `lu_distributed.slurm` | template genérico: recursos por línea de comando, parámetros por `--export` |
| `lu_serial.slurm` | referencia serial en el cluster (base T(1) de la parte d) |
| `sweep_b.slurm` | parte (c): barrido de b en config 2 con T=2, todo en un job |
| `plan_jobs.sh` | imprime los `sbatch` de la configuración 0..5 de la tabla del enunciado |
| `submit_next.sh` | envía lo que quepa en la cola (límite: 4 encolados, 1 corriendo) |

Flujo típico (desde la raíz del repo, en kraken):

```bash
slurm/plan_jobs.sh 2 256 > slurm/queue.txt     # config 2 con b=256
slurm/plan_jobs.sh 3 256 >> slurm/queue.txt
slurm/submit_next.sh                            # repetir cuando se liberen cupos
squeue -u $USER ; tail -f slurm/logs/*.out
```

Límites por grupo: 8 CPUs y 4 GB por nodo, 15 min por job, 4 en cola, 1 corriendo.
Nodos: `ventress` y `yodaxico`. Documentación: https://cluster.cenia.cl/.

**Pendiente de validar el primer día en el cluster:** que `mpirun` del env conda funcione
dentro de un job de SLURM con 2 nodos (configs 4 y 5). Si no levanta procesos en el
segundo nodo, usar `srun --mpi=pmix python ...` o el MPI del sistema (`module avail`).
