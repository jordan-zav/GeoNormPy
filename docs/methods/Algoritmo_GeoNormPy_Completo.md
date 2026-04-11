# Algoritmo completo de GeoNormPy

## Propósito general

GeoNormPy es un motor de cálculo de mineralogía normativa CIPW a partir de análisis geoquímicos de roca total expresados como porcentajes en peso de óxidos. Su objetivo no es reconstruir la mineralogía modal real observada al microscopio, sino traducir una composición química global en un ensamblaje normativo ideal, químicamente coherente y reproducible.

El algoritmo trabaja en base anhidra, transforma los óxidos a moles, reparte la química en una secuencia fija de minerales normativos y finalmente vuelve a expresar el resultado como porcentajes en peso de minerales. Toda la lógica está organizada para respetar prioridades estequiométricas: primero se retiran componentes volátiles y accesorios que no deben competir con los silicatos mayores; luego se asignan aluminio y álcalis; después se resuelven los silicatos máficos; y por último se decide el estado de saturación en sílice.

## Entradas admitidas

El cálculo puede recibir, según disponibilidad, los siguientes óxidos o componentes:

- SiO2
- TiO2
- Al2O3
- Fe2O3
- FeO
- FeOT
- MnO
- MgO
- CaO
- Na2O
- K2O
- P2O5
- ZrO2
- Cr2O3
- CO2
- S
- F
- Cl
- SO3

No todos son obligatorios. El algoritmo admite entradas parciales, pero la calidad interpretativa del resultado dependerá de cuánta información esté disponible.

## Salidas generadas

GeoNormPy devuelve cuatro bloques conceptuales:

- Minerales normativos en moles.
- Minerales normativos en porcentaje en peso.
- Banderas diagnósticas sobre hierro, saturación en sílice, estado del aluminio y balance de masa.
- En modo de depuración, óxidos residuales no consumidos.

Cuando el motor habla de "moles de minerales", se refiere a moles de fórmula mineral normativa. Ese detalle es importante porque minerales como Or y Ab se forman a partir de óxidos alcalinos dobles como K2O y Na2O, pero el inventario interno queda almacenado como moles de fórmula de feldespato, no como moles del óxido precursor. Por eso las transformaciones posteriores en subsaturación deben leerse siempre en términos de fórmulas minerales ya formadas.

Los minerales que puede producir son:

- Q, Cor, Or, Ab, An
- Le, Ne, Kp
- Ac, Di, Hd, Wo, En, Fs, Fo, Fa
- Mt, Hm, Ilm, Cm, Ru, Tn, Z, Ap
- Cc, Py, Fl, Hl, Th
- ns, ks

## Estructura lógica global

La secuencia real del motor es la siguiente:

1. Normalizar la composición a 100 % en base anhidra.
2. Resolver la especiación del hierro.
3. Volver a normalizar a 100 % tras el tratamiento del hierro.
4. Convertir todos los óxidos a moles.
5. Formar fases volátiles y sales.
6. Formar minerales accesorios.
7. Evaluar el estado de saturación en aluminio sobre el CaO realmente disponible para silicatos.
8. Formar feldespatos, corindón, acmita y silicatos alcalinos residuales.
9. Formar óxidos de hierro.
10. Formar silicatos máficos.
11. Resolver la saturación o subsaturación en sílice.
12. Limpiar residuos numéricos.
13. Convertir moles minerales a porcentaje en peso.
14. Medir el error de balance de masa y producir flags de control.

Lo importante es que el orden no es decorativo. El resultado depende directamente de esta jerarquía de consumo químico.

## Paso 1. Normalización inicial

El algoritmo primero elimina valores nulos y suma todos los componentes reportados. Si la suma total es menor o igual a cero, el cálculo se detiene porque no existe una base química válida.

Después, cada óxido se reescala para que la suma total sea exactamente 100 %. Esto asegura que todas las muestras entren al cálculo en una base comparable.

La lógica no intenta corregir humedad, pérdida por ignición ni agua estructural. Solo trabaja con la química entregada y la trata como base anhidra utilizable.

## Paso 2. Manejo jerárquico del hierro

El hierro es el punto más delicado del algoritmo porque puede venir informado de varias maneras. GeoNormPy no lo inventa en silencio; aplica una jerarquía explícita y registra qué hizo.

### Caso A. FeO y Fe2O3 medidos

Si ambos existen y no viene FeOT, el algoritmo usa directamente esos valores. El modo se marca como `measured`.

### Caso B. Solo FeO o solo Fe2O3

Si solo aparece uno de los dos y no existe FeOT, el faltante se fija en cero. El modo se marca como `partial_assumed` y se genera advertencia, porque el dato es utilizable pero incompleto.

### Caso C. Solo FeOT

Si solo viene el hierro total, se divide en FeO y Fe2O3 usando una fracción fija de Fe3+ sobre hierro total. Por defecto se usa 0.15. El Fe2O3 equivalente se ajusta estequiométricamente para que represente masa de Fe2O3, mientras que el resto queda como FeO. El modo se marca como `estimated_from_FeOT` y también se registra advertencia.

### Caso D. Entrada inconsistente

Si aparece FeOT junto con FeO o Fe2O3, la entrada se considera inconsistente. El algoritmo lo marca como `inconsistent_input`. En modo estricto, se detiene con error. En modo no estricto, elimina FeOT y continúa con lo demás, dejando advertencia.

### Caso E. Sin hierro

Si no hay ninguna forma de hierro, el algoritmo fija FeO y Fe2O3 en cero, marca el modo como `missing` y deja advertencia.

### Conversión adicional de MnO

Si existe MnO, GeoNormPy lo transforma a equivalente de FeO sobre base molar y lo suma al FeO disponible. Esto sigue la convención normativa clásica en la que MnO acompaña al hierro ferroso dentro del reparto máfico.

## Paso 3. Renormalización después del hierro

Una vez resuelta la química del hierro, la composición se vuelve a normalizar a 100 %. Este paso es importante porque el tratamiento de FeOT y MnO modifica el conjunto de componentes disponibles. La renormalización impide que el resto del algoritmo trabaje con una suma desplazada.

## Paso 4. Conversión de porcentaje en peso a moles

Cada óxido se divide por su masa molar. Desde este punto en adelante, toda la lógica interna trabaja en moles, no en porcentaje en peso.

Esto es imprescindible porque la estequiometría normativa se define en relaciones molares. El porcentaje en peso solo se recupera al final.

## Paso 5. Formación de volátiles y sales

Antes de entrar a los silicatos, GeoNormPy retira primero varios componentes que químicamente no deben competir con el núcleo silicatado principal. Todo este bloque suma además una bandera llamada `volatile_fraction_moles`.

### Calcita normativa

Si hay CO2, se combina con CaO para formar calcita (`Cc`). La cantidad formada es el mínimo entre CO2 y CaO. Ambos se consumen en la misma proporción molar.

### Fluorita normativa

Si hay F, se forma fluorita (`Fl`) usando CaO. Como CaF2 requiere dos átomos de flúor por unidad mineral, la cantidad de fluorita es el mínimo entre F/2 y CaO.

### Pirita normativa

Si hay azufre elemental reportado como S, se forma pirita (`Py`) usando FeO. Como FeS2 requiere dos átomos de azufre, la cantidad mineral es el mínimo entre S/2 y FeO.

### Halita normativa

Si hay Cl, se forma halita (`Hl`) consumiendo Na2O. La lógica usa el mínimo entre Cl y dos veces Na2O, porque cada mol de Na2O puede aportar dos sodios para sal. Internamente `Hl` se guarda como moles de fórmula de NaCl, que numéricamente coinciden con los moles de Cl consumidos porque cada unidad de halita contiene exactamente un Cl.

### Thenardita normativa

Si hay SO3, se forma thenardita (`Th`) consumiendo Na2O en relación 1 a 1.

Este bloque es importante porque puede drenar Ca, Fe o Na antes de que esos elementos entren en feldespatos o silicatos máficos.

## Paso 6. Formación de minerales accesorios

Luego se retiran minerales accesorios que deben fijarse tempranamente.

### Circón

Si hay ZrO2, se forma circón (`Z`) consumiendo ZrO2 y la misma cantidad molar de SiO2.

### Apatita

GeoNormPy sigue aquí la convención CIPW clásica usada por la norma histórica. La apatita se representa como `Ca(10/3)(PO4)2`, equivalente a `3.33CaO·P2O5`, tal como está definida también en la tabla interna de minerales normativos. Por eso la cantidad de apatita es el mínimo entre P2O5 disponible y CaO dividido entre `10/3`, y cada mol de P2O5 consume `10/3` moles de CaO dentro de esta representación normativa.

Esta convención no coincide con la fórmula mineralógica completa de apatita, pero sí con la representación normativa clásica de Cross, Iddings, Pirsson y Washington. En GeoNormPy debe mantenerse consistente con la masa molar normativa de `Ap`; por eso no se debe cambiar la razón CaO/P2O5 sin actualizar al mismo tiempo la definición mineral y las pruebas.

### Cromita normativa

Si hay Cr2O3, se forma cromita (`Cm`) consumiendo Cr2O3 y FeO en relación 1 a 1.

### Ilmenita

Si hay TiO2 y FeO, se forma ilmenita (`Ilm`) en relación 1 a 1.

### Titanita

Después de formar ilmenita, el TiO2 que aún quede puede pasar a titanita (`Tn`) si simultáneamente existe CaO y SiO2. La cantidad de titanita es el mínimo entre TiO2, CaO y SiO2.

### Rutilo

El TiO2 que siga sobrando después de ilmenita y titanita se asigna a rutilo (`Ru`).

Con este diseño, GeoNormPy evita dejar titanio libre sin destino normativo.

## Paso 7. Estado químico del aluminio

Una vez retirados volátiles y accesorios, GeoNormPy diagnostica la relación entre Al2O3 y la suma de CaO, Na2O y K2O que todavía quedan disponibles para silicatos. Usa la relación:

Al2O3 / (CaO + Na2O + K2O)

con una tolerancia numérica muy pequeña para evitar divisiones inestables.

La interpretación es:

- Si Na2O + K2O es mayor que Al2O3, la muestra se marca como peralcalina.
- Si la relación anterior es mayor que 1, la muestra se marca como peraluminosa.
- En cualquier otro caso se marca como metaluminosa.

Este diagnóstico se hace sobre el calcio remanente después de que calcita, fluorita, apatita y titanita hayan retirado su parte. Por eso es más representativo del CaO realmente disponible para feldespatos y silicatos.

## Paso 8. Feldespatos, aluminio residual y álcalis remanentes

Este es uno de los núcleos del algoritmo porque fija el reparto del aluminio y una parte grande del sodio, potasio y calcio.

### Ortoclasa

La ortoclasa (`Or`) se forma con el mínimo entre K2O y Al2O3. Al producirla, el algoritmo consume:

- 1 mol de K2O
- 1 mol de Al2O3
- 6 moles de SiO2

y produce 2 moles de Or.

La producción de 2 moles refleja que una unidad de K2O contiene dos cationes K capaces de generar dos fórmulas normativas de feldespato. Desde este punto, el inventario de `Or` ya está expresado como moles de fórmula mineral de ortoclasa.

### Albita

La albita (`Ab`) se forma con el mínimo entre Na2O y Al2O3. Consume:

- 1 mol de Na2O
- 1 mol de Al2O3
- 6 moles de SiO2

y produce 2 moles de Ab.

Igual que en la ortoclasa, esos moles ya son moles de fórmula mineral de albita.

### Anortita

La anortita (`An`) se forma con el mínimo entre CaO y Al2O3. Consume:

- 1 mol de CaO
- 1 mol de Al2O3
- 2 moles de SiO2

y produce 1 mol de An.

### Corindón

Si tras Or, Ab y An aún queda Al2O3, ese remanente forma corindón (`Cor`). Esto expresa el exceso normativo de alúmina.

### Acmita

Después del corindón, si todavía existen Na2O y Fe2O3, el algoritmo forma acmita (`Ac`). Consume:

- 1 mol de Na2O
- 1 mol de Fe2O3
- 4 moles de SiO2

y produce 2 moles de Ac.

Este paso es especialmente relevante en composiciones peralcalinas o con hierro férrico residual.

### Silicatos alcalinos residuales

Si aún queda Na2O después de todo lo anterior, se transforma en metasilicato sódico (`ns`) consumiendo la misma cantidad molar de SiO2.

Si aún queda K2O, se transforma en metasilicato potásico (`ks`) consumiendo también SiO2 en relación 1 a 1.

Estos minerales residuales permiten cerrar químicamente el exceso alcalino sin dejar álcalis libres.

## Paso 9. Óxidos de hierro

Una vez repartidos aluminio y álcalis, GeoNormPy consume el hierro férrico restante en óxidos.

### Magnetita

La magnetita (`Mt`) se forma usando el mínimo entre Fe2O3 y FeO. Ambos se consumen en relación 1 a 1.

### Hematita

El Fe2O3 que sobreviva después de formar magnetita pasa a hematita (`Hm`).

Este diseño implica que la magnetita solo aparece cuando coexistían simultáneamente Fe3+ y Fe2+ disponibles en este punto del algoritmo.

## Paso 10. Silicatos máficos

Aquí se organiza el reparto de MgO, FeO y CaO remanentes dentro de los silicatos ferromagnesianos.

### 10.1. Clinopiroxenos cálcicos

Primero se calcula cuánto MgO y FeO total queda disponible. A esa suma se le puede llamar reserva máfica ferromagnesiana.

Si hay reserva máfica mayor que cero, el algoritmo forma clinopiroxeno total igual al mínimo entre CaO y la suma MgO + FeO.

Sin embargo, en vez de producir un solo mineral mixto, reparte ese clinopiroxeno proporcionalmente según la fracción de magnesio y hierro disponibles:

- La parte magnésica se convierte en diópsido (`Di`).
- La parte ferrosa se convierte en hedenbergita (`Hd`).

En ambos casos se consumen en conjunto:

- 1 mol de CaO por cada mol total de clinopiroxeno
- 1 mol de MgO o FeO según proporción
- 2 moles de SiO2 por mol total de clinopiroxeno

Este detalle es central: GeoNormPy no usa una división arbitraria entre Di y Hd, sino una partición proporcional al inventario real Mg/Fe del sistema remanente.

### 10.2. Ortopiroxenos

Una vez retirado el clinopiroxeno, todo MgO y FeO restante se asigna a ortopiroxeno:

- MgO remanente forma enstatita (`En`).
- FeO remanente forma ferrosilita (`Fs`).

Cada mol de MgO o FeO consume un mol de SiO2.

### 10.3. Wollastonita directa

Si después de los piroxenos aún queda CaO y ya no queda prácticamente ni MgO ni FeO, el CaO residual se combina con SiO2 para formar wollastonita (`Wo`) en relación 1 a 1.

Este paso captura el calcio silicatado restante cuando ya no existe pareja ferromagnesiana para seguir formando piroxenos.

## Paso 11. Resolución de la saturación en sílice

Este bloque decide si la composición final es sobresaturada, saturada o subsaturada. El criterio se basa en el SiO2 restante después de haber formado todos los minerales anteriores.

### Caso 1. Saturación exacta

Si el valor residual de SiO2 es prácticamente cero dentro de una tolerancia numérica muy pequeña, la muestra se marca como `saturated`.

### Caso 2. Exceso de sílice

Si queda SiO2 positivo, ese excedente forma cuarzo (`Q`). La muestra se marca como `oversaturated`.

### Caso 3. Déficit de sílice

Si el SiO2 residual es negativo, la muestra se marca como `undersaturated`. En ese caso el algoritmo no se limita a reportar el déficit; reorganiza minerales ya formados para recuperar sílice y adaptarse a una composición subsaturada.

Ese reajuste ocurre por etapas.

#### 11.1. Conversión de ortopiroxeno a olivino

El primer candidato a ser reducido es el ortopiroxeno ya formado, es decir, la suma En + Fs.

El algoritmo calcula cuánto déficit existe y determina cuánta hiperstena puede deshacerse para recuperar sílice. La reducción máxima posible es el mínimo entre:

- la cantidad total de En + Fs ya presente
- dos veces el déficit de sílice

Luego reparte esa reducción según la misma proporción En/Fs existente:

- La parte reducida de En pasa a forsterita (`Fo`).
- La parte reducida de Fs pasa a fayalita (`Fa`).

Como el olivino requiere menos sílice que el ortopiroxeno, esta transformación disminuye el déficit.

#### 11.2. Conversión de ortoclasa a leucita

Si aun después del paso anterior sigue faltando sílice, el algoritmo reduce primero la ortoclasa (`Or`) y la transforma en leucita (`Le`) en relación 1 a 1, siguiendo la prioridad potásica implementada para la rama subsaturada.

Cada mol de Or convertido a Le recupera un mol de déficit de sílice, porque ambos se almacenan como moles de fórmula mineral y la relación estequiométrica normativa es:

`KAlSi3O8 = KAlSi2O6 + SiO2`

#### 11.3. Conversión de leucita a kalsilita

Si el sistema sigue siendo aún más subsaturado, la leucita ya formada puede reducirse adicionalmente a kalsilita (`Kp`) también en relación 1 a 1.

Cada mol de Le convertido a Kp recupera un mol adicional de déficit de sílice, porque la relación normativa es:

`KAlSi2O6 = KAlSiO4 + SiO2`

#### 11.4. Conversión de albita a nefelina

Si todavía hay déficit después de agotar la rama potásica, el algoritmo intenta reducir la albita (`Ab`) ya formada. La cantidad reducible es el mínimo entre la albita existente y la mitad del déficit residual. La albita reducida se transforma en nefelina (`Ne`).

Cada mol de Ab convertido a Ne recupera dos moles de déficit de sílice, porque la relación normativa es:

`NaAlSi3O8 = NaAlSiO4 + 2SiO2`

### Déficit residual extremo

Si incluso después de todas estas conversiones persiste déficit de sílice, GeoNormPy guarda ese valor en la bandera `residual_silica_deficit_moles`. Eso significa que la secuencia normativa estándar no logró absorber completamente la subsaturación con los minerales previstos.

Al final de este paso el SiO2 residual interno se fuerza a cero para cerrar el sistema mineralógico y se eliminan minerales con cantidades numéricamente despreciables.

## Paso 12. Limpieza numérica

Durante todo el cálculo, GeoNormPy aplica una tolerancia extremadamente pequeña para distinguir entre ruido numérico y materia real.

Las reglas son:

- Si un valor residual absoluto es menor que la tolerancia, se lleva a cero.
- Ningún óxido distinto de SiO2 puede quedar negativo; si eso pasa, el algoritmo considera que hubo una inconsistencia y lanza error.
- Los minerales con cantidades menores o iguales a la tolerancia se eliminan del resultado final.

Esto vuelve el motor más estable frente a errores de redondeo.

## Paso 13. Conversión a porcentaje en peso

Una vez cerrada la mineralogía normativa en moles, cada mineral se multiplica por su masa molar ideal para obtener su masa correspondiente.

Luego cada masa mineral se expresa como porcentaje respecto a la masa total de entrada, que después de la normalización es 100. Por eso, en condiciones ideales, la suma de porcentajes minerales también debe acercarse a 100.

## Paso 14. Balance de masa y control de calidad

El algoritmo suma todos los porcentajes minerales y calcula:

|100 - suma_real|

Ese valor se guarda como `mass_balance_error`.

Además, compara ese error con una tolerancia configurable:

- Si el error supera la tolerancia, activa `mass_balance_warning`.
- Si no la supera, deja esa bandera en falso.

En modo de depuración también devuelve los óxidos remanentes en moles y en masa, siempre que no hayan quedado anulados por la limpieza numérica.

## Cómo interpreta GeoNormPy el resultado

El resultado final no es solo una lista de minerales. También resume el comportamiento químico de la muestra:

- `silica_saturation` indica si el sistema es sobresaturado, saturado o subsaturado en sílice.
- `alumina_state` indica si es peraluminoso, metaluminoso o peralcalino.
- `iron_mode` indica cómo se resolvió la especiación del hierro.
- `warnings` recopila todas las decisiones asumidas o situaciones problemáticas.
- `residual_silica_deficit_moles` indica si quedó subsaturación extrema no resuelta completamente.

## Flujo completo integrado en una sola narración

Si se resume todo en una sola secuencia conceptual, GeoNormPy funciona así:

Primero toma una composición química de roca total, la normaliza y resuelve el hierro de forma jerárquica para no mezclar datos medidos con supuestos ocultos. Después pasa toda la química a moles porque el reparto normativo solo tiene sentido en relaciones estequiométricas. Antes de formar los silicatos principales, retira los componentes volátiles y los accesorios como calcita, fluorita, pirita, halita, thenardita, circón, apatita, cromita, ilmenita, titanita y rutilo. Con la química remanente diagnostica el estado del aluminio y luego asigna el aluminio y los álcalis a ortoclasa, albita, anortita, corindón, acmita y silicatos alcalinos residuales. Luego consume el hierro férrico en magnetita y hematita. Después organiza el calcio, el magnesio y el hierro ferroso en clinopiroxenos, ortopiroxenos y, si corresponde, wollastonita. Solo al final mira cuánta sílice sobró o faltó. Si sobra, genera cuarzo. Si falta, reorganiza primero ortopiroxeno a olivino, luego reduce ortoclasa a leucita, después leucita a kalsilita y recién después albita a nefelina si la subsaturación persiste. Finalmente limpia residuos numéricos, convierte todo a porcentaje en peso, verifica el balance de masa y entrega tanto la mineralogía normativa como las banderas diagnósticas que explican cómo llegó a ese resultado.

## Qué hace especial a este algoritmo frente a un CIPW mínimo

GeoNormPy no implementa solo una versión reducida del CIPW clásico. Lo amplía en varios puntos importantes:

- Admite múltiples formas de entrada del hierro y deja trazabilidad de la decisión tomada.
- Convierte MnO a equivalente ferroso en vez de ignorarlo.
- Considera componentes volátiles y sales normativas.
- Incluye minerales accesorios adicionales como circón, cromita, titanita y rutilo.
- Separa clínicamente las fracciones magnésica y ferrosa del clinopiroxeno en Di y Hd.
- Permite fases peralcalinas y silicatos alcalinos residuales.
- Registra déficit residual de sílice y advertencias de balance de masa.

## Estado metodológico actual

Tras la auditoría de consistencia realizada sobre código y documentación, el estado metodológico de la implementación actual puede resumirse así:

- La rama subsaturada sigue el orden `En+Fs -> Fo+Fa`, luego `Or -> Le`, después `Le -> Kp` y finalmente `Ab -> Ne`.
- Los factores de recuperación de sílice de `Or`, `Le` y `Ab` están expresados en moles de fórmula mineral y son consistentes con la representación interna del inventario mineral.
- La apatita usa la convención CIPW clásica `Ca(10/3)(PO4)2`, no la fórmula mineralógica completa de apatita natural.
- El diagnóstico de saturación en aluminio se calcula después de retirar volátiles y accesorios, es decir, sobre el calcio realmente disponible para silicatos.
- `MnO` se transforma a equivalente de `FeO` y genera advertencia adicional cuando supera `0.5 wt%`.
- `Hl` se interpreta como moles de fórmula de `NaCl`, equivalentes numéricamente a los moles de `Cl` consumidos.

En consecuencia, el documento ya no describe una versión idealizada distinta del programa, sino la lógica efectiva de la implementación vigente.

## Limitaciones explícitas

El algoritmo sigue siendo normativo, no modal. Eso significa que:

- No reproduce texturas, zonaciones ni historia cristalina real.
- La asignación mineral depende totalmente del orden normativo fijado.
- La interpretación es más fuerte cuando la química está bien reportada y menos segura cuando el hierro o los volátiles deben asumirse.
- Un buen balance de masa no garantiza por sí mismo que la roca contenga realmente esos minerales en la naturaleza; solo indica coherencia interna del cálculo normativo.

## Conclusión

La lógica completa de GeoNormPy puede entenderse como un sistema de contabilidad química secuencial. Cada óxido entra con una cantidad determinada, se convierte a moles y va siendo retirado por minerales normativos en un orden fijo de prioridad. Ningún paso es independiente del anterior: lo que consumen los volátiles afecta a los accesorios; lo que consumen los accesorios afecta a los feldespatos; lo que dejan los feldespatos condiciona los silicatos máficos; y todo ello determina finalmente si el sistema termina con cuarzo, olivino o feldespatoides. El resultado final es una traducción sistemática de química total a ensamblaje normativo, acompañada por indicadores que dejan claro qué decisiones fueron medidas, cuáles fueron asumidas y qué tan bien cerró el balance químico.
