# Benchmarks CIPW

benchmark_cipw.py comprueba inventarios estequiométricos, minerales puros,
estabilidad numérica, sensibilidad al hierro y diferencias con pyrolite.
No modifica datasets ni entrena modelos. Requiere el tag local v1.0.0 para
la comparación con la versión publicada.

La referencia se instala en una carpeta de dependencias separada; no es
una dependencia de producción de GeoNormPy. La corrida documentada usa
pyrolite 0.3.8.post1 y periodictable 2.1.0. Sus dependencias auxiliares son
mpltern, sympy, mpmath y requests, con urllib3, charset-normalizer e idna.
Se reutilizan NumPy, pandas, scipy y matplotlib del entorno científico validado.

Ejecutar desde la raíz mediante DEVRESOURCES_RUN.cmd y el intérprete del
entorno aislado. La orden Python, con rutas elegidas para cada PC, es:

    python benchmarks/benchmark_cipw.py --reference-deps RUTA_DEPENDENCIAS --output CARPETA_NUEVA

Para añadir la base local sin escribir en ella:

    python benchmarks/benchmark_cipw.py --reference-deps RUTA_DEPENDENCIAS --output CARPETA_NUEVA --local-dataset RUTA_EXCEL_CURADO

La carpeta de salida debe ser nueva. --random-count controla el tamaño
de cada conjunto sintético; el valor predeterminado es 2.000. La semilla
es 20261025. El JSON registra versiones, hashes, tamaños y resultados;
los CSV y la figura PDF/PNG permiten examinar las diferencias.

## Límites de la comparación

Se igualan la química mayor, la normalización y la especiación de hierro.
Las ramas de volátiles y trazas se omiten en ambos motores para esta
comparación; se prueban por separado mediante inventarios y controles puros.
Mn se transforma previamente al equivalente de FeO en ambos motores.
Las columnas omitidas de la referencia reciben ceros flotantes explícitos
para este experimento controlado. No representan nuevas mediciones.

La concordancia se resume sobre normas que GeoNormPy marca como completas,
y se informa también el número de incompletas. Los CSV incluyen ambas.
No se compara con los valores normativos históricos guardados en el CSV
público: se vuelve a ejecutar pyrolite con los mismos datos de entrada.

El conjunto público de 551 análisis procede del material de prueba incluido
en pyrolite. Sus columnas ADJ solo están disponibles en 498 filas, por lo
que esa segunda comparación tiene un denominador distinto y no constituye
otro conjunto independiente. Las composiciones sintéticas de estrés no
representan una distribución de rocas naturales.

Los intervalos de sensibilidad al hierro son escenarios sobre una misma
química, no mediciones nuevas. Acuerdo entre programas y conservación de
inventarios no equivalen a validación petrográfica ni mineralogía modal.

Resultados e interpretación: [benchmark y revisión bibliográfica](../docs/benchmarks_y_metodos_cipw_20261025.md).

## Comparación de perfiles 1.1

benchmark_profiles.py ejecuta los tres perfiles sobre 2 000 composiciones
sintéticas mayores y 2 000 extendidas por perfil, además del conjunto público
y, opcionalmente, la química local de GeoNormML. Usar --output con un directorio
nuevo, --reference-deps con las dependencias aisladas de pyrolite y
--local-dataset con el Excel opcional. No escribe en los datos de entrada.

Para Pruseth se omiten Cl y SO3 en el experimento extendido y se excluye
apatita de la métrica de concordancia por mineral, porque su fluorapatita
normativa constituye otra convención; ambos valores de apatita quedan en CSV.
Las muestras incompletas también se conservan en los resultados. La comparación
externa sigue limitada a mayores con hierro y Mn previamente armonizados.

## Pruebas ampliadas de componentes y accesorios

tests/test_profile_properties.py reconstruye inventarios por componente sobre
30.000 composiciones, barre sílice y comprueba políticas de hierro equivalentes,
reactivos limitantes, entradas inválidas y conservación de filas en lotes.

benchmark_accessories.py compara 2.000 composiciones adicionales con pyrolite,
usando su química ajustada como entrada común. Admite --reference-deps y
--output con un directorio nuevo. Conserva las discrepancias de reactivos
limitantes y tres casos aislados contrastados con cálculos manuales.

Consultar [pruebas ampliadas y discrepancias identificadas](../docs/pruebas_ampliadas_20261026.md).
