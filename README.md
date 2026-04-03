# GeoNormPy

GeoNormPy es un motor de calculo en Python para estimar mineralogia normativa CIPW a partir de datos geoquimicos de roca total. El proyecto esta orientado a flujos de trabajo de petrologia ignea y a procesamiento reproducible de datos geoquimicos.

## Caracteristicas

- Calculo CIPW secuencial con enfoque numericamente robusto.
- Manejo de hierro a partir de `FeOT` o especiacion explicita `FeO`/`Fe2O3`.
- Diagnosticos de saturacion de silice y estado de alumina.
- Procesamiento individual y por lotes con `pandas`.
- Suite de pruebas automatizadas con `pytest`.

## Instalacion

```bash
git clone https://github.com/jordan-zav/GeoNormPy.git
cd GeoNormPy
pip install -e .
```

## Uso rapido

```python
from geonormpy.norms.cipw import cipw

muestra = {
    "SiO2": 72.5,
    "Al2O3": 13.5,
    "FeOT": 2.5,
    "MgO": 0.5,
    "CaO": 1.8,
    "Na2O": 3.4,
    "K2O": 4.0,
}

resultado = cipw(muestra)
print(resultado["minerals_wtpercent"])
print(resultado["flags"])
```

## Procesamiento por lotes

```bash
python run_GeoNormPy.py
```

El script lee `data/test_data.csv` y genera `data/normative_results.csv`.

## Desarrollo

```bash
pytest -q
```

## Contexto academico

Este software fue desarrollado por Jordan Angel Luciano Zavaleta Reyes en el contexto de investigación aplicada a petrología ígnea y geoquímica computacional.

## Como citar

Si utilizas GeoNormPy en una tesis, articulo o informe tecnico, consulta el archivo `CITATION.cff`.

## Licencia

Este proyecto se distribuye bajo la licencia MIT.
