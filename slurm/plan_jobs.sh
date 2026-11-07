#!/usr/bin/env bash
# Imprime (NO envía) las líneas sbatch de una configuración del enunciado.
# Uso: slurm/plan_jobs.sh <config 0-5> <b> [N]  >> slurm/queue.txt
#      luego: slurm/submit_next.sh   (respeta el límite de 4 jobs en cola)
set -euo pipefail
CFG=$1; B=$2; N=${3:-8192}
OUTDIR=results/cluster
S=slurm/lu_distributed.slurm
job() { # pr pc T nodes tpn
  local pr=$1 pc=$2 T=$3 nodes=$4 tpn=$5
  echo "sbatch --job-name=c${CFG}_${pr}x${pc}_T${T}_b${B} --ntasks=$((pr*pc)) --cpus-per-task=$T --nodes=$nodes --ntasks-per-node=$tpn --export=ALL,N=$N,B=$B,PR=$pr,PC=$pc,OUT=$OUTDIR/config${CFG}.csv $S"
}
case "$CFG" in
  0) for T in 1 2 4 8; do job 1 1 $T 1 1; done
     for T in 1 2 4 8; do echo "sbatch --job-name=serial_T${T}_b${B} --cpus-per-task=$T --export=ALL,N=$N,B=$B,OUT=$OUTDIR/serial.csv slurm/lu_serial.slurm"; done ;;
  1) for g in "1 2" "2 1"; do for T in 1 2 4; do job $g $T 1 2; done; done ;;
  2) for T in 1 2; do job 2 2 $T 1 4; done ;;
  3) job 2 4 1 1 8; job 4 2 1 1 8 ;;
  4) job 2 4 1 2 4 ;;
  5) job 4 4 1 2 8 ;;
  *) echo "config debe ser 0..5" >&2; exit 1 ;;
esac
