#!/usr/bin/env bash
# Parte (a): lu_serial.py con N = 2^12 y UN thread, b en {2^12, ..., 2^6}.
# Uso: scripts/run_parte_a.sh            (REPS=5 scripts/run_parte_a.sh para más repeticiones)
# Salida: results/parte_a_<host>.csv (se anexa; usar la mediana por b en el informe).
set -euo pipefail
cd "$(dirname "$0")/.."
N=${N:-4096}
REPS=${REPS:-3}
OUT=${OUT:-results/parte_a_$(hostname -s).csv}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
echo "N=$N reps=$REPS out=$OUT  (cerrar otras apps pesadas; 1 thread)"
for b in 4096 2048 1024 512 256 128 64; do
  python src/lu_serial.py --N "$N" --b "$b" --threads 1 --reps "$REPS" --out "$OUT"
done
