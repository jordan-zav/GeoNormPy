# GeoNormPy 1.1.0: estado y pendientes

[English](STATUS.md) · [Procedimiento de publicación](PUBLISHING.md)

La versión 1.1.0 incorpora extended_cipw_v3 3.1, verma2003 1.0 y pruseth2009
1.0, con políticas de hierro independientes. El perfil predeterminado corregido
no es idéntico a GeoNormPy 1.0.0 ni a la versión del congreso.

## Funciones disponibles

API Python, errores estructurados, CLI, lotes y metadata por cálculo. Las pruebas
cubren casos congelados, fases puras, conservación de componentes, validación de
entradas y límites de sílice. Los informes conservan comparaciones numéricas con
composiciones públicas y pyrolite, sus denominadores y convenciones.

GeoNormML declara la dependencia exacta 1.1.0. Sus pruebas de integración usan
los tres perfiles reales hasta variables, preprocesamiento y predicción
sintética, sin necesitar datos o modelos de investigación privados.

## Límites pendientes

Falta una comparación externa completa de todas las ramas de accesorios,
componentes menores y composiciones extremas, con entradas y resultados
normativos publicados y de procedencia conocida. Las pruebas existentes no
certifican mineralogía modal ni validez petrográfica universal.

El cierre puede incluir componentes libres y correcciones con signo: no implica
que la asignación mineral sea completa. Se deben inspeccionar estado y avisos.
Un mejor cierre tampoco demuestra una mejora en clasificación ML.

## Entrega

1.1.0 se distribuye separadamente de las versiones históricas. Se verifican
metadata, licencia, hashes, wheel real fuera del checkout y pruebas desde el
archivo fuente extraído, conforme a la [guía de publicación](PUBLISHING.md).
No se sustituyen artefactos históricos de PyPI ni perfiles de modelos entrenados.
