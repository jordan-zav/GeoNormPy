<p align="center"><a href="README.md">English</a> · <strong>Español</strong></p>

# GeoNormPy

**Mineralogía normativa CIPW reproducible a partir de química de roca total.**

Convierte análisis de óxidos mayores en asociaciones minerales normativas,
diagnósticos y tablas auditables mediante Python o la línea de comandos.

> Una norma CIPW es un cálculo idealizado, no mineralogía modal medida. No
> sustituye la petrografía, las relaciones de campo ni un diagrama QAPF apropiado.

## Legacy y referencia al congreso

El trabajo anterior de GeoNormPy / GeoNormML fue **presentado como trabajo técnico
en el [XXIII Congreso Peruano de Geología (CPG XXIII)](https://congresosgp.org.pe/)**,
organizado por la Sociedad Geológica del Perú en 2026. Esa generación se conserva
como **Legacy**; sus cifras históricas no son los benchmarks vigentes.

GeoNormPy 1.0.0 se conserva como versión Legacy. El material del congreso anunciaba
0.1.1, otro corte temporal. El perfil extended_cipw_v3 3.1 corregido de 1.1.0 no es
idéntico a esas versiones. Verma 2003 y Pruseth 2009 son perfiles de cálculo, no
clasificadores entrenados. El cierre numérico no demuestra mayor precisión ML.
Consultar [los metadatos de cita](CITATION.cff) y la
[decisión de generaciones de GeoNormML](https://github.com/jordan-zav/GeoNormML/blob/main/docs/revisiones/modelos_legacy_y_vigentes.md).


## Alcance metodológico y crítica

Las pruebas del motor comprueban comportamiento numérico, inventarios y errores
en los casos documentados; no certifican mineralogía modal ni precisión de un
clasificador. Un inventario puede cerrar incluyendo componentes libres y
correcciones firmadas aunque la asignación mineral siga incompleta: revisar el
estado de cálculo, la química admitida y las advertencias, no solo la suma.

Comparar perfiles exige igualar entradas, unidades, normalización y política de
hierro, y declarar diferencias de apatita y carbonatos. Sustituir el perfil que
generó las variables de un modelo ML requiere reevaluarlo bajo el mismo diseño.
La revisión realizada no atribuye la diferencia de métricas Legacy a un fallo
de GeoNormPy ni demuestra que el cierre mejorado aumente la exactitud ML.
La [metodología y crítica de GeoNormML](https://github.com/jordan-zav/GeoNormML/blob/main/README.es.md#metodología-vigente-y-crítica)
separa los resultados ya comprobados de la validación anidada e independiente
que todavía debe realizarse para futuras selecciones.

## Qué permite hacer

| Función | Alcance |
| --- | --- |
| Cálculo | Asignación secuencial de minerales normativos CIPW |
| Hierro | Entrada como FeOT o como FeO y Fe2O3 separados |
| Diagnóstico | Saturación en sílice, estado de alúmina, balance de masa y errores |
| Ejecución | API Python, lotes con pandas y CLI |
| Reproducción | Configuración YAML, esquema de datos, plantillas y validación |
| Integración | Motor de variables normativas para GeoNormML |

La versión 1.1.0 ofrece extended_cipw_v3, verma2003 y pruseth2009. La política de
hierro se elige por separado. Sus convenciones de apatito, componentes libres y
conjuntos de entrada difieren; los repartos no resueltos se informan explícitamente.
Consulta [perfiles y convenciones](docs/PERFILES_CIPW.md) y [errores](docs/ERRORS.md).

## Instalación

Requiere Python 3.9 o superior. Para instalar la distribución:

~~~powershell
python -m pip install geonormpy
~~~

Desde el código fuente, prepara un entorno Python aislado e instala el proyecto:

~~~powershell
git clone https://github.com/jordan-zav/GeoNormPy.git
cd GeoNormPy
python -m pip install -e .
~~~

## Primer cálculo

~~~python
from geonormpy.norms.cipw import cipw

sample = {
    "SiO2": 72.5, "Al2O3": 13.5, "FeOT": 2.5,
    "MgO": 0.5, "CaO": 1.8, "Na2O": 3.4, "K2O": 4.0,
}
result = cipw(sample)
print(result["minerals_wtpercent"])
print(result["flags"])
~~~

Para trabajar con tablas y configuración:

~~~powershell
geonormpy --help
geonormpy schema
geonormpy make-template
geonormpy make-config
geonormpy validate --input data/test_data.csv
geonormpy run --config config/workflow.yaml
python run_GeoNormPy.py
~~~

El lanzador de ejemplo utiliza data/test_data.csv y escribe data/normative_results.csv.

## Entradas, salidas y control

Las entradas incluyen SiO2, TiO2, Al2O3, Fe2O3, FeO, FeOT, MnO, MgO, CaO, Na2O,
K2O, P2O5 y componentes accesorios. Sample_ID y Notes pueden conservar identificadores.
Utiliza una base consistente de porcentaje en peso y documenta pérdida por
ignición, límites de detección y tratamiento del hierro total.

Conserva tanto los minerales como silica_saturation, alumina_state,
mass_balance_error, interpretive_flag y calc_error. Eliminar filas fallidas sin
guardar sus motivos rompe la trazabilidad. Las hipótesis de especiación del
hierro, alteración y volátiles pueden cambiar el resultado; un balance correcto
no demuestra que el nombre de roca sea correcto.

## Método, desarrollo y cita

- [Descripción completa del método](docs/methods/Algoritmo_GeoNormPy_Completo.md).
- [Auditoría CIPW](docs/methods/Auditoria_CIPW_Sesion_2026-04-10.md).
- [Comparaciones y estabilidad](docs/benchmarks_y_metodos_cipw_20261025.md).
- [Ejecución de benchmarks](benchmarks/README.md).
- [Publicación en PyPI](docs/PUBLISHING.md) y [metadatos de cita](CITATION.cff).

Las pruebas cubren el motor, casos de robustez, CLI y flujos configurados:

~~~powershell
python -m pytest -q
~~~

El código principal está en geonormpy/norms, geonormpy/core, geonormpy/schema.py
y geonormpy/cli.py. Configuraciones, pruebas y documentación se mantienen en
config, tests y docs. Consulta el [README inglés](README.md) para el catálogo
completo de campos minerales y las instrucciones de desarrollo.

## Licencia y contacto

[GNU GPL v3](LICENSE). Jordan Zavaleta — GisGeo Dev.
[Correo](mailto:jordanzav@gisgeo.dev) · [Sitio web](https://gisgeo.dev).
