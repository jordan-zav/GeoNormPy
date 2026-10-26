# Validación de perfiles CIPW: 26 de octubre de 2026

Actualización posterior: [388 pruebas y validación ampliada](pruebas_ampliadas_20261026.md).
Las cifras siguientes documentan la primera ejecución de 297 pruebas.

GeoNormPy 1.1.0.dev0 incorpora extended_cipw_v3, verma2003 y pruseth2009,
con políticas independientes de hierro y metadatos de cálculo. La ruta
predeterminada conserva el motor anterior con la corrección numérica de
piroxenos. Es una versión de desarrollo local, sin publicación en PyPI.

La [guía de perfiles](PERFILES_CIPW.md) detalla API, consola, unidades,
carbonatos, fluorapatita y diferencias de preparación respecto de los artículos.

## Verificación funcional y del paquete

- GeoNormPy: 297 pruebas aprobadas, ninguna omitida en la ejecución final.
- Incluye ejecución desde el wheel fuera del checkout para los tres perfiles.
- Veinte análisis congelados del motor anterior reproducen minerales,
  residuales, diagnósticos y balance dentro de una tolerancia absoluta de 1e-12.
- Pruseth reproduce el ejemplo ultrabásico publicado: corindón, anortita,
  olivino, ilmenita, apatita, silicato dicálcico y kaliophilita. Se comparan
  valores sobre la base original de 99,72 %, con tolerancias de redondeo de
  0,00002 a 0,00003 puntos porcentuales.
- GeoNormML: 32 pruebas aprobadas; análisis estático y comprobación de
  dependencias aprobados. No se entrenaron modelos.
- Los 68 archivos registrados de Dataset y artifacts conservan sus hashes
  originales. La base curada mantiene sus 2.755 filas.

Wheel comprobado: geonormpy-1.1.0.dev0-py3-none-any.whl.
SHA256: bb57a0bb9e674972f3acf6e5da2f4cbf92bdc3a5413a596fac2fb85203f9f99a.

## Estrés sintético

Se ejecutaron 12.000 cálculos principales: 2.000 composiciones mayores y
2.000 extendidas para cada perfil. Semillas 20261026 y 20261027. Para Pruseth
se omiten Cl y SO3 en el grupo extendido, conforme a su conjunto implementado.
Estas composiciones deliberadamente amplias no representan la distribución
de rocas naturales. Se registran también las normas incompletas.

| Perfil | Completas mayores / 2.000 | Completas extendidas / 2.000 | Máximo error de masa entre completas, mayores / extendidas |
| --- | --- | --- | --- |
| Compatibilidad | 924 | 757 | 0,002590 / 1,081790 |
| Verma | 982 | 1.026 | 2,84e-14 / 2,84e-14 |
| Pruseth | 1.034 | 1.051 | 4,26e-14 / 4,26e-14 |

Los perfiles nuevos contabilizan minerales, componentes libres y correcciones
de oxígeno y F con signos explícitos, sin renormalizar los minerales.
El máximo error del inventario total, incluyendo el déficit negativo de
sílice cuando existe, es 5,69e-14 puntos porcentuales. Ese inventario puede
cerrar aunque una norma siga incompleta; no debe confundirse con una norma
aceptable para interpretación.

La comprobación de escala de las primeras cien filas de cada grupo, con
factor 1e200, produce diferencias por mineral inferiores a 1,21e-13 puntos.
Los mayores conteos de asignación completa reflejan tanto las reglas de
componentes libres como la extensión de déficit de Pruseth.

## Comparación externa controlada

Comparador: pyrolite 0.3.8.post1, aislado de las dependencias del paquete.
Se ejecuta sobre los mismos mayores ajustados y la misma partición de hierro.
Mn se armoniza previamente en ambos motores para este experimento, según
la preparación del benchmark anterior. No se evalúan aquí las ramas de
trazas, volátiles ni las tablas normativas históricas guardadas en los datos.

| Grupo | Filas | Sin déficit de sílice en ambos: Verma / Pruseth | Máxima diferencia por mineral, Verma / Pruseth |
| --- | --- | --- | --- |
| Sintéticos mayores | 2.000 | 982 / 982 | 0,004254 / 0,004254 |
| Públicos de pyrolite | 551 | 525 / 525 | 0,003355 / 0,003355 |
| Mayores de GeoNormML | 2.755 | 2.755 / 2.755 | 0,003512 / 0,003512 |

Las diferencias se expresan en puntos porcentuales de peso. Para Pruseth
se excluye apatita de esa métrica por su fluorapatita normativa; ambos valores
de apatita quedan guardados aparte. Entre los casos sin déficit compartido,
ninguna fila supera 0,01 puntos porcentuales por mineral.

Pruseth completa otros 52 sintéticos y un análisis público mediante su
extensión de anortita. En estos casos el comparador conserva déficit de
sílice, y aparecen diferencias máximas de 51,06 y 19,39 puntos respectivamente.
Los CSV y el resumen conservan esos casos y distinguen los denominadores.

En GeoNormML, el perfil anterior marca 20 análisis como incompletos por
componentes no asignados. Los nuevos perfiles conservan esos componentes
libres con advertencia y cierran su contabilidad. El cambio de estado no
elimina las observaciones químicas ni demuestra que esas muestras sean
petrográficamente correctas. No se modificaron sus datos ni normas almacenadas.

## Reproducción y límites

El [resumen JSON](../benchmarks/results/cipw_profiles_20261026.json) conserva
semillas, hashes del motor y del ejecutor, denominadores y métricas.
El ejecutor es benchmarks/benchmark_profiles.py; sus opciones están en
benchmarks/README.md. Los CSV completos y el wheel de esta ejecución están
en D:\DevResources\Sessions\GeoNormPy\profiles_20261026_1793025667018,
subdirectorios results_final y wheels_final.

Las fases puras, sustituyentes y componentes libres se comprueban mediante
pruebas estequiométricas; no se realizó una comparación externa completa
de todas las ramas menores de ambos artículos. Las convenciones de entrada
comunes y el carbonato explícito están documentados. Los perfiles tienen
validación numérica, sin certificación petrográfica independiente.
