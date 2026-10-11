# ADR 002. Fuente por API: Get on Board en vez de Greenhouse y Lever

Fecha: 2026-10-01. Estado: aceptada. Decidió: Andrea.

## Contexto

La especificación pide tres tipos de fuente: alertas por correo, las APIs públicas de Greenhouse y Lever (empresa por empresa) y vacantes que el usuario manda con un link.

## Decisión

Cambié Greenhouse y Lever por la API pública de Get on Board (`https://www.getonbrd.com/api/v0/categories/{categoria}/jobs`), que no pide clave ni requiere scraping. El flujo `radar-getonbrd` consulta cada hora las categorías de los usuarios activos, y profile-api filtra los resultados por las palabras clave de cada usuario, el idioma (que no pidan inglés), la ubicación (remota o en Colombia) y el nivel (hasta Semi Senior).

## Por qué

Antes de decidir investigué qué empresas con vacantes de QA en Colombia publican en Greenhouse y Lever. Casi todas son internacionales, piden nivel senior y hacen las entrevistas en inglés; algunas, como CI&T, Monks o Capco, ni siquiera tenían vacantes en Colombia. No encajaban con lo que busco, que es QA junior y en español.

Además, con Greenhouse y Lever habría que mantener una lista de empresas una por una. Get on Board es un portal de tecnología de Latinoamérica, en español, organizado por categorías (por ejemplo `sysadmin-devops-qa`) y con el nivel de experiencia dentro de los datos.

Con este cambio se sigue cumpliendo lo importante del requisito: tener una fuente por API oficial, sin scraping y respetando los términos de uso.

## Consecuencias

Las tres fuentes quedan así: correo (LinkedIn, Indeed y Workana), API (Get on Board) y link manual con `/vacante`.

Las categorías de Get on Board se sacan de las palabras clave de cada usuario, las que se ven y se cambian con `/preferencias`.

El lector de links reconoce los de Get on Board y usa el mismo id que la API, así que una vacante no se duplica si llega por las dos vías.

## Cuándo revisarla

Si cambia el tipo de cargo que busco hacia roles donde Greenhouse o Lever sí tengan vacantes que sirvan, por ejemplo con inglés avanzado en empresas internacionales. Agregar un conector por empresa es compatible con el diseño actual (`_guardar_lote` en profile-api).
