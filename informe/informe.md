---
title: "Tarea 3 — Factorización LU distribuida con mpi4py"
subtitle: "IIC3533 Computación de Alto Rendimiento · 2026-2"
author: "José Ignacio Salas, <integrante 2>, <integrante 3>"
date: "16 de noviembre de 2026"
---

<!-- Generar PDF: pandoc informe/informe.md -o informe/informe.pdf  (o reportlab como en la Tarea 2) -->
<!-- Todas las figuras: título, labels con unidades, leyenda, fuente ≥ 11pt. Tablas con mediana y N de repeticiones. -->

## Entorno de pruebas
- Computador personal (parte a): modelo, CPU, cores físicos, RAM, versiones numpy/scipy/BLAS (`threadpoolctl`).
- Cluster kraken: nodos `ventress`/`yodaxico`, límites (8 CPUs, 4 GB, 15 min), versiones.

## (a) Barrido de b en serial (N = 4096, 1 thread) — 10 pts
<!-- apuntes: informe/apuntes/parte_a.txt. Datos: results/parte_a_mac_jose.csv -->
Mostrar: tabla (b, mediana, min, max, GFLOP/s) + figura `informe/figuras/parte_a_mac_jose.png`. Máquina y condiciones. b elegido = 1024 (512–2048 equivalentes).

## (b) Implementación distribuida — 20 pts
<!-- apuntes: informe/apuntes/parte_b.txt -->
- Distribución bloque-cíclica y layout local (sub-arreglo contiguo ⇒ un matmul por paso).
- Por paso k, con (r,c) = (k mod pr, k mod pc): tabla **operación colectiva / comunicador / raíz / tamaño**.
- Medición separada de cómputo y comunicación por proceso (qué se cuenta en cada uno; la espera va en comunicación).
- Verificación de correctitud vs serial: misma matriz determinista, comparación elemento a elemento y residuo ||A−LU||/||A||. Casos probados (grids, b=N, nb no múltiplo de pr/pc).
- Oversubscription: cómo se evitó.

## (c) Barrido de b en el cluster (N = 8192, config 2, T = 2) — 10 pts
Tabla/gráfico. ¿Sigue siendo el mejor el b de (a)? Por qué sí/no.

- Datos: `results/cluster/parte_c.csv` (job 37838, ventress). Tabla y figura: `python scripts/plot_parte_c.py` → `informe/figuras/parte_c.png`.
- Apuntes con la tabla y los argumentos: `informe/apuntes/parte_c.txt`. Setup del cluster (hardware, hyperthreading, lanzador): `informe/apuntes/cluster.txt`.
- Resultado: **b = 512** (2.59 s, 141.6 GFLOP/s); b=256 +6 %, b=1024 +12 %. Óptimo más chico que en (a) por el desbalance con b grande.

## (d) Configuraciones 0 a 3: speedup y eficiencia — 20 pts
<!-- apuntes: informe/apuntes/parte_d.txt | script: scripts/plot_parte_d.py -> informe/figuras/parte_d.png -->
Elección y justificación de T(1). Tabla/gráfico speedup y eficiencia vs CPUs totales. Mejor configuración. Efecto de la forma del grid (1×2 vs 2×1, 2×4 vs 4×2).

## (e) Configuraciones 4 y 5: dos nodos — 15 pts
<!-- apuntes: informe/apuntes/parte_e.txt | script: scripts/plot_parte_e.py -> informe/figuras/parte_e.png -->
Config 4 (2×4, 2 nodos) vs config 3 (2×4, 1 nodo): cómputo vs comunicación. Latencia y ancho de banda intra vs inter nodo. Config 5 (4×4).

## (f) Grid 2×2: b = N/2 vs b = N/16 — 15 pts
<!-- apuntes: informe/apuntes/parte_f.txt | script: scripts/plot_parte_f.py -> informe/figuras/parte_f.png -->
Cómputo y comunicación de cada proceso (4 procesos × 2 valores de b). Explicación (desbalance con b grande, más mensajes con b chico).

## (g) Modelo de costo (α, β, γ) — 10 pts
<!-- apuntes: informe/apuntes/parte_g.txt -->
Costo total en función de N, b, pr, pc. Términos que explican el b óptimo. Cuello de botella según las mediciones.

## Declaración de uso de IA
Se usó <herramienta> para: inicialización del repositorio y scripts base, revisión de código, redacción. Todo el código fue revisado y probado por los integrantes.

## Anexos
Scripts SLURM, comandos usados, CSV crudos.
