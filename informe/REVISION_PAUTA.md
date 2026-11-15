# Revisión de la Tarea 3 contra el enunciado

Fecha: 15 de noviembre de 2026. Rama de trabajo: `informe`.

Se revisó `docs/tarea03.pdf`, idéntico al PDF facilitado por la usuaria. No se
proporcionó una rúbrica adicional de corrección. Los puntajes siguientes son los
del enunciado y no una calificación asignada o garantizada.

## Cobertura por inciso

| Inciso | Puntos | Evidencia revisada | Resultado |
| --- | --- | --- | --- |
| (a) | 10 | N=4096, un thread, siete bloques y tres repeticiones, tabla, figura, elección de b=1024 y residuos | Cubierto |
| (b) | 20 | Núcleo MPI, layout local, colectivas/raíces/tamaños, timers por proceso, contraste serial y oversubscription | Cubierto; 14 pruebas MPI nuevas correctas |
| (c) | 10 | N=8192, grid 2×2, T=2, siete bloques requeridos más b=N, tres repeticiones, tabla/figura y comparación con (a) | Cubierto |
| (d) | 20 | Las 14 variantes de configs 0–3 para cada b, justificación de T(1), speedup, eficiencia y forma del grid | Cubierto: 28 configuraciones |
| (e) | 15 | Configs 4–5 para ambas b, comparación con config 3, cómputo/comunicación, latencia/ancho de banda y desglose por host | Cubierto: cuatro configuraciones adicionales |
| (f) | 15 | Los cuatro procesos para b=4096 y 512, N=8192, grid 2×2 y T=2 declarado, tabla/figura y explicación del desbalance | Cubierto |
| (g) | 10 | Modelo alfa/beta/gamma, sumas, factores del grid, dependencia en b, condición de óptimo y contraste con mediciones | Cubierto; 49 verificaciones algebraicas |
| Entrega | — | Tres integrantes, uso de IA declarado, PDF y scripts SLURM dentro del ZIP | Incluido |

## Comprobaciones ejecutadas

- `python scripts/audit_results.py`: ocho tablas numéricas coinciden con los CSV;
  480 registros distribuidos, 40 grupos de medición y 21 mediciones seriales.
  Se revisan cobertura, tres repeticiones, ranks, hosts, recursos, tiempos finitos
  y definición de t_max, sin sobreescribir resultados.
- `python tests/test_layout.py`: cinco pruebas correctas.
- `bash scripts/test_distributed.sh`: 14 casos correctos, diferencia relativa cero
  frente a serial y residuos entre 1.21e-16 y 2.17e-16. Se incluyeron procesos sin
  bloques y comunicadores con paneles vacíos. No se alteró el núcleo LU.
- Control del verificador: un lanzador simulado que imprime PASS y termina con
  código de error es rechazado por la suite en los 14 casos.
- Modelo: las sumas por paso y las expresiones reagrupadas coinciden en 49
  combinaciones con aritmética racional exacta, incluidos b=N y grids degenerados.
- Los cinco scripts de figuras se ejecutaron desde los CSV; las figuras (c) y
  (f) se actualizaron para explicitar espera y threads, respectivamente.
- El planificador SLURM produjo 32 comandos MPI y ocho seriales con las directivas
  y recursos correctos, sin enviar jobs. El gráfico rechazó la ausencia de una
  referencia medida de T(1), como corresponde.
- Se revisó sintaxis de Python y de todos los scripts shell/SLURM. Se compiló el
  PDF y se comprobaron ecuaciones, tablas y las cinco figuras renderizadas.
- Se verifica la integridad de los ZIP, la coincidencia del PDF empaquetado y la
  presencia de fuentes, pruebas, evidencias y scripts SLURM, sin ZIPs anidados.

Las salidas y metadatos están en `verificacion/`. Las nuevas pruebas son locales y
de correctitud; no son nuevas mediciones de rendimiento ni sustituyen los jobs
registrados en el cluster. La procedencia física de los CSV se toma de los
registros del grupo; la auditoría comprueba su coherencia interna.

## Ajustes realizados para evitar pérdidas de puntaje

1. Se usaron las mediciones definitivas y se distinguió comunicación de espera.
2. Se declaró la referencia serial por bloque y se agregó una referencia común
   alternativa; la configuración de menor tiempo no cambia.
3. Se explicaron explícitamente los términos de latencia y transferencia, sin
   inventar mediciones de red ni descontar esperas como si fueran independientes.
4. Se reagrupó el modelo conservando todos los términos en b y se agregó la
   condición de equilibrio del óptimo. No se afirma predecir b=512 sin calibración.
5. Se impidieron falsos positivos del script de pruebas ante un error de MPI.
6. El gráfico de speedup ya no inventa una referencia si falta T(1): exige un CSV
   válido o un tiempo medido entregado explícitamente con `--t1`.
7. El ZIP incluye ahora pruebas, fuentes del informe y registros de validación,
   y se construye temporalmente para conservar el anterior si falla el empaquetado.

## Revisión de los integrantes antes de entregar

Confirmar que la declaración de IA incluya también cualquier uso previo del grupo
para código/scripts, además de la asistencia documentada durante este informe.
La nota depende de la evaluación docente. Los cambios permanecen locales en la
rama `informe`; esta revisión no los publica ni entrega en Canvas.
