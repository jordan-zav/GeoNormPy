# Preparación de GeoNormPy 0.1.2 para PyPI

La licencia elegida para esta versión es GPL-3.0-or-later. PyPI 0.1.1 conserva sus metadatos históricos MIT; esos archivos publicados no se reemplazan. La versión nueva usa un número distinto y conserva la licencia y el aviso GPL del repositorio actual.

## Verificación

    python -m pytest -q
    python -m build
    python -m twine check --strict dist/*

El wheel y el archivo fuente deben declarar la versión 0.1.2, GPL-3.0-or-later y la dependencia de Python indicada en pyproject.toml. El archivo fuente contiene las pruebas, la configuración y el CSV de ejemplo necesarios para repetir la verificación. La prueba test_installed_wheel.py utiliza GEONORMPY_AUDIT_WHEEL para comprobar el wheel real fuera del checkout.

La integración continua comprueba Python 3.9, 3.11 y 3.14 cuando se ejecute en GitHub. La ejecución local de esta revisión se realizó con Python 3.14.5; la matriz de GitHub no se presenta como ya ejecutada.

## Publicación

Los artefactos preparados localmente se encuentran en D:\DevResources\GeoNormPy\dist\0.1.2. SHA256SUMS.txt permite verificar su integridad. Esa carpeta es una entrega preparada y debe conservarse.

La publicación puede hacerse con el workflow Publish package del repositorio, que comprueba pruebas, distribución y wheel antes de subir. Requiere el secreto PYPI_API_TOKEN configurado en GitHub y la autorización del entorno pypi. Otra opción es ejecutar twine upload sobre los dos archivos preparados usando la autenticación habitual del propietario.

No se ha publicado ni creado una release de GitHub durante esta preparación. Las credenciales no se incluyen en los artefactos. Si se vuelve a construir después de cambiar código, deben repetirse las comprobaciones y actualizarse los hashes.
