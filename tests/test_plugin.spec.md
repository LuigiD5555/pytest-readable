# test_plugin.py

## Expone opciones readable en ayuda de pytest
**Qué prueba:** Que el plugin registra sus flags y aparecen en `pytest --help`.
**Pasos:**
1. Ejecuta pytest con `-p pytest_readable.plugin --help`
2. Busca flags `--readable*` en la salida
3. Verifica que todas las opciones esperadas estén presentes

## Imprime resumen legible al ejecutar pytest
**Qué prueba:** Que `--readable` muestra un resumen integrado en el flujo de pytest.
**Pasos:**
1. Crea un test simple en un proyecto temporal
2. Ejecuta pytest con `--readable`
3. Verifica presencia del encabezado y total de pruebas en la salida

## Muestra arbol en collect-only
**Qué prueba:** Que `--collect-only --readable-tree` imprime jerarquía por módulo y clase.
**Pasos:**
1. Crea un test dentro de una clase
2. Ejecuta pytest en modo collect-only con árbol readable
3. Verifica módulo, clase y nombre legible del test

## Exporta markdown desde flags de pytest
**Qué prueba:** Que el plugin puede exportar documentación markdown con `--readable-docs`.
**Pasos:**
1. Crea un test temporal
2. Ejecuta pytest con formato markdown y ruta de salida
3. Verifica que el archivo se genere con encabezado de documentación

## Exporta csv desde flags de pytest
**Qué prueba:** Que el plugin puede exportar CSV con encabezados esperados.
**Pasos:**
1. Crea un test temporal
2. Ejecuta pytest con formato csv y ruta de salida
3. Verifica que el archivo exista y tenga encabezado correcto

## Respeta idioma es para salida readable
**Qué prueba:** Que `--readable-lang=es` cambia el encabezado del resumen al español.
**Pasos:**
1. Crea un test temporal
2. Ejecuta pytest collect-only con `--readable` y lenguaje español
3. Verifica que aparezca `Resumen legible`

## Respeta idioma en para salida readable
**Qué prueba:** Que `--readable-lang=en` mantiene el encabezado en inglés.
**Pasos:**
1. Crea un test temporal
2. Ejecuta pytest collect-only con `--readable` y lenguaje inglés
3. Verifica que aparezca `Readable summary`

## Usa fallback a spec markdown para nombre de arbol
**Qué prueba:** Que sin decorator el plugin toma nombre legible desde `.spec.md`.
**Pasos:**
1. Crea un test sin metadata decorada
2. Agrega archivo `.spec.md` con nombre de caso narrativo
3. Ejecuta collect-only con árbol en español
4. Verifica que el árbol imprima el nombre del spec markdown
