# Perfiles CIPW y tratamiento del hierro

Implementación 1.1.0. Los perfiles se eligen explícitamente;
la llamada existente conserva extended_cipw_v3 como valor predeterminado.
La licencia sigue siendo GPL-3.0-or-later.

| Perfil | Asignación | Diferencias principales |
| --- | --- | --- |
| extended_cipw_v3 | Secuencial de GeoNormPy | Conserva las convenciones anteriores y la corrección numérica de piroxenos; versión de perfil 3.1. |
| verma2003 | Secuencial revisada | Masas de componentes sustituidos, apatita con y sin F medido, componentes libres y oxígeno desplazado. |
| pruseth2009 | Solución matricial provisional y reacciones | Fluorapatita normativa, matriz de siete componentes y reacción adicional de anortita ante déficit extremo de sílice. |

Los dos perfiles nuevos tienen versión de implementación de perfil 1.0.
El nombre del artículo identifica las reglas de asignación utilizadas, con las
convenciones de entrada y salida de GeoNormPy descritas a continuación.
No significa reproducción literal de todas las opciones del programa original.

## Uso en Python

Importar cipw y available_profiles desde geonormpy. La llamada
cipw(oxides, profile="verma2003", iron_policy="measured") calcula la norma con
las dos especies de hierro declaradas. oxides es un diccionario de mediciones.
La llamada cipw(oxides, profile="pruseth2009", iron_policy="fixed",
fe3_fraction=0.15) aplica una fracción atómica férrica explícita.

available_profiles() devuelve perfiles, versiones, componentes admitidos y
políticas disponibles. cipw_safe(oxides, profile="verma2003") devuelve el sobre
JSON de éxito o error; conserva la detección de asignaciones incompletas.

calculate_cipw_dataframe, en geonormpy.norms.batch, acepta las mismas opciones
profile, iron_policy, fe3_fraction, carbonate_mode, strict y mass_tol.

## Consola y YAML

Consultar perfiles: geonormpy profiles --json

Ejecutar: geonormpy run --config config/workflow.yaml --profile verma2003
--iron-policy measured --json

Las opciones de consola sustituyen la configuración para esa ejecución sin
reescribir el archivo YAML. La sección calculation admite:

    method: cipw
    profile: verma2003
    iron_policy: measured
    fe3_fraction: 0.15
    carbonate_mode: calcite
    strict: false
    mass_tol: 0.000001

Un perfil desconocido o una opción mal escrita produce un error explícito.

## Políticas de hierro independientes

| Política | Comportamiento |
| --- | --- |
| auto | Conserva FeO y Fe2O3 declarados; con hierro total utiliza fe3_fraction; informa especies ausentes. |
| measured | Exige FeO y Fe2O3 explícitos, incluidos ceros medidos. |
| fixed | Redistribuye el hierro total, conservando átomos, con Fe3+/Fe total = fe3_fraction. |
| le_maitre_volcanic | Estima la partición con SiO2 y álcalis, usando la ecuación volcánica de Le Maitre. |
| le_maitre_plutonic | Usa la ecuación plutónica de Le Maitre. |

FeOT expresa hierro total como FeO; Fe2O3T, admitido por los perfiles nuevos,
lo expresa como Fe2O3. No combinar un total con especies medidas. Las opciones
explícitas rechazan esa ambigüedad. auto conserva el comportamiento permisivo
anterior fuera de strict e informa la inconsistencia.

Le Maitre estima FeO/(FeO+Fe2O3) en masa: 0.93 − 0.0042 SiO2 − 0.022
(Na2O+K2O) para volcánicas; 0.88 − 0.0016 SiO2 − 0.027 (Na2O+K2O)
para plutónicas. Se limita a [0, 1] y se convierte a fracción atómica antes
de repartir el hierro. Se requieren las tres mediciones explícitas.
Estas políticas representan hipótesis de cálculo, no mediciones de redox.

## Convenciones y alcance científico

- Todas las entradas están en porcentaje en masa. F, Cl y S son elementos;
  las demás columnas son óxidos. No se infieren ppm ni se convierten nombres
  de elementos a óxidos. Convertir trazas antes de llamar a la API.
- GeoNormPy usa una base común: todos los componentes suministrados se
  normalizan a 100 antes y después de la política de hierro, sin redondeo
  intermedio. Verma describe primero la normalización de once mayores y luego
  la incorporación de menores. Esa preparación en dos etapas y su redondeo
  no se reproducen automáticamente. Para contrastar tablas externas hay que
  igualar previamente la composición ajustada, unidades y partición de hierro.
- No incluir agua ni LOI como óxidos normativos. Revisar la calidad analítica
  y la alteración antes de interpretar una composición anhidra.
- Mn, Ni y otros sustituyentes admitidos se agrupan molarmente con masas
  efectivas calculadas desde sus contribuciones. No se convierte su masa
  medida a una masa ficticia de FeO, CaO o álcalis.
- En Verma, F medido se asigna a fluorapatita antes que a fluorita. Ap expresa
  la apatita de tipo óxido y FAp la fluorapatita; no sumarlas de nuevo como
  un agregado adicional. Un mol de FAp corresponde a tres moles de P2O5.
- Pruseth utiliza fluorapatita normativa incluso sin F medido. Su aporte de
  F supuesto aparece como normative_F_correction negativo en los componentes
  libres y el oxígeno desplazado aparece como O positivo. Son correcciones
  contables explícitas. No constituyen un análisis químico de F.
- carbonate_mode es una hipótesis explícita. En Verma, calcite consume CO2 con
  CaO disponible; sodium_carbonate lo asigna a Nc; free conserva CO2 libre.
  No se implementa la estimación modal de cancrinita descrita por Verma.
  En ausencia de evidencia petrográfica del carbonato, usar free. Los otros
  perfiles conservan su convención de calcita.
- Pruseth rechaza CoO, Rb2O, Cs2O, Li2O, V2O3, Cl y SO3 no nulos, fuera del
  conjunto de componentes aquí implementado para ese artículo.
- Los perfiles no calculan equilibrio a presión, temperatura o fugacidad de
  oxígeno, ni reemplazan la mineralogía modal observada. No incluyen Middlemost.

## Balance y trazabilidad

Cada resultado incluye calculation_metadata con perfil, versión del perfil,
versión de GeoNormPy, política solicitada y aplicada, parámetros de hierro,
carbonato, tolerancia, unidades y normalización. También quedan en el CSV.

En los perfiles nuevos, total_mass_sum suma solamente minerales.
mass_balance.accounted_sum suma minerales y componentes libres, con sus signos.
mass_balance_error es la diferencia absoluta respecto de 100 de esa suma
corregida. No se renormalizan los minerales para forzar un cierre aparente.

Un componente libre declarado, como P2O5 sin calcio disponible, puede coexistir
con una asignación completa y genera una advertencia. Un déficit de sílice
sin resolver conserva calculation_complete=false: cipw permite inspeccionarlo,
cipw_safe lo devuelve como error y el lote deja minerales vacíos en esa fila.
Esta semántica revisada se distingue de la del perfil de compatibilidad.

En una muestra extrema, el inventario que incorpora el déficit negativo puede
cerrar a 100 aunque la norma siga incompleta. Ese cierre no valida la norma.

## Referencias y comprobaciones

La implementación utiliza las ecuaciones de [Verma, Torres-Alvarado y
Velasco-Tapia (2003), A revised CIPW norm](https://www.researchgate.net/publication/233544669_A_revised_CIPW_norm),
el método de [Pruseth (2009)](https://doi.org/10.1007/s12040-009-0010-0)
y la partición de [Le Maitre (1976)](https://doi.org/10.1007/BF00399603).
Las ecuaciones se implementaron localmente; pyrolite se usa como comparador
externo aislado y no es una dependencia de GeoNormPy.

Las pruebas incluyen fases puras, conservación de hierro, oxígeno desplazado,
apatita, sustituyentes, límites de entrada, integración de lotes y consola,
el ejemplo numérico publicado por Pruseth y veinte resultados congelados del
motor anterior. Los benchmarks adicionales se ejecutan con
benchmarks/benchmark_profiles.py. Consultar el
[informe de resultados](validacion_perfiles_20261026.md).

El estado declarado de los perfiles es numerically_benchmarked_not_petrologically_certified.
Las comparaciones entre implementaciones evalúan concordancia numérica sobre
entradas controladas; no son una certificación petrográfica independiente.
