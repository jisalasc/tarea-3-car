# Tarea 3 — IIC3533 · LU distribuida con mpi4py

Factorización LU por bloques sobre un grid 2D de procesos MPI. Enunciado: [`docs/tarea03.pdf`](docs/tarea03.pdf)
(resumen en [`docs/ENUNCIADO.md`](docs/ENUNCIADO.md)). Plan y división del trabajo: [`docs/PLAN.md`](docs/PLAN.md).
**Entrega: lunes 16 de noviembre 2026, 23:59** (zip con scripts SLURM + informe PDF, por Canvas).

## Estructura
```
src/lu_serial.py        LU por bloques serial del curso (parte a)  ✔ con matrix_entries para generar bloques
src/lu_distributed.py   LU distribuida MPI (parte b)                ◐ infraestructura lista, núcleo con TODOs
src/layout.py           distribución bloque-cíclica (sin MPI)       ✔ testeada vs Figuras 1 y 2
src/lu_serial.py        es el archivo del curso SIN modificar (copia en docs/lu_serial_original.py)
tests/test_layout.py    python tests/test_layout.py
scripts/                parte_a.py, run_local_mpi.sh, make_zip.sh
slurm/                  templates sbatch + planificador de cola (ver slurm/README.md)
results/                CSV de mediciones (se versionan)           ver results/README.md
informe/informe.md      esqueleto del informe
```

## Setup

### macOS (miniforge/conda)
```bash
mamba env create -f environment.yml      # o conda env create -f environment.yml
conda activate tarea3
python tests/test_layout.py
python src/lu_serial.py --N 512 --b 64 --threads 1 --check
mpirun -n 6 python src/lu_distributed.py --N 24 --b 4 --pr 2 --pc 3 --layout-only
```

### Windows
Opción recomendada: **WSL2 (Ubuntu)** + Miniforge dentro de WSL, y los mismos comandos de arriba
(es el mismo flujo que Linux y que el cluster). Clonar el repo dentro del filesystem de WSL (`~/`), no en `/mnt/c`.

Opción nativa: Miniforge para Windows, `conda env create -f environment.yml` (conda-forge instala `mpi4py` sobre
MS-MPI). El lanzador es `mpiexec` en vez de `mpirun`:
```powershell
mpiexec -n 4 python src\lu_distributed.py --N 512 --b 64 --pr 2 --pc 2 --threads 1 --verify
```
Antes de clonar: `git config --global core.autocrlf input` (los scripts SLURM deben quedar con LF; `.gitattributes` lo fuerza).

### Cluster (kraken)
Ver [`slurm/README.md`](slurm/README.md) y la sección "Cluster" de `docs/ENUNCIADO.md`. Miniconda en `$HOME/miniconda3`
(o ajustar `CONDA_BASE` en `slurm/env.sh`), `conda env create -f environment.yml`, `git clone` y `sbatch`.

## Correr

```bash
conda activate tarea3
python scripts/parte_a.py --check            # parte (a): N=4096, 1 thread, b=4096..64 → results/parte_a_<host>.csv
scripts/run_local_mpi.sh 2 2 512 64          # parte (b) local con --verify (falla hasta implementar los TODOs)
python src/lu_distributed.py --help
```

**Oversubscription:** localmente siempre `T=1` y `pr*pc ≤ cores físicos`. Los scripts fijan
`OMP_NUM_THREADS/OPENBLAS_NUM_THREADS/MKL_NUM_THREADS` antes de importar numpy (flag `--threads`).

## Flujo git
Ramas por feature, PR/merge a `main` cuando esté probado, `git pull --rebase` antes de `push`.
`results/` se versiona; `slurm/logs/` no. Nunca subir claves privadas.
