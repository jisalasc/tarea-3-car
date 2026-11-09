# Se hace `source slurm/env.sh` dentro de cada job. Miniconda ya está instalado en la cuenta
# del grupo en kraken (ver README.md de esta carpeta para recrearlo).
CONDA_BASE=${CONDA_BASE:-$HOME/miniconda3}
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate tarea3
# Threads de BLAS = cpus por tarea (OBLIGATORIO según el enunciado)
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
# Lanzador MPI. Validado en kraken (jobs 37828-37830, 1 y 2 nodos):
#  - `srun --mpi=pmix` (elegido): SLURM reparte los procesos entre nodos y liga cada uno a
#    sus $SLURM_CPUS_PER_TASK CPUs; verify PASS con diferencia 0 vs serial.
#  - `mpirun -n $SLURM_NTASKS --use-hwthread-cpus`: también funciona (alternativa).
#  - `mpirun` a secas FALLA: liga por core, ve 4 cores (las 8 CPUs son 4 cores con
#    hyperthreading) y aborta con 8 procesos. `--bind-to none` corre pero es 10x más lento.
LAUNCH=${LAUNCH:-"srun --mpi=pmix --ntasks=$SLURM_NTASKS --cpus-per-task=${SLURM_CPUS_PER_TASK:-1}"}
