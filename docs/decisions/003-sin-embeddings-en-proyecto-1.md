# ADR 003. Sin embeddings en el Proyecto 1

Fecha: 2026-10-03. Estado: aceptada, revisar si crece el volumen. Decidió: Andrea.

## Contexto

La especificación propone controlar el costo de la IA en tres pasos: primero filtros fijos, después embeddings para medir qué tan parecidos son el perfil y la vacante, y al final una evaluación con IA generativa solo para las mejores (secciones 8 y 11).

## Decisión

En el Proyecto 1 no uso embeddings. El filtro queda en dos pasos:

1. Filtros fijos en profile-api, con sus tests: palabras clave del usuario en el título (las de `/preferencias`), ubicación, idioma, nivel, antigüedad y eliminación de duplicados.
2. Puntaje con IA en `radar-puntaje`, 10 vacantes por hora, y después unas reglas fijas que ponen topes cuando piden inglés, nivel senior o hay señales de alerta.

## Por qué

El volumen no lo necesita. Llegan decenas de vacantes al día por usuario, no miles, y desde que agregué el filtro de palabras (BUG-28 y BUG-29) la IA solo puntúa las que tienen que ver con la búsqueda.

Los embeddings agregan piezas: otro modelo (local o como servicio), guardar los vectores en pgvector y recalcularlos cada vez que cambia el perfil. Es más infraestructura y más memoria en un Mac que ya corre todo en Docker.

Un filtro por palabras se entiende fácil, se prueba con tests y el usuario lo ajusta con `/preferencias`. Un umbral de similitud es más difícil de explicar y de depurar.

Y el puntaje ya cuesta cero con el plan gratis (ADR 001).

## Consecuencias

El filtro por palabras puede dejar por fuera vacantes que sí servían. Me pasó con "tester", que no atrapaba "Test Analyst" (BUG-29). Lo manejo usando raíces cortas como "test" o "automatiza", y revisando con la vista previa de `app.limpiar_pendientes`.

La IA nunca ve las vacantes que el filtro descartó, así que si el usuario cambia su búsqueda, las vacantes viejas no se vuelven a evaluar.

## Cuándo revisarla

- Si llegan cientos de vacantes por usuario al día y no alcanza la cuota de la IA (se ve en la telemetría).
- Si las vacantes que el filtro deja por fuera sin razón se vuelven frecuentes.
- En el Proyecto 2, si hace falta comparar el CV con la descripción completa de la vacante para adaptar la postulación.
