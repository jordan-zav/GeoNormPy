# Benchmarks y métodos CIPW: revisión del 25 de octubre de 2026

## Qué utiliza GeoNormPy actualmente

La versión 1.0.0 se identifica como extended_cipw_v3. Sigue una asignación
secuencial de óxidos y ya incorpora transformaciones de subsaturación
procedentes de la norma revisada: hiperstena a olivino, titanita a perovskita,
albita a nefelina, ortoclasa a leucita y silicatos cálcicos a silicato dicálcico.
Por tanto, no es una copia intacta del procedimiento de 1902.

Eso tampoco significa que implemente íntegramente SINCLAS, Pruseth,
pyrolite o todos los accesorios de las revisiones modernas. El ajuste
del hierro total continúa usando una fracción férrica fija configurable;
el tratamiento de oxígeno libre, fósforo y halógenos requiere desarrollo.

## Diseño de los experimentos

Se utilizó el código local con la corrección numérica del diópsido. La
referencia fue pyrolite 0.3.8.post1, instalada en una carpeta separada,
con periodictable 2.1.0, NumPy 2.2.6 y pandas 2.3.3. El intérprete fue
Python 3.11.9. El runner y las salidas registran la semilla 20261025 y hashes.

Se compararon porcentajes en peso de 26 fases equivalentes, sin duplicar
los agregados de diopside, olivino e hiperstena presentes en la referencia.
Se igualaron primero las entradas de óxidos mayores y el reparto FeO/Fe2O3.
No se dejó que pyrolite estimara otro reparto de hierro. Mn se convirtió
previamente al mismo equivalente de FeO; volátiles y trazas se omitieron
de ambos motores en la comparación entre implementaciones.

El dataset público es CIPW_Verma_Test.csv, distribuido con pyrolite.
Se comparan cálculos nuevos sobre las mismas entradas, no las columnas
NORM antiguas, que pueden usar otros ajustes. La
[documentación de la referencia](https://pyrolite.readthedocs.io/en/main/examples/geochem/CIPW.html)
explica el origen y el uso de ese conjunto.

## Concordancia para óxidos mayores

Las diferencias son absolutas y se expresan en puntos porcentuales en peso.
La última columna resume solo normas completas; la cantidad de incompletas
se informa por separado y sus resultados están incluidos en los CSV.

| Entradas | Filas calculadas | Completas en GeoNormPy | Incompletas | Mayor diferencia en una fase, sobre completas |
| --- | ---: | ---: | ---: | ---: |
| Composiciones sintéticas de estrés | 2.000 | 937 | 1.063 | 0,001716 |
| Dataset público, química original armonizada | 551 | 521 | 30 | 0,001310 |
| Dataset público, columnas ADJ disponibles | 498 | 494 | 4 | 0,001211 |
| GeoNormML, química mayor armonizada | 2.755 | 2.735 | 20 | 0,001529 |

Ninguna norma completa de esos conjuntos superó 0,01 puntos de diferencia
en una fase; todas quedaron por debajo de 0,002. Esto respalda la concordancia
del núcleo de óxidos mayores con esta referencia bajo las condiciones fijadas.
No demuestra exactitud geológica ni valida las ramas de F, Cl, S o trazas.

Las 53 filas sin datos ADJ no se eliminaron del conjunto original de 551:
solo faltan en la comprobación secundaria de columnas ajustadas. Ambas
comprobaciones corresponden al mismo conjunto público, no son réplicas independientes.

## Robustez y controles independientes

| Control | Resultado |
| --- | --- |
| 33 composiciones de fases puras | Las 33 producen la fase esperada y asignación completa |
| Advertencias de masa en esos controles | 27; incluyen redondeo y diferencias de base de oxígeno |
| Conservación de inventarios, 2.000 composiciones de mayores | Error máximo 8,95 × 10^-16 mol |
| Conservación, otras 2.000 composiciones con volátiles y accesorios | Error máximo 5,13 × 10^-16 mol |
| Excepciones de cálculo en las 4.000 composiciones sintéticas | 0 |
| Asignaciones completas en el conjunto extendido | 772 de 2.000 |
| Cuarzo coexistiendo con olivino o feldespatoides en los conjuntos sintéticos | 0 casos |
| Escalado de 200 composiciones por cuatro factores, de 10^-250 a 10^250 | Diferencia máxima 1,32 × 10^-13 puntos |
| Invertir el orden de las claves de entrada | Diferencia máxima 1,42 × 10^-14 puntos |
| Código local frente al tag publicado, 200 composiciones aleatorias | Diferencia máxima 3,27 × 10^-10 puntos; sin cambios de saturación |

Las mezclas aleatorias de estrés incluyen composiciones extremas que no son
rocas plausibles. Sus normas incompletas pueden sumar mucho más de 100 al
mantener un déficit de sílice sin resolver. No deben reinterpretarse como
resultados válidos: cipw_safe las rechaza. Conservarlas en el benchmark permite
ver los límites del motor en lugar de ocultarlos mediante renormalización.

La comprobación de inventarios reconstruye equivalentes de óxidos, incluidos
los residuos. En haluros y sulfuros esa base incluye oxígeno desplazado y no
equivale a cerrar la masa elemental real; la contabilización de oxígeno libre
sigue pendiente.

Los tiempos de cada motor están en el JSON como observaciones de esta corrida.
No constituyen un benchmark estadístico de velocidad: no se hicieron múltiples
repeticiones con control de cachés, carga y plataforma.

## Sensibilidad a la hipótesis de hierro

Se tomó la misma química de 200 composiciones sintéticas y se repitió el
cálculo con fracciones atómicas Fe3+/Fe total de 0, 0,10, 0,15, 0,30 y 0,50.
Son 1.000 escenarios dependientes, no 1.000 muestras medidas.

Cuatro composiciones cambiaron de categoría de saturación. El rango máximo
de cuarzo normativo fue 10,126 puntos porcentuales; la mediana de rangos
fue cero porque muchas composiciones no producen cuarzo con ningún supuesto.
Esto justifica evaluar explícitamente la política de hierro antes de atribuir
una diferencia de norma al orden del algoritmo. No identifica una fracción
férrica correcta para cada muestra.

## Investigación posterior al CIPW clásico

| Trabajo | Aporte relevante para GeoNormPy |
| --- | --- |
| [Verma, Torres-Alvarado y Velasco-Tapia, 2003: A revised CIPW norm](https://www.researchgate.net/publication/233544669_A_revised_CIPW_norm) | Procedimiento estandarizado, masas moleculares variables y componentes libres, incluido oxígeno. Es una referencia para completar accesorios y trazabilidad del balance. |
| [Pruseth, 2009: Calculation of the CIPW norm: New formulas](https://literature.wolkersdorfer.info/literature/Calculation%20of%20the%20CIPW%20norm%20New%20formulas.pdf) | Reformulación mediante álgebra matricial y otro orden de cálculo, con atención a masas de apatita, fluorita y pirita y errores de redondeo. Sería un perfil metodológico separado, no un parche intercambiable. |
| [WebNORM, 2023](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2023.1232256/full) | Compara implementaciones y muestra la importancia de armonizar hierro y elementos menores. Usa pyrolite: no puede contarse como otra referencia computacional independiente en este benchmark. |
| [shinyNORRRM, 2023](https://link.springer.com/article/10.1007/s11004-023-10052-2) | Implementación abierta en R con elementos menores y traza y varios ajustes de hierro. Es una candidata a segunda referencia; no se ejecutó aquí. |
| [Borisov y colaboradores, 2025: modelo para fundidos félsicos](https://research.uni-hannover.de/en/publications/ferricferrous-ratio-in-silicate-melts-a-model-calibrated-for-fels/) | Relaciona el reparto férrico/ferroso con composición, temperatura y fugacidad de oxígeno. Su calibración experimental no autoriza a aplicarlo sin esos datos ni a toda roca total. |
| [ARMADILLO_VolcaNorm, 2026](https://www.sciencedirect.com/science/article/pii/S0895981126000544) | Herramienta abierta para rocas volcánicas con siete opciones de reparto del hierro y entradas adicionales según el modelo. Se consultó su publicación; no se ejecutó la hoja Excel. |

Estas publicaciones muestran que la investigación continúa, pero no prueban
que la herramienta más reciente produzca la mineralogía modal real. El objetivo
de una norma y la exactitud de su implementación deben evaluarse por separado.

## Mejoras recomendadas, en orden

1. Armonizar las masas minerales y la tolerancia de advertencia. Los 27 avisos
   en controles puros hacen que un aviso no discrimine bien entre redondeo y
   un problema químico real. Mantener el error bruto disponible.
2. Contabilizar oxígeno libre y residuos en una salida explícita, distinguiendo
   cierre de inventario y cierre gravimétrico. No forzar los minerales a 100.
3. Completar y contrastar apatita con F, la prioridad del fósforo y la competencia
   de Ca con carbonatos y fluorita. Incorporar estas decisiones en un perfil
   versionado, conservando extended_cipw_v3 para reproducir los resultados previos.
4. Añadir políticas de hierro seleccionables: valores medidos, fracción fija
   y métodos publicados cuando existan las entradas necesarias. Mantener el
   método y sus parámetros en cada resultado; no estimarlos en silencio.
5. Evaluar masas variables para sustituciones menores y una segunda referencia
   realmente independiente, con datos y normas publicadas de procedencia conocida.
6. Antes de usar un perfil nuevo en GeoNormML, comparar variables y normas,
   conservar las 2.755 muestras y evaluar el efecto sobre modelos por separado.

No se implementaron automáticamente esas modificaciones científicas en esta
corrida. El resultado principal es que el núcleo de mayores ya presenta
concordancia estrecha; las mejoras prioritarias se concentran en diagnóstico,
accesorios y supuestos de hierro, no en sustituirlo sin evidencia.

## Reproducibilidad y entregables

El runner está en [benchmarks/benchmark_cipw.py](../benchmarks/benchmark_cipw.py)
y su [guía de ejecución](../benchmarks/README.md). El resumen contiene versiones,
hash del motor, hash del dataset público y del dataset local, hash del código
del tag 1.0.0 y la semilla. Las salidas se guardan fuera del repositorio:

D:\DevResources\Sessions\GeoNormPy\benchmark_20261025_1792981387384\results_final

Incluyen summary.json, CSV de controles, comparaciones por fila y sensibilidad,
y benchmark_comparison.png y .pdf. Los intentos iniciales se conservaron:
uno detectó columnas enteras implícitas en la referencia con NumPy 2 y otro
las 53 filas sin ADJ. El adaptador final utiliza ceros flotantes explícitos y
separa las dos bases de entrada; no se modificó la biblioteca de referencia.

No se reemplazaron datos, modelos ni normas guardadas. No se entrenaron
clasificadores, se publicaron versiones ni se hizo commit o push.
