#!/bin/bash
#SBATCH --job-name=lu_serial
#SBATCH --comment="IIC3533 T3: LU por bloques serial de referencia para calcular speedup"
#SBATCH --qos=hpc-iic3533
#SBATCH --partition=hpc-iic3533
#SBATCH --account=default-account
#SBATCH --time=00:15:00
#SBATCH --mem=4G
#SBATCH --threads-per-core=1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --ntasks-per-node=1
#SBATCH --output=slurm/logs/%x_%j.out
#SBATCH --error=slurm/logs/%x_%j.err
# Referencia serial en el cluster (base T(1) para speedup, parte d). --cpus-per-task en sbatch.
#   sbatch --cpus-per-task=1 --export=ALL,N=8192,B=256,TAG=kraken_T1 slurm/lu_serial.slurm
# Escribe results/parte_a_<TAG>.csv (mismo formato que la parte a).
set -euo pipefail
cd "$SLURM_SUBMIT_DIR"
source slurm/env.sh
echo "job=$SLURM_JOB_ID N=$N b=$B T=$SLURM_CPUS_PER_TASK nodelist=$SLURM_JOB_NODELIST"
python scripts/parte_a.py --N "$N" --b $B --threads "$SLURM_CPUS_PER_TASK" --reps "${REPS:-3}" --tag "${TAG:-kraken_T$SLURM_CPUS_PER_TASK}"
