# test_i18n.py

## Parsea campos con etiquetas en ingles
**Qué prueba:** Que el parser acepta etiquetas en ingles y extrae correctamente titulo, descripcion y pasos.
**Pasos:**
1. Crea un archivo `.spec.md` temporal con etiquetas `What it tests` y `Steps`
2. Ejecuta `parse_spec_file` con idioma ingles
3. Verifica que titulo, campo `what` y lista de pasos coinciden con el contenido esperado

## Parsea campos con etiquetas en espanol
**Qué prueba:** Que el parser acepta etiquetas en espanol y conserva correctamente los datos del test.
**Pasos:**
1. Crea un archivo `.spec.md` temporal con etiquetas `Qué prueba` y `Pasos`
2. Ejecuta `parse_spec_file` con idioma espanol
3. Verifica que titulo, descripcion y pasos se hayan parseado correctamente

## Exporta markdown con etiquetas localizadas
**Qué prueba:** Que la exportacion markdown usa encabezados y labels traducidos al idioma seleccionado.
**Pasos:**
1. Construye una estructura de spec en memoria con un test documentado
2. Ejecuta `export_markdown` con idioma espanol
3. Verifica presencia de titulo, marca de fecha y labels traducidos

## Exporta csv con encabezados localizados
**Qué prueba:** Que la exportacion csv genera encabezados traducidos al idioma seleccionado.
**Pasos:**
1. Construye una estructura de spec en memoria
2. Ejecuta `export_csv` con idioma espanol
3. Verifica que el encabezado inicia con columnas esperadas en espanol

## Prioriza idioma explicito sobre entorno
**Qué prueba:** Que la resolucion de idioma usa el argumento explicito por encima de variables de entorno.
**Pasos:**
1. Define `SPECVIEW_LANG` con valor espanol
2. Llama `resolve_language` con argumento `en`
3. Verifica que el resultado final sea ingles

## Prioriza idioma detectado en specs sobre entorno
**Qué prueba:** Que al usar modo auto se privilegia el idioma detectado en archivos spec sobre `LANG` del entorno.
**Pasos:**
1. Crea un spec temporal en espanol
2. Define `LANG` en ingles
3. Llama `resolve_language` con `auto` y el archivo temporal
4. Verifica que el idioma resuelto sea espanol

## Usa variables de entorno cuando auto no tiene specs
**Qué prueba:** Que en modo auto se usa el idioma del entorno cuando no hay contenido para detectar.
**Pasos:**
1. Define `LANG` con una localidad en espanol
2. Llama `resolve_language` sin archivos spec
3. Verifica que el idioma resultante sea espanol

## Usa ingles por defecto sin configuracion
**Qué prueba:** Que la resolucion de idioma vuelve a ingles cuando no hay argumento ni variables de entorno.
**Pasos:**
1. Limpia `SPECVIEW_LANG`, `LC_ALL` y `LANG`
2. Llama `resolve_language` sin argumentos
3. Verifica que el resultado sea `en`

## Retorna nulo para deteccion ambigua
**Qué prueba:** Que la deteccion de idioma retorna `None` cuando el texto contiene etiquetas mezcladas en ambos idiomas.
**Pasos:**
1. Prepara texto con etiquetas inglesas y espanolas en el mismo contenido
2. Ejecuta `detect_language_from_text`
3. Verifica que el resultado sea `None`

## Carga traducciones gettext desde catalogos
**Qué prueba:** Que `get_i18n` obtiene traducciones reales desde los catalogos compilados.
**Pasos:**
1. Solicita instancia i18n en espanol
2. Consulta una clave traducible conocida
3. Verifica que el texto retornado sea la traduccion esperada

## Compila po a mo y permite lectura con gettext
**Qué prueba:** Que la compilacion de archivos `.po` genera un `.mo` valido y legible.
**Pasos:**
1. Crea un `.po` temporal con una traduccion simple
2. Ejecuta `compile_po_file`
3. Abre el `.mo` resultante con `GNUTranslations`
4. Verifica que la clave traducida se resuelve al valor esperado
