#!/usr/bin/env bash
# Verificación de lu_distributed.py contra lu_serial.py (archivo del curso) en varios grids,
# incluyendo b = N (nb = 1), nb no múltiplo de pr/pc, grids 1xP y Px1. Sale con error si alguno falla.
# Uso: scripts/test_distributed.sh        (requiere pr*pc <= cores físicos; acá máx 8 procesos)
set -euo pipefail
cd "$(dirname "$0")/.."
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
CASES=(
  "1 1 512 64"  "2 2 512 64"  "2 2 512 512" "2 2 512 256"
  "1 4 512 64"  "4 1 512 64"  "2 3 384 32"  "2 3 640 64"  "3 2 640 64"
  "2 4 1024 128" "4 2 1024 64" "2 2 1000 100"
)
fail=0
for c in "${CASES[@]}"; do
  set -- $c
  out=$(mpirun -n $(($1*$2)) python src/lu_distributed.py --N $3 --b $4 --pr $1 --pc $2 --threads 1 --verify 2>&1 | grep -E "\[verify\]" || true)
  printf "grid %sx%s N=%-5s b=%-4s  %s\n" "$1" "$2" "$3" "$4" "${out:-SIN SALIDA (error)}"
  [[ "$out" == *PASS* ]] || fail=1
done
[ $fail -eq 0 ] && echo "TODOS PASAN" || { echo "HAY FALLAS"; exit 1; }
