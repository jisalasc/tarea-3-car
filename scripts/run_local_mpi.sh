#!/usr/bin/env bash
# Prueba local de lu_distributed.py con verificación contra la versión serial.
# Uso: scripts/run_local_mpi.sh [pr] [pc] [N] [b]
#   scripts/run_local_mpi.sh 2 2 512 64
#   scripts/run_local_mpi.sh 2 3 384 32
# OVERSUBSCRIPTION: pr*pc*T no debe superar los cores físicos del computador.
# Acá T=1 siempre; con 10 cores se pueden probar hasta 8 procesos sin problema.
set -euo pipefail
cd "$(dirname "$0")/.."
PR=${1:-2}; PC=${2:-2}; N=${3:-512}; B=${4:-64}
NP=$((PR * PC))
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mpirun -n "$NP" python src/lu_distributed.py --N "$N" --b "$B" --pr "$PR" --pc "$PC" --threads 1 --verify "${@:5}"
