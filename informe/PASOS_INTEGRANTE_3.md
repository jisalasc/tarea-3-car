# Guía paso a paso para terminar la Tarea 3 (Integrante 3)

Todo el código del proyecto (`src/`), las ejecuciones en el cluster `kraken` (`results/cluster/config0.csv` a `config5.csv`, `results/parte_a_kraken_T*.csv`), los scripts de gráficos (`scripts/plot_parte_*.py`), las figuras definitivas (`informe/figuras/*.png`) y los apuntes técnicos completos de todas las preguntas (`informe/apuntes/parte_a.txt` a `parte_g.txt`) **ya están 100% listos y verificados**.

A continuación están los **2 únicos pasos** que faltan para cerrar la tarea y generar el `.zip` de entrega.

---

## 0. Resumen del estado del proyecto

| Parte | Estado de datos / código | Apuntes con tablas y explicación | Figura generada | Qué falta hacer |
|---|---|---|---|---|
| **(a)** Serial ($N=4096$) | ✅ Listo (`results/parte_a_mac_jose.csv`) | `informe/apuntes/parte_a.txt` | `informe/figuras/parte_a_mac_jose.png` | Pasar redacción a `informe.md` |
| **(b)** MPI distribuido | ✅ Listo (`src/lu_distributed.py`) | `informe/apuntes/parte_b.txt` | — | Pasar redacción y tabla de colectivas a `informe.md` |
| **(c)** Barrido $b$ en cluster | ✅ Listo (`results/cluster/parte_c.csv`) | `informe/apuntes/parte_c.txt` | `informe/figuras/parte_c.png` | Pasar redacción a `informe.md` |
| **(d)** Configs 0 a 3 (1 nodo) | ✅ Listo (`results/cluster/config0.csv`..`config3.csv`, $b\in\{512,1024\}$) | `informe/apuntes/parte_d.txt` | `informe/figuras/parte_d.png` | Pasar redacción y tabla a `informe.md` |
| **(e)** Configs 4 y 5 (2 nodos) | ✅ Listo (`results/cluster/config3.csv`..`config5.csv`, $b\in\{512,1024\}$) | `informe/apuntes/parte_e.txt` | `informe/figuras/parte_e.png` | Pasar redacción y tablas a `informe.md` |
| **(f)** Grid `2×2`: $b=N/2$ vs $N/16$ | ✅ Listo (`scripts/plot_parte_f.py` sobre `parte_c.csv`) | `informe/apuntes/parte_f.txt` | `informe/figuras/parte_f.png` | Pasar redacción a `informe.md` |
| **(g)** Modelo de costo $(\alpha,\beta,\gamma)$ | ✅ Listo (desarrollo teórico completo) | `informe/apuntes/parte_g.txt` | — | Pasar fórmulas y análisis a `informe.md` |

---

## Paso 1: Redactar el informe final en `informe/informe.md`

Abre [`informe/informe.md`](informe.md) y reemplaza los punteos de cada sección redactando con tus palabras a partir de los archivos de `informe/apuntes/` (que ya contienen todas las tablas Markdown definitivas, números exactos y explicaciones técnicas):

1. **Encabezado:** Completar los nombres de los 3 integrantes en `author:`.
2. **Entorno de pruebas:** Usar los datos de `informe/apuntes/parte_a.txt` (Mac M5) y `informe/apuntes/cluster.txt` (nodos `ventress` y `yodaxico`, `--threads-per-core=1`, `srun --mpi=pmix`).
3. **Sección (a) [10 pts]:** Copiar la tabla y los argumentos de `informe/apuntes/parte_a.txt` e insertar `![](figuras/parte_a_mac_jose.png)`.
4. **Sección (b) [30 pts]:** Usar `informe/apuntes/parte_b.txt` (explicación del arreglo local contiguo, tabla de colectivas `Bcast` con comunicador/raíz/tamaño, medición de `t_comp` vs `t_comm`, verificación con `diff = 0` y residuo $\sim 10^{-16}$).
5. **Sección (c) [10 pts]:** Usar `informe/apuntes/parte_c.txt` e insertar `![](figuras/parte_c.png)` explicando por qué el óptimo baja de `1024` (serial) a `512` (cluster).
6. **Sección (d) [20 pts]:** Usar la tabla completa y los argumentos de `informe/apuntes/parte_d.txt` (justificación de $T(1)$, comparación threads puros vs MPI puro vs híbrido `2×2 T=2`, y efecto de la forma del grid `1×2` vs `2×1` y `2×4` vs `4×2`) e insertar `![](figuras/parte_d.png)`.
7. **Sección (e) [10 pts]:** Usar las tablas y argumentos de `informe/apuntes/parte_e.txt` (latencia/ancho de banda inter-nodo en `col_comm.Bcast`, asimetría de hardware entre `ventress` y `yodaxico`, y escalamiento a 16 CPUs en Config 5 `4×4`) e insertar `![](figuras/parte_e.png)`.
8. **Sección (f) [10 pts]:** Usar la tabla por rango y explicación de `informe/apuntes/parte_f.txt` e insertar `![](figuras/parte_f.png)`.
9. **Sección (g) [10 pts]:** Usar la deducción y respuestas de `informe/apuntes/parte_g.txt`.
10. **Declaración de uso de IA:** Completar la sección final exigida por el enunciado.

*(Nota: Si en algún momento necesitas regenerar cualquiera de las figuras, los comandos son: `python scripts/plot_parte_a.py --tag mac_jose`, `python scripts/plot_parte_c.py`, `python scripts/plot_parte_d.py`, `python scripts/plot_parte_e.py` y `python scripts/plot_parte_f.py`).*

---

## Paso 2: Compilar el PDF y generar el `.zip` de entrega

1. Convierte `informe/informe.md` a **`informe/informe.pdf`** (por ejemplo con Pandoc, la extensión Markdown PDF de VS Code, o Typst/LaTeX).
   * Verifica al abrir `informe/informe.pdf` que todas las figuras (`parte_a_mac_jose.png`, `parte_c.png`, `parte_d.png`, `parte_e.png`, `parte_f.png`) y las fórmulas matemáticas se vean nítidas y sin cortes.
2. Desde la raíz del repositorio, ejecuta el script empaquetador:
   ```bash
   bash scripts/make_zip.sh
   ```
   Esto verificará que exista `informe/informe.pdf` y creará `tarea3_entrega.zip` con los scripts SLURM, el código fuente, los CSV de resultados y el informe en PDF listo para subir a Canvas.
