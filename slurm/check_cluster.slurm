#!/bin/bash
#SBATCH --job-name=check
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --time=00:05:00
#SBATCH --output=slurm/logs/%x_%j.out
#SBATCH --error=slurm/logs/%x_%j.err
# Diagnóstico del cluster: qué CPUs nos asignan (¿cores físicos o hyperthreads?), versión de MPI,
# y que mpirun levante $SLURM_NTASKS procesos en todos los nodos (--layout-only, sin cómputo).
#   sbatch --ntasks=8 --cpus-per-task=1 --nodes=1 --ntasks-per-node=8 slurm/check_cluster.slurm
#   sbatch --ntasks=8 --cpus-per-task=1 --nodes=2 --ntasks-per-node=4 slurm/check_cluster.slurm
set -uo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/env.sh
echo "job=$SLURM_JOB_ID nodes=$SLURM_JOB_NUM_NODES nodelist=$SLURM_JOB_NODELIST ntasks=$SLURM_NTASKS cpus/task=$SLURM_CPUS_PER_TASK"
echo "== CPUs asignadas en cada nodo (Cpus_allowed_list) y modelo"
srun --ntasks-per-node=1 bash -c 'echo "$(hostname): $(grep Cpus_allowed_list /proc/self/status)"; lscpu | grep -E "Model name|Thread\(s\) per core|Core\(s\) per socket|L2|L3"; echo "siblings de las CPUs asignadas:"; for c in $(grep Cpus_allowed_list /proc/self/status | cut -f2 | tr "," "\n"); do a=${c%-*}; b=${c#*-}; for i in $(seq $a $b); do echo -n "cpu$i->$(cat /sys/devices/system/cpu/cpu$i/topology/thread_siblings_list) "; done; done; echo'
echo "== MPI"
which mpirun; mpirun --version | head -1; python -c "import mpi4py; print('mpi4py', mpi4py.__version__)"
echo "== layout-only con mpirun -n \$SLURM_NTASKS"
mpirun -n "$SLURM_NTASKS" bash -c 'echo "rank $OMPI_COMM_WORLD_RANK en $(hostname) cpus=$(grep Cpus_allowed_list /proc/self/status | cut -f2)"' | sort -V
mpirun -n "$SLURM_NTASKS" python src/lu_distributed.py --N 64 --b 8 --layout-only
echo "== mini LU con verify (N=512, b=64)"
mpirun -n "$SLURM_NTASKS" python src/lu_distributed.py --N 512 --b 64 --threads "$SLURM_CPUS_PER_TASK" --verify
echo "FIN"
