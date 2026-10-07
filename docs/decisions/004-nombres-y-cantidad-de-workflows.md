# ADR 004 · 8 workflows con nombres propios en vez de los ~30 de la especificación

**Fecha:** 2026-10-03 · **Estado:** aceptada · **Decidió:** Andrea

## Contexto
La especificación (sección 9) lista unos 30 workflows en cuatro familias
(`sys-*`, `profile-*`, `search-*`/`connector-*`/`job-*`, `telegram-*`/
`summary-*`), cada uno con una sola tarea.

## Decisión
Mantener los **8 workflows actuales** con sus nombres en español y poner la
lógica de negocio en **profile-api** (Python, con tests), no en n8n. No
renombrarlos.

## Equivalencias con la especificación

| Workflow actual | Cubre de la especificación |
|---|---|
| `telegram-invitacion` | telegram-command-router, profile-onboarding, profile-cv-upload, profile-cv-extraction, profile-analysis, profile-interview-next-question, profile-answer-processing, profile-confirmation (`/corregir`), connector-manual-url (`/vacante`) |
| `verificar-acceso` | autorización de cada mensaje (registro por invitación, idempotencia) |
| `ai-model-router` | alias de IA (ADR 001) |
| `radar-correo` | connector-email-alerts |
| `radar-getonbrd` | conector por API (ADR 002, en vez de connector-greenhouse/lever) |
| `radar-puntaje` | job-ai-scoring |
| `radar-resumen-diario` | summary-daily-telegram, summary-daily-email |
| `alertas-errores` | sys-global-error-handler |
| **profile-api** (no es workflow) | job-normalizer, job-deduplicator, job-hard-filters, profile-versioning, telegram-notification (textos) |
| scripts (`scripts/`) | sys-daily-maintenance (respaldo y prueba de restauración) |

No implementados como workflow propio: `search-orchestrator` (cada radar
tiene su reloj), `connector-company-page` (sería scraping), `sys-audit-
execution` (se usa el historial de ejecuciones de n8n + telemetría) y
`sys-retry-failed` (los radares son idempotentes: la siguiente vuelta
reintenta sin duplicar).

## Por qué
- **Aprendizaje:** Andrea construye los nodos a mano; 8 flujos legibles son
  más fáciles de entender, probar y explicar en una entrevista que 30
  flujos pequeños conectados entre sí.
- **Lógica probada en código:** normalizar, deduplicar y filtrar en Python
  tiene ~140 tests automáticos; en nodos de n8n no habría pruebas unitarias.
- **Renombrar tiene costo y poco valor:** las referencias entre flujos
  (Execute Workflow, Error workflow) usan ids, pero la documentación, la
  bitácora y los commits usan los nombres actuales.

## Consecuencias
- `telegram-invitacion` es grande (≈50 nodos). Se ordena con notas en cada
  nodo y un Switch con salidas nombradas.
- Si el proyecto crece, lo primero a separar sería la entrevista del CV en
  su propio subworkflow.

## Cuándo revisarla
- Si `telegram-invitacion` se vuelve difícil de mantener o más de una
  persona trabaja en n8n a la vez.
