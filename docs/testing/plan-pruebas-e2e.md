# Plan de pruebas E2E — Proyecto 1

**Sistema:** job-search-agent (bot de Telegram + n8n + profile-api + Postgres + MinIO)
**Autora / ejecución:** Andrea Rivera · **Versión:** 1.0 · **Fecha:** 2026-10-07

## 1. Objetivo
Comprobar, de punta a punta y con el sistema real, que el Proyecto 1 cumple
su definición de terminado (especificación, sección 10.1): una persona se
registra, sube su CV, completa su perfil, recibe vacantes de varias fuentes
sin duplicados, las consulta y gestiona por Telegram, recibe su resumen
diario, y el sistema se recupera de fallos sin duplicar nada.

## 2. Alcance
**Dentro:** los E2E de la especificación (sección 34) que aplican al
Proyecto 1 — *alta y CV*, *vacante duplicada*, *reintento sin duplicado* —
más los 12 puntos de la definición de terminado.

**Fuera (se prueban en proyectos siguientes):** postulación autorizada,
CAPTCHA/MFA, autorización expirada, formulario modificado y
rechazo/entrevista (Proyecto 2); exportación y eliminación de datos del
usuario (Proyecto 3).

## 3. Estrategia: la pirámide de pruebas

| Nivel | Qué prueba | Herramienta | Cantidad | Cómo se corre |
|---|---|---|---|---|
| Unitarias | Funciones puras: lectores de correo, filtros, deduplicación, comandos, puntaje, telemetría, idempotencia | pytest | 136 | `cd services/profile-api && pytest -q` |
| Integración | profile-api + Postgres + MinIO reales, sin Telegram | scripts Python/Bash | 42 + 15 + 8 | `scripts/probar-aislamiento.py`, `probar-idempotencia.py`, `probar-restauracion.sh` |
| E2E | Telegram → n8n → profile-api → Postgres/MinIO → IA → Telegram/correo | manual con el bot real | 30 casos (abajo) | este documento |

Las unitarias y de integración cubren la lógica con muchos datos; los E2E
comprueban que las piezas conectadas funcionan para un usuario real. Por eso
hay muchas pruebas abajo de la pirámide y pocas arriba.

## 4. Entorno y datos
- Instalación local (`bash scripts/start-local.sh`), develop en el commit probado.
- Bot real; usuaria admin (Andrea) y, para casos de otro usuario, una
  invitación a una persona de confianza o un id de prueba 9000001xx/9000002xx
  (los scripts limpian sus datos; regla de BUG-22).
- CV real en PDF y en DOCX (sin escanear) y un PDF escaneado (solo imagen).
- Mailpit en http://localhost:8025 para ver los correos.

## 5. Cómo registrar la ejecución
Para cada caso: **Estado** (✅ pasó · ❌ falló · ⏸ bloqueado · ⬜ pendiente),
**fecha** y **evidencia**: captura o salida guardada en
`docs/testing/evidencias/` con el ID del caso en el nombre
(ej. `E2E-07_cv-docx.png`). Si un caso falla, se registra en
`docs/bitacora-bugs.md` como BUG nuevo y se vuelve a ejecutar tras el arreglo.

**Antecedente** indica dónde ya se había probado esa funcionalidad durante el
desarrollo; este plan la vuelve a ejecutar de forma ordenada y con evidencia.

## 6. Casos de prueba

### A. Registro y acceso
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-01 | Invitación válida | Admin: `/invitar`. Persona nueva: `/start CODIGO` | Bienvenida; queda registrada como usuario activo | DoD 5 usuarios | Multiusuario parte 2 (Carolina, Ludwing) | ⬜ | | |
| E2E-02 | Sin invitación | Persona no registrada escribe `hola` | Mensaje de que necesita invitación; no se registra | DoD 5 usuarios | probar-aislamiento | ⬜ | | |
| E2E-03 | Código ya usado | Otra persona usa el código de E2E-01 | "Código ya usado"; no se registra | DoD 5 usuarios | probar-aislamiento | ⬜ | | |
| E2E-04 | `/start` estando registrada | Admin escribe `/start` | "👋 Ya tienes acceso…" (sin datos raros) | — | BUG-23 | ⬜ | | |

### B. CV y perfil
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-05 | `/subir_cv` | Escribir `/subir_cv` | Instrucciones de cómo enviar el CV | Comandos spec | 2026-10-06 | ⬜ | | |
| E2E-06 | CV en PDF real | Enviar el PDF | Confirma caracteres leídos; perfil creado; preguntas solo de lo que falta; archivo en MinIO | DoD PDF | Reconstrucción 2026-10-07 | ⬜ | | |
| E2E-07 | CV en DOCX real | Enviar el mismo CV en Word | Igual que E2E-06 | DoD DOCX | | ⬜ | | |
| E2E-08 | PDF escaneado | Enviar un PDF que es solo imagen | Aviso de que no se pudo leer; NO crea perfil vacío | — | BUG-24 | ⬜ | | |
| E2E-09 | Reenviar el CV | Enviar el CV otra vez con la entrevista ya respondida | No repite preguntas ya respondidas | DoD perfil versionado | BUG-26 | ⬜ | | |
| E2E-10 | `/completar_perfil` | Con todo respondido | "No tengo preguntas pendientes…" | Comandos spec | BUG-30 | ⬜ | | |
| E2E-11 | `/perfil` y `/corregir` | `/perfil`; luego `/corregir ciudad` y responder | Muestra el perfil; la corrección se guarda y aparece en `/perfil` | DoD inferencia corregible | | ⬜ | | |

### C. Radar: fuentes y duplicados
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-12 | Vacante por correo | Esperar (o reenviar a la etiqueta Radar) una alerta de LinkedIn/Indeed | Aviso por Telegram con la vacante y su link | DoD 3 fuentes | radar-correo | ⬜ | | |
| E2E-13 | Get on Board | Ejecutar `radar-getonbrd` a mano | Las nuevas que coinciden con tus palabras llegan por Telegram | DoD 3 fuentes | 2026-10-03 | ⬜ | | |
| E2E-14 | URL manual | `/vacante <link>` | Vacante guardada con número | DoD 3 fuentes | | ⬜ | | |
| E2E-15 | **Vacante duplicada** entre fuentes | `/vacante` con el link de una vacante que ya llegó por Get on Board o correo | "👌 Esa vacante ya la tenías guardada" (mismo número); no crea otra | E2E spec, DoD dedup | | ⬜ | | |
| E2E-16 | Filtro de palabras | Revisar los avisos del día | Solo títulos con tus palabras clave (sin "nómina", "recepcionista"…) | — | BUG-28, BUG-29 | ⬜ | | |
| E2E-17 | Filtro de ubicación | Revisar avisos | Sin vacantes de otros países (ej. México), aunque sean remotas | — | BUG-18 | ⬜ | | |

### D. Consultas y gestión por Telegram
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-18 | `/nuevas` y `/mejores` | Escribir ambos | Listas con número, puntaje y link | DoD consulta | | ✅ | 2026-10-08 | [nuevas 1](evidencias/E2E-18_nuevas_1.jpg), [nuevas 2](evidencias/E2E-18_nuevas_2.jpg), [mejores 1](evidencias/E2E-18_mejores_1.jpg), [mejores 2](evidencias/E2E-18_mejores_2.jpg) |
| E2E-19 | `/detalle`, `/guardar`, `/descartar` | Con un número de la lista | Detalle completo; guardada aparece en `/guardadas`; descartada sale de `/mejores` y no se puntúa | DoD guardado y descarte | BUG-29 | ✅ | 2026-10-08 | [detalle](evidencias/E2E-19_detalle.jpg), [guardar y guardadas](evidencias/E2E-19_guardar_guardadas.jpg), [descartar y nuevas](evidencias/E2E-19_descartar_nuevas.jpg) |
| E2E-20 | `/buscar` | `/buscar bogota` (sin tilde) | Encuentra "Bogotá"; ordena por puntaje | Comandos spec | 2026-10-06 | ⬜ | | |
| E2E-21 | `/preferencias` | Ver y cambiar las palabras | Responde con las palabras nuevas; los próximos avisos las usan | — | BUG-28 | ⬜ | | |
| E2E-22 | Comando mal escrito / sticker | `/ayudaa` y un sticker | Responde la lista de comandos; nunca se queda callado | — | 2026-10-06 | ⬜ | | |
| E2E-23 | `/pausar` y `/reanudar` | Pausar; esperar el resumen; reanudar | Pausada no recibe avisos ni resumen; al reanudar vuelven | — | multiusuario | ⬜ | | |

### E. Resumen diario
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-24 | Resumen por Telegram y correo | Esperar las 11 am (o `/resumen` + ejecutar el flujo) | Llega por Telegram y aparece en Mailpit | DoD resumen | 2026-10-06 | ⬜ | | |
| E2E-25 | **Resumen sin repetir** | Ejecutar `radar-resumen-diario` a mano después del de las 11 am | No llega un segundo resumen ese día | E2E spec reintento | probar-idempotencia | ⬜ | | |

### F. Fallos y recuperación
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-26 | Groq falla → Gemini | Ver `/telemetria/ia` tras unas horas de radar | Llamadas con proveedor gemini y fallback; puntajes guardados igual | DoD telemetría | 2026-10-06/07 | ⬜ | | |
| E2E-27 | Corte de la IA / de profile-api | Apagar profile-api (`docker compose … stop profile-api`) durante una vuelta del radar; volver a prenderlo | Alerta por Telegram; la vuelta siguiente procesa lo pendiente **sin duplicar** vacantes ni avisos | DoD fallos recuperables | caso real 2026-10-07 9:29 | ⬜ | | |
| E2E-28 | **Reintento sin duplicado** (Telegram reenvía) | `python3 scripts/probar-idempotencia.py` | 15/15 | E2E spec, DoD fallos | 2026-10-06 | ✅ | 2026-10-07 | salida en la sesión de reconstrucción |

### G. Operación
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-29 | Respaldo y restauración | `backup-db.sh` y `probar-restauracion.sh` | 8/8 tablas + MinIO con la misma huella | DoD respaldo | | ✅ | 2026-10-07 | reconstrucción |
| E2E-30 | Reconstrucción desde cero | `docs/runbooks/reconstruccion.md` en carpeta nueva | Bot, CV, IA, MinIO y pruebas OK | DoD reconstrucción | BUG-31 | ✅ | 2026-10-07 | runbook, sección Resultado |

## 7. Trazabilidad con la definición de terminado
| Punto del DoD | Casos |
|---|---|
| Cinco usuarios aislados pueden registrarse | E2E-01..04 + probar-aislamiento (42/42) |
| Se procesa un PDF y un DOCX reales | E2E-06, E2E-07 |
| Toda inferencia puede confirmarse o corregirse | E2E-09, E2E-11 |
| Perfil estructurado y versionado | E2E-06, E2E-09 |
| Tres tipos de fuentes y 100 vacantes de prueba | E2E-12..14 (+ conteo en la base) |
| Deduplicación entre fuentes | E2E-15 |
| Consulta, guardado y descarte por Telegram | E2E-18..20 |
| Resumen por Telegram y correo | E2E-24, E2E-25 |
| Telemetría de IA | E2E-26 |
| Fallos recuperables sin duplicados | E2E-27, E2E-28 |
| Respaldo restaurable de PostgreSQL y MinIO | E2E-29 |
| Reconstrucción desde repositorio y .env.example | E2E-30 |

## 8. Limitaciones conocidas (no son fallas de estos casos)
- **Telemetría:** si Groq y Gemini fallan los dos (ej. corte de red), la
  llamada no queda en `ai_calls`, porque el flujo se corta antes de llegar a
  profile-api. Ese caso se detecta por la alerta de Telegram, no por
  `/telemetria/ia`.
- **Respaldo de IA alto:** el 2026-10-07 Gemini respondió el 30 % de las
  llamadas. Hipótesis: el radar manda 10 vacantes seguidas y supera el límite
  de tokens por minuto del plan gratis de Groq. Si se mantiene, agregar una
  pausa entre vacantes (ver `docs/decisions/001`).
- El sistema depende de que el Mac esté encendido (ver riesgos en la bitácora).

## 9. Observaciones de la ejecución
Hallazgos que no hacen fallar un caso, pero vale la pena registrar (posibles mejoras):

| Caso | Observación | Severidad | Decisión |
|---|---|---|---|
| E2E-18 | `/mejores` muestra sobre todo vacantes de hace 5–6 días; puede que algunas ya estén cerradas. No tiene límite de antigüedad. | Baja (mejora) | Pendiente de decidir |
| E2E-18 | `/nuevas` incluye vacantes poco afines ("Técnico de soporte en sitio", "Analista de producción, calidad e inventarios") porque coinciden con palabras amplias (soporte, calidad, ia). Es lo esperado: el filtro es amplio y el puntaje (15–20 pts) las deja abajo. | Informativa | Sin cambio |
| E2E-19 | En `/detalle 303`, la IA pone "Experiencia en automatización con Python y pytest" como punto a favor, pero en contra dice que la vacante no trae requisitos. El punto a favor sale del perfil, no de la vacante, así que puede dar una confianza que no está sustentada. | Baja (mejora) | Pendiente de decidir: ajustar el prompt para que los puntos a favor solo citen lo que dice la vacante |

## 10. Siguiente nivel (opcional): mutation testing
Romper el código a propósito para comprobar que las pruebas lo detectan
(ej. quitar la deduplicación, invertir el filtro de ubicación, saltar la
idempotencia). Si al "mutar" el código ninguna prueba falla, esa prueba no
está protegiendo nada. Herramienta posible: `mutmut` sobre profile-api.
