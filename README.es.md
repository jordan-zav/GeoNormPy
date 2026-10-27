<p align="center"><a href="README.md">English</a> · <strong>Español</strong></p>

# GeoNormPy

**Mineralogía normativa CIPW reproducible a partir de química de roca total.**

Convierte análisis de óxidos mayores en asociaciones minerales normativas,
diagnósticos y tablas auditables mediante Python o la línea de comandos.

> Una norma CIPW es un cálculo idealizado, no mineralogía modal medida. No
> sustituye la petrografía, las relaciones de campo ni un diagrama QAPF apropiado.

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
