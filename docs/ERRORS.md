# Errores y salida JSON

GeoNormPy 0.1.2 ofrece dos formas de integrar el cálculo. La función cipw devuelve la norma o lanza GeoNormPyError, compatible con ValueError. La excepción incluye code, field, details y el método to_dict. La función cipw_safe devuelve siempre un diccionario con ok, result y error.

    import json
    from geonormpy import cipw_safe

    response = cipw_safe({"SiO2": -1})
    print(json.dumps(response, allow_nan=False))

La respuesta contiene ok igual a false, result igual a null y este error:

    {"code": "invalid_measurement", "message": "Invalid numeric measurement for SiO2: enter a finite, nonnegative number.", "field": "SiO2", "details": {}}

Los códigos principales son invalid_analysis, invalid_measurement, unsupported_oxide, empty_analysis, invalid_option, inconsistent_iron y allocation_incomplete. Una norma que conserva déficit de sílice u óxidos sin asignar no se presenta como un cálculo completo en cipw_safe. La función cipw permite inspeccionarla con sus flags y residuos; strict=True la rechaza.

## Consola

    geonormpy run --config config/workflow.yaml
    geonormpy run --config config/workflow.yaml --json
    geonormpy --json schema

Sin la opción JSON, los errores de ejecución se escriben en stderr con su código y motivo, sin traceback. Con la opción JSON, stdout contiene una única respuesta JSON; los mensajes de progreso quedan fuera de esa respuesta. Los fallos de configuración, archivos y argumentos también se comunican en ese formato.

El código de salida es cero cuando la operación termina sin errores. Es uno si la ejecución falla, la validación falla o alguna muestra del lote falla. En este último caso, las muestras válidas siguen disponibles en el CSV y el JSON de consola incluye las filas con error. Los índices row son de base cero, sin contar el encabezado.

## Lotes

El CSV incorpora calc_error, error_code y error_json. En una muestra fallida, las abundancias minerales quedan desconocidas, no rellenadas con ceros. Las columnas de identificación y otras variables numéricas ajenas a los óxidos no entran en la normalización. Los textos numéricos sí se convierten; un texto inválido en un óxido provoca un error de esa muestra.

El guardado es atómico: un fallo al escribir conserva el archivo de salida anterior.

## Límites del modelo

Los datos se introducen con los nombres canónicos de los óxidos admitidos. La función individual rechaza metadatos, elementos traza en ppm, LOI y agua; el lote selecciona las columnas de óxidos. Los componentes no suministrados no se convierten en mediciones verificadas: la norma queda condicionada a la composición proporcionada. Para FeOT se utiliza una fracción férrica fija configurable, que es una suposición de cálculo.

Esta versión corrige la secuencia de desaturación y agrega transformaciones de titanita, wollastonita y piroxenos. El modelo conserva limitaciones para composiciones extremas. En análisis con F, Cl o S, el balance gravimétrico debe interpretarse con la base de oxígeno de esos componentes; las advertencias de masa permanecen visibles. La conservación de inventarios sintéticos no equivale a una validación completa contra muestras de referencia independientes.
