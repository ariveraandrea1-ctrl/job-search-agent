# ADR 004. 8 flujos con nombres propios en vez de los ~30 de la especificación

Fecha: 2026-10-03. Estado: aceptada. Decidió: Andrea.

## Contexto

En la sección 9, la especificación lista unos 30 flujos en cuatro familias (`sys-*`, `profile-*`, `search-*`/`connector-*`/`job-*` y `telegram-*`/`summary-*`), cada uno con una sola tarea.

## Decisión

Me quedo con los 8 flujos que tengo, con sus nombres en español, y la lógica de negocio va en profile-api (Python, con tests) y no en n8n. No los voy a renombrar.

## Equivalencias con la especificación

| Flujo actual | Lo que cubre de la especificación |
|---|---|
| `telegram-invitacion` | telegram-command-router, profile-onboarding, profile-cv-upload, profile-cv-extraction, profile-analysis, profile-interview-next-question, profile-answer-processing, profile-confirmation (`/corregir`), connector-manual-url (`/vacante`) |
| `verificar-acceso` | autorización de cada mensaje (registro por invitación e idempotencia) |
| `ai-model-router` | alias de IA (ADR 001) |
| `radar-correo` | connector-email-alerts |
| `radar-getonbrd` | conector por API (ADR 002, en lugar de connector-greenhouse y connector-lever) |
| `radar-puntaje` | job-ai-scoring |
| `radar-resumen-diario` | summary-daily-telegram, summary-daily-email |
| `alertas-errores` | sys-global-error-handler |
| profile-api (no es un flujo) | job-normalizer, job-deduplicator, job-hard-filters, profile-versioning, telegram-notification (los textos) |
| scripts (`scripts/`) | sys-daily-maintenance (respaldo y prueba de restauración) |

Algunos no los hice como flujo propio. `search-orchestrator` no hace falta porque cada radar tiene su propio reloj. `connector-company-page` sería scraping. Para `sys-audit-execution` uso el historial de ejecuciones de n8n y la telemetría. Y `sys-retry-failed` no hace falta porque los radares no duplican: si una vuelta falla, la siguiente vuelve a intentar.

## Por qué

Los nodos los construyo yo a mano mientras aprendo n8n. Ocho flujos que se pueden leer son más fáciles de entender, probar y explicar en una entrevista que 30 flujos pequeños conectados entre sí.

Normalizar, quitar duplicados y filtrar en Python me permite tener unos 140 tests automáticos. En nodos de n8n no tendría pruebas unitarias.

Renombrar cuesta y aporta poco. Las referencias entre flujos usan ids, pero la documentación, la bitácora y los commits usan los nombres actuales.

## Consecuencias

`telegram-invitacion` es grande, con unos 50 nodos. Lo mantengo ordenado con notas en cada nodo y un Switch con las salidas nombradas.

Si el proyecto crece, lo primero que separaría es la entrevista del CV en su propio subflujo.

## Cuándo revisarla

Si `telegram-invitacion` se vuelve difícil de mantener, o si más de una persona empieza a trabajar en n8n al mismo tiempo.
