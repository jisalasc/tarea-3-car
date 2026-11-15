# Compilación del informe

La fuente principal es `informe.md`. La versión `informe.tex` se genera con Pandoc;
si cambias el Markdown, vuelve a compilar para actualizar el LaTeX y el PDF.

## Compilación local

Instala Pandoc y Tectonic o XeLaTeX. Desde la raíz del repositorio:

```bash
bash scripts/build_informe.sh
```

Para utilizar binarios fuera del PATH:

```bash
PANDOC=/ruta/a/pandoc TECTONIC=/ruta/a/tectonic bash scripts/build_informe.sh
```

El script genera el PDF y `informe/overleaf_informe.zip` con el LaTeX y las cinco
figuras. Tectonic necesita acceso a internet la primera vez para descargar sus
paquetes de composición. Los auxiliares de LaTeX no se versionan.

## Overleaf

1. Elige **New Project → Upload Project** y sube `overleaf_informe.zip`.
2. En la configuración del proyecto, selecciona **XeLaTeX** como compilador y
   `informe.tex` como documento principal.
3. Compila y comprueba las tablas, ecuaciones y las cinco figuras. Las figuras
   grandes ocupan páginas horizontales para conservar su legibilidad.
4. Si editas en Overleaf, descarga también los fuentes para conservar esos cambios.
5. Descarga el PDF final y guárdalo como `informe/informe.pdf` antes de ejecutar
   `bash scripts/make_zip.sh` desde la raíz.

El PDF incluye los tres integrantes: José Ignacio Salas, Borja Smith y Josefina
Abbott. Las mediciones y verificaciones MPI históricas se atribuyen a los registros
del grupo; la compilación del documento no implica que se hayan repetido esos jobs.
