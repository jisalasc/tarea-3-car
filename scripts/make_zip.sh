#!/usr/bin/env bash
# Entrega con SLURM, PDF, fuentes, pruebas y datos; sin ZIPs anidados ni auxiliares.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT=${1:-tarea3_entrega.zip}
test -s informe/informe.pdf || { echo "Falta informe/informe.pdf"; exit 1; }
[[ "$(head -c 5 informe/informe.pdf)" == "%PDF-" ]] || { echo "El informe no es un PDF válido"; exit 1; }
STAGING_DIR=$(mktemp -d "${TMPDIR:-/tmp}/tarea3-entrega.XXXXXX")
trap 'rm -rf "$STAGING_DIR"' EXIT
zip -q -r "$STAGING_DIR/entrega.zip" slurm src scripts tests results informe \
  docs/tarea03.pdf docs/lu_serial_original.py README.md environment.yml \
  -x 'slurm/logs/*' '*/__pycache__/*' 'informe/*.zip' 'informe/*.aux' \
     'informe/*.log' 'informe/*.out' 'informe/*.toc' 'informe/*.synctex.gz'
unzip -tq "$STAGING_DIR/entrega.zip" >/dev/null
mv "$STAGING_DIR/entrega.zip" "$OUT"
echo "Listo: $OUT"
