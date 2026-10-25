# Publicación de GeoNormPy 1.0.0 en PyPI

La licencia elegida para esta versión es GPL-3.0-or-later. PyPI 0.1.1 conserva sus metadatos históricos MIT; esos archivos publicados no se reemplazan. La versión nueva usa un número distinto y conserva la licencia y el aviso GPL del repositorio actual.

## Verificación

    python -m pytest -q
    python -m build
    python -m twine check --strict dist/*

El wheel y el archivo fuente deben declarar la versión 1.0.0, GPL-3.0-or-later y la dependencia de Python indicada en pyproject.toml. El archivo fuente contiene las pruebas, la configuración y el CSV de ejemplo necesarios para repetir la verificación. La prueba test_installed_wheel.py utiliza GEONORMPY_AUDIT_WHEEL para comprobar el wheel real fuera del checkout.

La integración continua comprueba Python 3.9, 3.11 y 3.14. La ejecución local de la preparación se realiza con Python 3.14.5.

## Publicación

Los artefactos se encuentran en D:\DevResources\GeoNormPy\dist\1.0.0. SHA256SUMS.txt permite verificar su integridad. Esa carpeta es una entrega y debe conservarse. Los candidatos construidos localmente se mantienen en su subcarpeta candidate; los archivos obtenidos y verificados desde PyPI se guardan en la carpeta principal.

La publicación puede hacerse con el workflow Publish package del repositorio, que comprueba pruebas, distribución y wheel antes de subir. Requiere el secreto PYPI_API_TOKEN configurado en GitHub y la autorización del entorno pypi. Otra opción es ejecutar twine upload sobre los dos archivos preparados usando la autenticación habitual del propietario.

La release de GitHub v1.0.0 activa el workflow de publicación. Tras completarse, se verifica la versión, licencia y hashes de los archivos servidos por PyPI. Las credenciales no se incluyen en los artefactos. Si se vuelve a construir después de cambiar código, deben repetirse las comprobaciones y actualizarse los hashes.
