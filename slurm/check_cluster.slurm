#!/bin/bash
#SBATCH --job-name=check
#SBATCH --comment="IIC3533 T3: diagnostico de CPUs asignadas y de mpirun multi-nodo antes de los experimentos"
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --time=00:06:00
#SBATCH --mem=4G
#SBATCH --output=slurm/logs/%x_%j.out
#SBATCH --error=slurm/logs/%x_%j.err
# Diagnóstico del cluster: qué CPUs nos asignan (¿cores físicos o hyperthreads?), velocidad de
# cada nodo, y qué forma de lanzar MPI levanta $SLURM_NTASKS procesos en todos los nodos.
#   sbatch --ntasks=8 --cpus-per-task=1 --nodes=1 --ntasks-per-node=8 slurm/check_cluster.slurm
#   sbatch --ntasks=8 --cpus-per-task=1 --nodes=2 --ntasks-per-node=4 slurm/check_cluster.slurm
set -uo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/env.sh
NN=$SLURM_JOB_NUM_NODES
echo "job=$SLURM_JOB_ID nodes=$NN nodelist=$SLURM_JOB_NODELIST ntasks=$SLURM_NTASKS cpus/task=$SLURM_CPUS_PER_TASK"
echo "== CPUs asignadas por nodo (lista y hermanos de hyperthreading) y modelo"
srun --nodes=$NN --ntasks=$NN --ntasks-per-node=1 --cpus-per-task=$((SLURM_NTASKS/NN*SLURM_CPUS_PER_TASK)) bash -c '
  echo "$(hostname): $(lscpu | grep "Model name" | sed "s/.*: *//") | $(grep Cpus_allowed_list /proc/self/status)"
  for c in $(grep Cpus_allowed_list /proc/self/status | cut -f2 | tr "," "\n"); do a=${c%-*}; b=${c#*-}
    for i in $(seq $a $b); do echo -n "cpu$i->($(cat /sys/devices/system/cpu/cpu$i/topology/thread_siblings_list)) "; done; done; echo'
echo "== velocidad de cada nodo: lu_serial N=2048 b=256, 1 thread"
srun --nodes=$NN --ntasks=$NN --ntasks-per-node=1 --cpus-per-task=1 bash -c \
  'echo "$(hostname): $(OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python src/lu_serial.py --N 2048 --b 256)"'
echo "== MPI: $(which mpirun) | $(mpirun --version | head -1) | mpi4py $(python -c 'import mpi4py; print(mpi4py.__version__)')"
run_mode() {  # $1 = etiqueta, resto = comando lanzador
  local tag=$1; shift
  echo "== modo [$tag]: $*"
  "$@" bash -c 'echo "  rank $OMPI_COMM_WORLD_RANK$PMIX_RANK$SLURM_PROCID en $(hostname) cpus=$(grep Cpus_allowed_list /proc/self/status | cut -f2)"' 2>&1 | sort -V | head -12
  "$@" python src/lu_distributed.py --N 512 --b 64 --threads "$SLURM_CPUS_PER_TASK" --verify 2>&1 | tail -4
}
run_mode "mpirun --bind-to none"      mpirun -n "$SLURM_NTASKS" --bind-to none
run_mode "mpirun --use-hwthread-cpus" mpirun -n "$SLURM_NTASKS" --use-hwthread-cpus
run_mode "srun --mpi=pmix"            srun --mpi=pmix --ntasks="$SLURM_NTASKS" --cpus-per-task="$SLURM_CPUS_PER_TASK"
echo "FIN"
