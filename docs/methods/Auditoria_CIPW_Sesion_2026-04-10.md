# Auditoría CIPW - Sesión 2026-04-10

## Estado general

Se revisó la coherencia entre la implementación de GeoNormPy, la documentación metodológica y varias objeciones estequiométricas y normativas surgidas durante la auditoría. El resultado es que el motor quedó más explícito en sus convenciones internas y más cercano al orden clásico de la rama subsaturada del CIPW.

## Puntos cerrados

- La especiación del hierro basada en `FeOT` ahora deja explícito en las advertencias el valor de `fe3_fraction` usado.
- `MnO` sigue convirtiéndose a equivalente de `FeO` sobre base molar, y ahora genera advertencia adicional cuando `MnO > 0.5 wt%`.
- El diagnóstico `A/CNK` y la bandera `alumina_state` se calculan después de retirar volátiles y accesorios, es decir, sobre el `CaO` realmente disponible para silicatos.
- La documentación metodológica ya refleja ese orden correctamente.
- La convención de apatita normativa fue aclarada como convención CIPW clásica: `Ca(10/3)(PO4)2`, equivalente a `3.33CaO·P2O5`.
- Esa convención quedó documentada tanto en la lógica de consumo como en la definición mineral y en el documento metodológico.
- Se aclaró en código y documentación que los inventarios de minerales como `Or`, `Ab`, `Le`, `Ne` y `Hl` se almacenan como moles de fórmula mineral.
- Se confirmó que los factores de recuperación de sílice en `Or -> Le`, `Le -> Kp` y `Ab -> Ne` son correctos bajo esa convención de unidades.
- La rama subsaturada se reordenó a `Hy -> Ol`, luego `Or -> Le`, después `Le -> Kp` y finalmente `Ab -> Ne`.
- Se añadieron pruebas para fijar la prioridad potásica y el comportamiento en composiciones fuertemente potásicas y subsaturadas.

## Decisiones metodológicas que se mantienen

- La apatita no sigue la fórmula mineralógica completa de apatita natural; sigue la convención normativa CIPW histórica.
- `MnO -> FeO` se mantiene como convención normativa estándar.
- La halita se contabiliza como moles de fórmula de `NaCl`, numéricamente equivalentes a los moles de `Cl` consumidos.
- El algoritmo sigue siendo una norma química, no una reconstrucción modal ni textural de la roca real.

## Puntos que no se consideraron bugs

- La razón `10/3` en apatita no es un error aritmético dentro de este repositorio; es una convención normativa explícita y ahora está documentada.
- Los factores de recuperación de sílice de `Or` y `Ab` no estaban duplicados; la confusión provenía de interpretar `Or` y `Ab` como moles del óxido alcalino en vez de moles de fórmula mineral.
- El consumo de `FeO` por pirita antes de cromita e ilmenita sí ocurre de forma secuencial sobre el mismo estado químico; no hay doble conteo.

## Resultado práctico

Al cierre de esta sesión, el repositorio queda internamente consistente en los puntos auditados y con trazabilidad mucho más clara para una revisión petroquímica externa.

## Verificación

La validación local ejecutada sobre la suite relevante fue:

`pytest -q tests\test_cipw.py tests\test_cipw_robustness.py`

Resultado al cierre de la sesión:

`12 passed`
