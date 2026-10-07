# ADR 003 · Sin embeddings en el Proyecto 1

**Fecha:** 2026-10-03 · **Estado:** aceptada, revisar con más volumen · **Decidió:** Andrea

## Contexto
La especificación propone controlar el costo en tres pasos: filtros
determinísticos → **embeddings** (parecido entre perfil y vacante) →
evaluación generativa solo de las mejores (secciones 8 y 11).

## Decisión
No usar embeddings en el Proyecto 1. El embudo queda en dos pasos:
1. **Filtros determinísticos** en profile-api (con tests): palabras clave
   del usuario en el título (`/preferencias`), ubicación, idioma, nivel,
   antigüedad y deduplicación.
2. **Puntaje con IA** (`radar-puntaje`, 10 vacantes por hora), con reglas
   fijas después (topes por inglés, nivel senior y señales de alerta).

## Por qué
- **El volumen no lo pide:** llegan decenas de vacantes al día por usuario,
  no miles. Después del filtro de palabras (BUG-28/29) la IA solo puntúa
  las que tienen que ver con la búsqueda.
- **Menos piezas:** embeddings exigen un modelo más (local o servicio),
  guardar vectores (pgvector) y recalcularlos cuando cambia el perfil. Es
  infraestructura y memoria extra en un Mac que ya corre todo en Docker.
- **Explicable:** un filtro por palabras se entiende y se prueba con tests;
  el usuario lo ajusta con `/preferencias`. Un umbral de similitud es más
  difícil de explicar y de depurar.
- **Costo:** el puntaje ya cuesta USD 0 con el plan gratis (ADR 001).

## Consecuencias
- El filtro por palabras puede dar **falsos negativos** (ej. "tester" no
  atrapaba "Test Analyst", BUG-29). Se mitiga con raíces cortas ("test",
  "automatiza") y la vista previa de `app.limpiar_pendientes`.
- La IA no ve vacantes descartadas por el filtro; si el usuario cambia de
  búsqueda, las viejas no se re-evalúan.

## Cuándo revisarla
- Si llegan cientos de vacantes por usuario al día y la cuota de IA no
  alcanza (la telemetría lo muestra).
- Si los falsos negativos del filtro por palabras se vuelven frecuentes.
- En el Proyecto 2, si se necesita comparar el CV con la descripción
  completa de la vacante para adaptar postulaciones.
