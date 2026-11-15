# Estado del informe — Integrante 3

El informe está desarrollado en `informe/informe.md`, con los tres integrantes:
José Ignacio Salas, Borja Smith y Josefina Abbott. Incluye metodología, todos los
incisos del enunciado, declaración de IA y anexos de trazabilidad y reproducción.

| Inciso | Puntaje del PDF | Contenido del informe | Figura |
| --- | --- | --- | --- |
| (a) | 10 | Barrido serial, tabla y elección de b=1024 | `figuras/parte_a_mac_jose.png` |
| (b) | 20 | Distribución, colectivas, raíces, medición y verificaciones registradas | — |
| (c) | 10 | Barrido distribuido, tabla y elección de b=512 | `figuras/parte_c.png` |
| (d) | 20 | Ambas b, configuraciones 0–3, speedup, eficiencia y grid | `figuras/parte_d.png` |
| (e) | 15 | Ambas b, configuraciones 4–5, comparación con un nodo y desglose por host | `figuras/parte_e.png` |
| (f) | 15 | Cómputo y comunicación/espera por proceso, b=N/2 y N/16 | `figuras/parte_f.png` |
| (g) | 10 | Modelo alfa/beta/gamma, sumas, supuestos y cuellos de botella | — |

Las tablas se calcularon desde los CSV definitivos. Los apuntes originales siguen
en `apuntes/` como antecedentes; ante diferencias numéricas, el informe utiliza
`config0.csv` a `config5.csv` y `parte_c.csv`, sin mezclar corridas preliminares.
`t_comm` siempre se interpreta como comunicación **más espera**.

## Generar el PDF y el proyecto Overleaf

Desde la raíz, con Pandoc y Tectonic o XeLaTeX instalados:

```bash
bash scripts/build_informe.sh
```

Se generan `informe/informe.tex`, `informe/informe.pdf` e
`informe/overleaf_informe.zip`. Las instrucciones para Overleaf están en
[`OVERLEAF.md`](OVERLEAF.md). El Markdown es la fuente principal.

## Revisión y entrega

Los integrantes deben revisar la interpretación de sus experimentos y confirmar
que la declaración de IA refleje también cualquier asistencia adicional usada
previamente en código o scripts. El informe distingue las verificaciones MPI
históricas de las comprobaciones hechas durante la preparación del documento.

Tras revisar el PDF, desde la raíz:

```bash
bash scripts/make_zip.sh
```

El resultado es `tarea3_entrega.zip`. La entrega del enunciado es por Canvas el
lunes 16 de noviembre de 2026, a las 23:59. Los ZIP generados están excluidos de Git;
el Markdown, el LaTeX y el PDF sí pueden versionarse en la rama `informe`.
