# Pruebas ampliadas de GeoNormPy

Ejecución del 26 de octubre de 2026 sobre 1.1.0.dev0. Resultado final:
388 pruebas aprobadas en 26,81 segundos, ninguna omitida. Incluye las tres
pruebas del wheel fuera del checkout. Las nuevas comprobaciones están en
tests/test_profile_properties.py y benchmarks/benchmark_accessories.py.
No se detectaron fallos nuevos del motor dentro de los casos comprobados.

## Conservación por componente

Se probaron 30.000 composiciones adicionales: dos perfiles nuevos, cinco
semillas, tres distribuciones y mil muestras por combinación. Distribuciones:
densa, dispersa con ceros y logarítmica con valores entre 1e-14 y 1e2.

La comprobación reconstruye cada óxido desde fórmulas minerales declaradas
independientemente del solver y los residuales. Desagrupa Mn, Ni, Co, Sr,
Ba, Rb, Cs, Li y V usando la composición de entrada; también contabiliza
el F normativo de Pruseth. No se limita a comprobar que una suma dé 100.

Se verificaron:

- Cada inventario de componente dentro de 2e-10 moles absolutos.
- Inventario total, incluido el déficit firmado, dentro de 1e-7 puntos
  porcentuales; balance de las asignaciones completas por debajo de 1e-7.
- Masas minerales finitas y no negativas; ausencia de cuarzo coexistente con
  olivino o feldespatoides por encima de la tolerancia indicada en la prueba.
- Serialización JSON estricta, sin NaN ni infinitos.
- Invariancia al orden de las entradas y al multiplicarlas por 1e-200 y
  1e200 en las primeras diez muestras de cada combinación: 900 cálculos
  adicionales, con tolerancia de 1e-8 puntos por mineral.

El barrido de sílice añade 2.002 composiciones, de 0 a 100 en incrementos
de 0,1, comprobando conservación por componente y ausencia de saltos mayores
de dos puntos porcentuales por mineral entre entradas consecutivas.
Esto es una comprobación numérica local, no una demostración matemática
de continuidad en todas las composiciones posibles.

## Hierro, reactivos limitantes y lotes

Se comparó hierro total frente a pares medidos equivalentes con fracciones
férricas 0, 0,01, 0,15, 0,5, 0,99 y 1 en los tres perfiles. También se
compararon FeOT y Fe2O3T en los nuevos perfiles. Los minerales coinciden
dentro de 1e-10 puntos porcentuales absolutos.

Hay cálculos manuales de halita, thenardita, pirita, fluorita, cromita e
ilmenita con reactivos limitantes, además de las tres hipótesis de carbonato.
Se comprobaron entradas negativas, booleanos, NaN, infinito, texto, listas
y diccionarios; sus errores se serializan como JSON estricto.
Los lotes mixtos conservan índices repetidos, muestras correctas y muestras
fallidas, con minerales vacíos en las filas fallidas.

## Comparación externa de accesorios

Se añadieron 2.000 comparaciones de Verma contra pyrolite 0.3.8.post1,
usando la química ajustada que devuelve el comparador como entrada común.
Esto iguala unidades, normalización y especiación antes de evaluar la
asignación. Se adopta explícitamente carbonato de sodio en esta comparación.

| Grupo | Muestras | Máxima diferencia por mineral, puntos porcentuales |
| --- | --- | --- |
| Sustituyentes y trazas | 500 | 0,003815 |
| Accesorios con reactivos suficientes | 500 | 0,002271 |
| Exceso de F | 500 | 0,002219 |
| Reactivos limitantes | 500 | 0,101811 |

Las 1.500 primeras muestras quedan por debajo de 0,01 puntos por mineral.
Las 500 del último grupo presentan su mayor diferencia en halita.
La métrica excluye apatita: sus salidas fluoradas y agregadas en el comparador
no se consideran una referencia independiente para esa fase.

Se aislaron tres casos para contrastar las diferencias con estequiometría:

| Caso aislado sobre la misma entrada ajustada | GeoNormPy, porcentaje en masa | pyrolite, porcentaje en masa |
| --- | --- | --- |
| Halita con Na limitante | 0,30172174 | 0,07542744 |
| Halita con Cl limitante cerca de la bifurcación | 0,08238197 | 0,07840533 |
| Pirita con S limitante cerca de la bifurcación | 0,09349236 | 0,27765163 |

En los tres casos, los moles de GeoNormPy coinciden con el cálculo manual:
halita = mínimo de 2 Na2O y Cl; pirita = mínimo de FeO y S/2.
La revisión del código del comparador muestra umbrales que no corresponden
a esas relaciones en las ramas identificadas. Por tanto, esas discrepancias
no justifican modificar GeoNormPy para imitar el resultado externo.

El error de masa local máximo de las 2.000 muestras externas fue 2,85e-14
puntos porcentuales. El [resumen de accesorios](../benchmarks/results/cipw_accessories_20261026.json)
incluye entradas ajustadas de los tres casos, valores manuales, resultados
y hashes del código y las pruebas.

## Reproducción y alcance

Ejecutar python -m pytest -q para la suite. Para incluir las pruebas del
paquete construido, definir GEONORMPY_AUDIT_WHEEL con la ruta del wheel.
benchmark_accessories.py requiere --reference-deps y --output, como el
ejecutor anterior; output debe ser un directorio nuevo.

Los CSV de esta ampliación están en
D:\DevResources\Sessions\GeoNormPy\accessories_20261026_1513_final.
Se conserva también la ejecución exploratoria anterior.

Estas pruebas amplían la evidencia numérica y las comprobaciones de ramas;
no prueban todas las composiciones ni certifican mineralogía modal.
No se modificaron datos, modelos ni el código del motor durante esta ampliación.
