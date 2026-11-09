# Scripts SLURM

Todos incluyen los campos obligatorios del enunciado (`--qos`, `--partition`, `--account`), el
`--comment` descriptivo que exige kraken (sin él `sbatch` rechaza el job), `--mem=4G` (sin él
SLURM pide 233 GB y el job queda pendiente para siempre con `MaxMemPerLimit`) y
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

## Entorno en kraken (ya instalado en la cuenta del grupo)

kraken no trae `mpi4py` ni `module`; el enunciado recomienda Miniconda. Ya está instalado
en `~/miniconda3` con el env `tarea3` creado desde `environment.yml`, y el repo clonado en
`~/tarea-3-car`. Para usarlo basta con `git pull` y lanzar los `sbatch`.

Si hay que recrearlo desde cero:

```bash
cd ~ && wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh
bash miniconda.sh -b -p $HOME/miniconda3 && rm miniconda.sh
source ~/miniconda3/etc/profile.d/conda.sh
# Solo conda-forge: con el canal `defaults` conda exige aceptar los Terms of Service de Anaconda.
# El instalador deja ~/miniconda3/.condarc con `defaults`; hay que sobrescribir ambos archivos.
printf "channels:\n  - conda-forge\nchannel_priority: strict\n" > ~/.condarc
printf "channels:\n  - conda-forge\n" > ~/miniconda3/.condarc
conda config --show channels      # debe listar solo conda-forge
git clone https://github.com/jisalasc/tarea-3-car.git ~/tarea-3-car
cd ~/tarea-3-car && conda env create -f environment.yml -y
```

Nota: `~/scratch` es un symlink roto; trabajar en `~`. El home es NFS, la instalación tarda
varios minutos.

Límites por grupo: 8 CPUs y 4 GB por nodo, 15 min por job, 4 en cola, 1 corriendo.

## Lo que aprendimos del diagnóstico (`check_cluster.slurm`, jobs 37826-37840)

- Las 8 "CPUs" son 4 cores físicos con hyperthreading. Con `--threads-per-core=1` (ya en
  todos los scripts) SLURM entrega 8 cores físicos distintos.
- Los nodos son distintos: ventress (Xeon E5-2640 v4, ~25 GFLOP/s por core) y yodaxico (Xeon
  Silver 4210R, ~18 GFLOP/s por core). `plan_jobs.sh` fija los jobs de 1 nodo a ventress
  (`NODE=... slurm/plan_jobs.sh` para cambiarlo, `NODE=""` para no fijar).
- `mpirun` a secas falla por binding; el lanzador es `srun --mpi=pmix` (variable `LAUNCH` en
  `env.sh`). Detalle completo en `informe/apuntes/cluster.txt`.
Nodos: `ventress` y `yodaxico`. Documentación: https://cluster.cenia.cl/.

**Validado el 9 nov:** `srun --mpi=pmix` levanta los procesos en los 2 nodos (ver arriba).
