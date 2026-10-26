# Revisión independiente del cálculo CIPW de GeoNormPy 1.0.0

Se recibió por avance rápido la actualización 7d0b4e8. El AGENTS local se
respaldó antes de integrar el nuevo archivo y se conservaron sus instrucciones
adicionales. La revisión distingue errores numéricos de las convenciones y
limitaciones científicas que la versión ya documentaba.

## Error reproducido y corregido: saturación del diópsido

Una entrada formada por un mol de CaO, un mol de MgO y dos moles de SiO2
contiene exactamente la estequiometría de CaMgSi2O6. El motor publicado
devolvía diópsido pero marcaba silica_saturation como undersaturated.

El reparto de Mg y Fe usaba como denominador MgO + FeO + EPS. La suma de
las proporciones quedaba ligeramente por debajo de uno; el remanente artificial
de Mg/Fe introducía demanda adicional de sílice. La rama ya exige que MgO + FeO
sea positivo, por lo que no hace falta sumar EPS a ese denominador.

Se usa el cociente exacto y la cantidad de hedenbergita se calcula como el
resto del clinopiroxeno asignado. Se añadieron siete controles entre los
extremos magnésico y ferroso. La comparación con el código del commit
recibido reproduce el cambio undersaturated a saturated en el extremo
magnésico; los otros seis controles conservan su diagnóstico.

No se modificaron el orden normativo, las masas molares ni la política de
hierro. El test comprueba saturación, fases, proporción Mg/Fe, ausencia de
residuos y terminación completa, sin afirmar una suma exactamente 100 con
masas minerales redondeadas.

## Puntos pendientes del modelo

### Balance de oxígeno en F, Cl y S

En los controles estequiométricos siguientes el motor asigna todos los
componentes, pero calcula el cierre sobre la masa de óxidos y elementos
iniciales sin declarar por separado el oxígeno liberado:

| Control | Suma mineral, % | calculation_complete |
| --- | ---: | --- |
| CaO + 2 F, fluorita | 82,9852 | true |
| 0,5 Na2O + Cl, halita | 87,9597 | true |
| FeO + 2 S, pirita | 88,2439 | true |

La diferencia no prueba una pérdida de Ca, Na o Fe: sustituir el oxígeno
de sus óxidos por halógenos o azufre cambia la base gravimétrica. Falta
contabilizar ese oxígeno y distinguir el cierre químico completo del simple
consumo del inventario. Una renormalización ciega de los minerales a 100 no
resolvería la trazabilidad. Esta limitación ya consta en la revisión anterior.
La [implementación de referencia de pyrolite](https://pyrolite.readthedocs.io/en/main/_modules/pyrolite/mineral/normative.html)
contabiliza componentes libres, incluido oxígeno.

### Prioridad de apatita y competencia por Ca

GeoNormPy consume Ca en calcita y fluorita antes de formar apatita. En un
control con 10/3 mol de CaO, un mol de P2O5 y un mol de CO2, forma calcita,
solo asigna el 70 % del fósforo a apatita y deja P2O5 residual.

La norma revisada de [Verma y colaboradores, 2003](https://www.researchgate.net/publication/233544669_A_revised_CIPW_norm)
forma apatita antes de fluorita y carbonatos, e incluye el uso de F en apatita.
La versión actual difiere en esa rama. No se cambió automáticamente esta
convención: modificarla altera las normas de composiciones con Ca limitado
y requiere una decisión metodológica explícita y nuevas comparaciones.

### Advertencias de masa por redondeo

La apatita estequiométrica devuelve 99,99777 % y la albita 100,00038 % con
las masas tabuladas actuales. Ambas activan mass_balance_warning porque
mass_tol predeterminado es 0,000001 puntos porcentuales, mucho menor que
el redondeo de las masas minerales. Esas advertencias no deben interpretarse
como errores de análisis. Queda pendiente armonizar las masas o documentar
una tolerancia coherente, sin esconder residuos químicos reales.

## Comprobación sobre la base local de GeoNormML

Se recalcularon en memoria las 2.755 filas curadas, seleccionando únicamente
los componentes admitidos. No se escribieron normas en Excel ni se cambiaron
datasets, modelos, etiquetas o resultados anteriores.

| Control | Resultado |
| --- | ---: |
| Errores de ejecución de cipw | 0 |
| Filas con asignación incompleta | 20 |
| Filas con error gravimétrico mayor que 0,01 puntos porcentuales | 33 |
| Filas con error gravimétrico mayor que 0,10 puntos porcentuales | 14 |
| Mayor error gravimétrico observado, puntos porcentuales | 0,4384 |
| Filas con diferencia mayor que 0,01 puntos en algún mineral previamente guardado | 2 |

Las veinte filas incompletas dejan P2O5 sin asignar y deben conservarse para revisión: este resultado
no autoriza a retirarlas de la base curada. La API cipw permite inspeccionar
la norma parcial; cipw_safe y el procesamiento por lotes las rechazan. Por
tanto, una regeneración del dataset con la API nueva puede cambiar también
el tratamiento de fallos. Los dos cambios de abundancias comparan esta versión
con las columnas normativas almacenadas; no son una mejora demostrada de ML.

## Validación y alcance

La suite inicial dio 174 pruebas correctas y una omitida. Después de la
corrección numérica: 181 correctas y una omitida. La omitida requiere un wheel
compilado y prueba su CLI fuera del checkout; esta revisión del cálculo usó
el código fuente. Se actualizó la instalación editable del entorno a 1.0.0,
sin generar paquetes de distribución ni publicar versiones.

Se contrastó el orden de desaturación con la fuente de pyrolite: las
transformaciones de Hy, titanita, albita, ortoclasa y silicatos cálcicos de
la actualización son coherentes con esa referencia. No se ejecutó una
comparación exhaustiva entre implementaciones sobre patrones certificados.
La conservación estequiométrica y los tests no certifican exactitud geológica.

Los controles reproducibles y el resumen numérico se guardaron en
O:\0. Projects\RepoSyncLogs con prefijo geonormpy y fecha 20261025. La corrección
queda local, sin commit, push ni publicación. Los modelos ML no se reentrenaron.
