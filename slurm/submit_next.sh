#!/usr/bin/env bash
# Envía las primeras líneas de slurm/queue.txt mientras haya cupo (máx 4 en cola por grupo).
# La cuenta del cluster es COMPARTIDA por los 3: avisar en el grupo antes de encolar.
set -euo pipefail
cd "$(dirname "$0")/.."
Q=${1:-slurm/queue.txt}
MAX=${MAX_QUEUED:-4}
test -s "$Q" || { echo "cola vacía: $Q"; exit 0; }
while :; do
  n=$(squeue -u "$USER" -h | wc -l | tr -d ' ')
  [ "$n" -ge "$MAX" ] && { echo "ya hay $n jobs en cola; quedan $(wc -l < "$Q") pendientes en $Q"; break; }
  line=$(head -n1 "$Q"); [ -z "$line" ] && break
  echo "+ $line"; eval "$line"
  tail -n +2 "$Q" > "$Q.tmp" && mv "$Q.tmp" "$Q"
  [ -s "$Q" ] || { echo "cola vacía"; break; }
done
