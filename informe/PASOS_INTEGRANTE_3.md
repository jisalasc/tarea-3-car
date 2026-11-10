# Guía paso a paso para terminar la Tarea 3 (Integrante 3)

Todo el código del proyecto (`src/`), los scripts de SLURM (`slurm/`), los scripts de gráficos (`scripts/plot_parte_*.py`) y los apuntes técnicos de todas las preguntas (`informe/apuntes/parte_a.txt` a `parte_g.txt`) **ya están implementados y probados**.

A continuación están los **4 pasos exactos** que faltan para cerrar la tarea y generar el `.zip` de entrega.
v
---

## 0. Resumen de qué ya está listo vs. qué falta

| Parte | Estado de datos / código | Apuntes con tablas y explicación | Figura generada | Qué falta hacer |
|---|---|---|---|---|
| **(a)** Serial ($N=4096$) | ✅ Listo (`results/parte_a_mac_jose.csv`) | `informe/apuntes/parte_a.txt` | `informe/figuras/parte_a_mac_jose.png` | Pasar redacción a `informe.md` |
| **(b)** MPI distribuido | ✅ Listo (`src/lu_distributed.py`) | `informe/apuntes/parte_b.txt` | — | Pasar redacción y tabla de colectivas a `informe.md` |
| **(c)** Barrido $b$ en cluster | ✅ Listo (`results/cluster/parte_c.csv`) | `informe/apuntes/parte_c.txt` | `informe/figuras/parte_c.png` | Pasar redacción a `informe.md` |
| **(d)** Configs 0 a 3 (1 nodo) | ⏳ Script listo (`scripts/plot_parte_d.py`); faltan CSV de configs 0, 1 y resto de 2, 3 | `informe/apuntes/parte_d.txt` | `informe/figuras/parte_d.png` (preliminar) | **Correr configs 0–3 en `kraken`**, re-ejecutar `plot_parte_d.py` y redactar |
| **(e)** Configs 4 y 5 (2 nodos) | ⏳ Script listo (`scripts/plot_parte_e.py`); ya está `2×4` (1n vs 2n), falta Config 5 (`4×4`) | `informe/apuntes/parte_e.txt` | `informe/figuras/parte_e.png` (con Config 3 vs 4) | **Correr configs 4–5 en `kraken`**, re-ejecutar `plot_parte_e.py` y redactar |
| **(f)** Grid `2×2`: $b=N/2$ vs $N/16$ | ✅ Listo (`scripts/plot_parte_f.py` sobre `parte_c.csv`) | `informe/apuntes/parte_f.txt` | `informe/figuras/parte_f.png` | Pasar redacción a `informe.md` |
| **(g)** Modelo de costo $(\alpha,\beta,\gamma)$ | ✅ Listo (desarrollo teórico completo) | `informe/apuntes/parte_g.txt` | — | Pasar fórmulas y análisis a `informe.md` |

---

## Paso 1: Ejecutar las configuraciones faltantes en el cluster `kraken` (Partes d y e)

El entorno `conda` (`tarea3`) y el repositorio ya están instalados en la cuenta del grupo en `kraken` (`~/tarea-3-car`).

### 1.1 Conectarse y actualizar el repositorio
```bash
ssh kraken
cd ~/tarea-3-car
git pull
```
*(Si están trabajando en la rama `dev`, verifica con `git checkout dev && git pull`).*

### 1.2 Armar la cola de jobs con `slurm/plan_jobs.sh`
El enunciado pide en **(d)** y **(e)** usar los valores de $b$ obtenidos en **(a)** ($b = 1024$) y en **(c)** ($b = 512$).
Primero encola todas las configuraciones `0..5` con **`b = 512`** (que es el óptimo del cluster):

```bash
rm -f slurm/queue.txt
for c in 0 1 2 3 4 5; do
    slurm/plan_jobs.sh $c 512 >> slurm/queue.txt
done
```

*(Opcional recomendado: para cumplir literalmente con "los valores de $b$ obtenidos en (a) y en (c)", una vez terminen los de `512`, puedes encolar también `b = 1024` con `for c in 0 1 2 3 4 5; do slurm/plan_jobs.sh $c 1024 >> slurm/queue.txt; done`).*

### 1.3 Enviar los jobs respetando el límite de la cola (máx. 4 encolados, 1 corriendo)
Usa el script despachador que ya está programado:

```bash
slurm/submit_next.sh
```

* Revisa el progreso con:
  ```bash
  squeue -u $USER
  tail -n 20 slurm/logs/*.out
  ```
* Cada vez que veas que se desocuparon cupos en `squeue -u $USER`, vuelve a correr `slurm/submit_next.sh` hasta que te diga `cola vacía`.
* Cada job tarda entre 10 y 40 segundos en correr, así que toda la tanda sale rápido.

### 1.4 Subir los resultados CSV al repositorio
Cuando terminen todos los jobs, verifica que existan `results/cluster/config0.csv` ... `results/cluster/config5.csv` (y `results/parte_a_kraken_T*.csv` generados por la referencia serial de Config 0) y súbelos a Git:

```bash
git add results/
git commit -m "resultados cluster configs 0 a 5"
git push
```

---

## Paso 2: Regenerar las tablas y figuras definitivas de (d) y (e)

En tu computador (o en el mismo `kraken` activando `conda activate tarea3`), haz `git pull` y ejecuta:

### 2.1 Actualizar tabla y figura de la Parte (d)
```bash
python scripts/plot_parte_d.py
```
* Esto leerá automáticamente `results/cluster/config[0-3].csv` y `results/parte_a_kraken_T1.csv` (para $T(1)$).
* Imprimirá en la terminal la **tabla Markdown definitiva** de Speedup y Eficiencia (cópiala para ponerla en `informe/informe.md`).
* Actualizará la figura `informe/figuras/parte_d.png`.

### 2.2 Actualizar tabla y figura de la Parte (e)
```bash
python scripts/plot_parte_e.py --csv results/cluster/config3.csv results/cluster/config4.csv results/cluster/config5.csv
```
* Imprimirá en la terminal las **dos tablas Markdown definitivas** (resumen de Config 3 vs Config 4 vs Config 5, y desglose por nodo `ventress` vs `yodaxico`).
* Actualizará la figura `informe/figuras/parte_e.png`.

*(Si necesitas regenerar cualquiera de las otras figuras, los comandos son: `python scripts/plot_parte_a.py --tag mac_jose`, `python scripts/plot_parte_c.py` y `python scripts/plot_parte_f.py`).*

---

## Paso 3: Redactar el informe final en `informe/informe.md`

Abre [`informe/informe.md`](informe.md) y reemplaza los punteos de cada sección redactando con tus palabras a partir de los archivos de `informe/apuntes/` (que ya tienen todas las tablas, números y explicaciones técnicas):

1. **Encabezado:** Completar los nombres de los 3 integrantes en `author:`.
2. **Entorno de pruebas:** Usar los datos de `informe/apuntes/parte_a.txt` (Mac M5) y `informe/apuntes/cluster.txt` (nodos `ventress` y `yodaxico`, `--threads-per-core=1`, `srun --mpi=pmix`).
3. **Sección (a):** Copiar tabla y argumentos de `informe/apuntes/parte_a.txt` e insertar `![](figuras/parte_a_mac_jose.png)`.
4. **Sección (b):** Usar `informe/apuntes/parte_b.txt` (explicación del arreglo local contiguo, tabla de colectivas `Bcast` con comunicador/raíz/tamaño, medición de `t_comp` vs `t_comm`, verificación con `diff = 0` y residuo $\sim 10^{-16}$).
5. **Sección (c):** Usar `informe/apuntes/parte_c.txt` e insertar `![](figuras/parte_c.png)` explicando por qué el óptimo baja de `1024` (serial) a `512` (cluster).
6. **Sección (d):** Usar los argumentos de `informe/apuntes/parte_d.txt`, pegar la tabla generada en el **Paso 2.1** e insertar `![](figuras/parte_d.png)`.
7. **Sección (e):** Usar los argumentos de `informe/apuntes/parte_e.txt` (latencia/ancho de banda inter-nodo + asimetría entre `ventress` y `yodaxico`), pegar las tablas del **Paso 2.2** e insertar `![](figuras/parte_e.png)`.
8. **Sección (f):** Usar `informe/apuntes/parte_f.txt` e insertar `![](figuras/parte_f.png)`.
9. **Sección (g):** Usar la deducción y respuestas de `informe/apuntes/parte_g.txt`.
10. **Declaración de uso de IA:** Completar la sección final exigida por el enunciado.

---

## Paso 4: Compilar el PDF y generar el `.zip` de entrega

1. Convierte `informe/informe.md` a **`informe/informe.pdf`** (por ejemplo con Pandoc, la extensión Markdown PDF de VS Code, o Typst/LaTeX).
   * Verifica al abrir `informe/informe.pdf` que todas las figuras (`parte_a_mac_jose.png`, `parte_c.png`, `parte_d.png`, `parte_e.png`, `parte_f.png`) y las fórmulas matemáticas se vean nítidas y sin cortes.
2. Desde la raíz del repositorio, ejecuta el script empaquetador:
   ```bash
   bash scripts/make_zip.sh
   ```
   Esto verificará que exista `informe/informe.pdf` y creará `tarea3_entrega.zip` con los scripts SLURM, el código fuente, los CSV de resultados y el informe en PDF listo para subir a Canvas.
