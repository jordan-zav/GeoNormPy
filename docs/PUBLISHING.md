# Preparación y publicación de GeoNormPy 1.1.0

La licencia elegida para esta versión es GPL-3.0-or-later. PyPI 0.1.1 conserva sus metadatos históricos MIT; esos archivos publicados no se reemplazan. La versión nueva usa un número distinto y conserva la licencia y el aviso GPL del repositorio actual.

## Verificación

    python -m pytest -q
    python -m build
    python -m twine check --strict dist/*

El wheel y el archivo fuente deben declarar la versión 1.1.0, GPL-3.0-or-later y la dependencia de Python indicada en pyproject.toml. La versión de ejecución y CITATION.cff deben coincidir. El archivo fuente incluye pruebas, fixtures JSON, configuración, CSV de ejemplo y ejecutores de benchmarks. La prueba test_installed_wheel.py utiliza GEONORMPY_AUDIT_WHEEL para comprobar los tres perfiles desde el wheel real fuera del checkout.

La integración continua está configurada para Python 3.9, 3.11 y 3.14. La preparación local de 1.1.0 utiliza Python 3.11.9. Los informes de benchmarks anteriores corresponden a 1.1.0.dev0; conservan sus versiones, fechas y hashes históricos.

Después de construir, ejecutar python scripts/check_distribution.py RUTA_DIST para revisar metadatos, licencia y archivos necesarios en ambos artefactos. Repetir la suite desde el archivo fuente extraído permite detectar omisiones del manifiesto que una ejecución desde el repositorio no revela.

## Publicación

Los candidatos 1.1.0 se construyen en una sesión nueva de D:\DevResources\Sessions\GeoNormPy, separados de la entrega anterior 1.0.0. SHA256SUMS.txt permite verificar su integridad. Conservar los artefactos y el informe de preparación. Preparar un candidato no publica archivos en PyPI.

La publicación puede hacerse con el workflow Publish package del repositorio, que comprueba pruebas, distribución y wheel antes de subir. Requiere el secreto PYPI_API_TOKEN configurado en GitHub y la autorización del entorno pypi. Otra opción es ejecutar twine upload sobre los dos archivos preparados usando la autenticación habitual del propietario.

La release de GitHub v1.1.0 activa el workflow de publicación. Crear esa release o ejecutar manualmente Publish package constituye una acción de publicación. Tras completarse, verificar versión, licencia y hashes de los archivos servidos por PyPI. Las credenciales no se incluyen en los artefactos. Si se vuelve a construir después de cambiar código, deben repetirse las comprobaciones y actualizarse los hashes.
