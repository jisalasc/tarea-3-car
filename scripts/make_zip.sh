#!/usr/bin/env bash
# Arma el .zip de entrega para Canvas: scripts SLURM + código + resultados + informe PDF.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-tarea3_entrega.zip}
test -f informe/informe.pdf || { echo "Falta informe/informe.pdf"; exit 1; }
rm -f "$OUT"
zip -r "$OUT" slurm src scripts results informe/informe.pdf README.md environment.yml -x 'slurm/logs/*' -x '*/__pycache__/*'
echo "Listo: $OUT"
