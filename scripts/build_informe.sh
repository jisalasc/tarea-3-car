#!/usr/bin/env bash
# Compila el Markdown y empaqueta fuentes compatibles con Overleaf.
# Requiere Pandoc y Tectonic o XeLaTeX. Se pueden indicar con PANDOC y TECTONIC.
set -euo pipefail
cd "$(dirname "$0")/../informe"
PANDOC_BIN=${PANDOC:-pandoc}
"$PANDOC_BIN" informe.md --standalone --from=markdown --to=latex \
  --top-level-division=section --pdf-engine=xelatex --output=informe.tex
if command -v "${TECTONIC:-tectonic}" >/dev/null 2>&1; then
  "${TECTONIC:-tectonic}" --keep-logs informe.tex
elif command -v xelatex >/dev/null 2>&1; then
  xelatex -interaction=nonstopmode -halt-on-error informe.tex
  xelatex -interaction=nonstopmode -halt-on-error informe.tex
else
  echo "LaTeX generado en informe/informe.tex; instala Tectonic o XeLaTeX para obtener el PDF." >&2
  exit 1
fi
zip -q -r -FS overleaf_informe.zip informe.tex figuras OVERLEAF.md
printf '%s\n' 'Listo: informe/informe.tex, informe/informe.pdf e informe/overleaf_informe.zip'
