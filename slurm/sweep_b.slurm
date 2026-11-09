#!/bin/bash
#SBATCH --job-name=lu_sweep_b
#SBATCH --comment="IIC3533 T3 parte c: barrido del tamano de bloque b en grid 2x2 con 2 threads"
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --time=00:15:00
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --ntasks-per-node=4
#SBATCH --cpus-per-task=2
#SBATCH --output=slurm/logs/%x_%j.out
#SBATCH --error=slurm/logs/%x_%j.err
# Parte (c): configuración 2 (grid 2x2, T=2), N=2^13, barrido de b en UN solo job
# (ahorra cupos de la cola: máximo 4 jobs encolados y 1 corriendo por grupo).
#   sbatch --export=ALL,OUT=results/cluster/parte_c.csv slurm/sweep_b.slurm
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/env.sh
N=${N:-8192}
for B in ${B_LIST:-8192 4096 2048 1024 512 256 128 64}; do
  echo "=== b=$B"
  mpirun -n "$SLURM_NTASKS" python src/lu_distributed.py --N "$N" --b "$B" --pr 2 --pc 2 \
      --threads "$SLURM_CPUS_PER_TASK" --reps "${REPS:-3}" --out "$OUT"
done
