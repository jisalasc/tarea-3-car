#!/bin/bash
#SBATCH --job-name=lu_dist
#SBATCH --comment="IIC3533 T3: LU por bloques distribuida con mpi4py, tiempos por configuracion de grid y threads"
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --time=00:15:00
#SBATCH --mem=4G
#SBATCH --threads-per-core=1
#SBATCH --output=slurm/logs/%x_%j.out
#SBATCH --error=slurm/logs/%x_%j.err
# --ntasks (p = pr*pc), --cpus-per-task (T), --nodes y --ntasks-per-node se pasan
# en la línea de sbatch; N, B, PR, PC, OUT (y opcional REPS) van en --export.
# Ejemplo (configuración 2, T=2):
#   sbatch --ntasks=4 --cpus-per-task=2 --nodes=1 --ntasks-per-node=4 \
#          --export=ALL,N=8192,B=256,PR=2,PC=2,OUT=results/cluster/config2.csv slurm/lu_distributed.slurm
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/env.sh
echo "job=$SLURM_JOB_ID N=$N b=$B grid=${PR}x${PC} T=$SLURM_CPUS_PER_TASK ntasks=$SLURM_NTASKS nodes=$SLURM_JOB_NUM_NODES tpn=${SLURM_NTASKS_PER_NODE:-?} nodelist=$SLURM_JOB_NODELIST"
$LAUNCH python src/lu_distributed.py --N "$N" --b "$B" --pr "$PR" --pc "$PC" \
    --threads "$SLURM_CPUS_PER_TASK" --reps "${REPS:-3}" --out "$OUT"
