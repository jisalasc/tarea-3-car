# Se hace `source slurm/env.sh` dentro de cada job. Ajustar la ruta de Miniconda en kraken.
# Instalación en el cluster (una vez, en el nodo de entrada):
#   bash Miniconda3-latest-Linux-x86_64.sh -b -p $HOME/miniconda3
#   $HOME/miniconda3/bin/conda env create -f environment.yml
CONDA_BASE=${CONDA_BASE:-$HOME/miniconda3}
source "$CONDA_BASE/etc/profile.d/conda.sh"
conda activate tarea3
# Threads de BLAS = cpus por tarea (OBLIGATORIO según el enunciado)
export OMP_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export OPENBLAS_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
export MKL_NUM_THREADS=${SLURM_CPUS_PER_TASK:-1}
