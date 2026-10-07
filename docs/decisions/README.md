# Decisiones de diseño (ADR)

Cada archivo explica una decisión en la que el Proyecto 1 se aparta de la
especificación técnica (`docs/architecture/especificacion-tecnica.md`) o
deja algo para después: qué decía la especificación, qué se hizo, por qué y
cuándo conviene revisarlo.

Formato: contexto → decisión → por qué → consecuencias → cuándo revisarla.

| # | Decisión | Estado |
|---|---|---|
| [001](001-ia-groq-gemini-en-vez-de-nim.md) | IA: Groq + respaldo Gemini en vez de NVIDIA NIM | Aceptada |
| [002](002-get-on-board-en-vez-de-greenhouse-lever.md) | Fuente por API: Get on Board en vez de Greenhouse/Lever | Aceptada |
| [003](003-sin-embeddings-en-proyecto-1.md) | Sin embeddings en el Proyecto 1 | Aceptada (revisar con más volumen) |
| [004](004-nombres-y-cantidad-de-workflows.md) | 8 workflows con nombres propios en vez de los ~30 de la especificación | Aceptada |
| [005](005-correo-de-alertas-solo-admin.md) | El radar por correo lee solo el buzón de la admin | Aceptada (Proyecto 1) |
| [006](006-mailpit-en-local-smtp-real-en-produccion.md) | Resumen por correo: Mailpit en local, SMTP real en producción | Aceptada |
