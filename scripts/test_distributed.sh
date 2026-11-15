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
  "2 3 64 64" "1 8 64 32"  # procesos sin bloques locales y paneles vacíos
)
fail=0
for c in "${CASES[@]}"; do
  read -r pr pc N b <<< "$c"
  if out=$(mpirun -n "$((pr*pc))" python src/lu_distributed.py --N "$N" --b "$b" --pr "$pr" --pc "$pc" --threads 1 --verify 2>&1); then
    verification=$(printf '%s\n' "$out" | grep -E '\[verify\]' || true)
    if [[ "$verification" == *"-> PASS"* ]]; then
      printf 'grid %sx%s N=%-5s b=%-4s  %s\n' "$pr" "$pc" "$N" "$b" "$verification"
    else
      printf 'FALLO: grid %sx%s N=%s b=%s sin verificación PASS\n%s\n' "$pr" "$pc" "$N" "$b" "$out"
      fail=1
    fi
  else
    printf 'FALLO MPI: grid %sx%s N=%s b=%s\n%s\n' "$pr" "$pc" "$N" "$b" "$out"
    fail=1
  fi
done
[ $fail -eq 0 ] && echo "TODOS PASAN" || { echo "HAY FALLAS"; exit 1; }
