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
| E2E-01 | Invitación válida | Admin: `/invitar`. Persona nueva: `/start CODIGO` | Bienvenida; queda registrada como usuario activo | DoD 5 usuarios | Multiusuario parte 2 (Carolina, Ludwing) | ✅ | 2026-10-08 | [bienvenida](evidencias/E2E-01_bienvenida.jpg) (recortada: el resto muestra datos personales del ayudante) · aislamiento: [`/nuevas` vacío y `/preferencias` propias](evidencias/E2E-01_aislamiento_nuevas_preferencias.jpg), [cambia sus palabras sin tocar las de la admin](evidencias/E2E-01_aislamiento_preferencias_propias.jpg); `/perfil` muestra solo su CV (captura no publicada) · exploratoria: [código inexistente](evidencias/E2E-01_ayudante_codigo_inexistente.jpg) |
| E2E-02 | Sin invitación | Persona no registrada escribe `hola` | Mensaje de que necesita invitación; no se registra | DoD 5 usuarios | probar-aislamiento | ✅ | 2026-10-08 | [ayudante](evidencias/E2E-02_ayudante_hola.jpg), [tercera persona](evidencias/E2E-03_tercero.jpg) · las dos reciben "solo por invitación" |
| E2E-03 | Código ya usado | Otra persona usa el código de E2E-01 | "Código ya usado"; no se registra | DoD 5 usuarios | probar-aislamiento | ✅ | 2026-10-08 | [tercera persona](evidencias/E2E-03_tercero.jpg) · el código A3JFN2BN, ya usado por el ayudante, responde "Ese código ya fue usado"; tampoco entra con `zzz9999` |
| E2E-04 | `/start` estando registrada | Admin escribe `/start` | "👋 Ya tienes acceso…" (sin datos raros) | — | BUG-23 | ✅ | 2026-10-08 | [/start](evidencias/E2E-04_start.jpg) |

### B. CV y perfil
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-05 | `/subir_cv` | Escribir `/subir_cv` | Instrucciones de cómo enviar el CV | Comandos spec | 2026-10-06 | ✅ | 2026-10-08 | [/subir_cv](evidencias/E2E-05_subir_cv.jpg) |
| E2E-06 | CV en PDF real | Enviar el PDF | Confirma caracteres leídos; perfil creado; preguntas solo de lo que falta; archivo en MinIO | DoD PDF | Reconstrucción 2026-10-07 | ✅ | 2026-10-08 | [PDF y pregunta](evidencias/E2E-06_pdf_pregunta.jpg), [perfil 1](evidencias/E2E-06_perfil_1.jpg), [perfil 2](evidencias/E2E-06_perfil_2.jpg) · MinIO no revisado en esta ejecución (verificado en la reconstrucción 2026-10-07) |
| E2E-07 | CV en DOCX real | Enviar el mismo CV en Word | Igual que E2E-06 | DoD DOCX | | ✅ | 2026-10-08 | [docx](evidencias/E2E-07_docx.jpg) |
| E2E-08 | PDF escaneado | Enviar un PDF que es solo imagen | Aviso de que no se pudo leer; NO crea perfil vacío | — | BUG-24 | ✅ | 2026-10-08 | [aviso y perfil](evidencias/E2E-08_escaneado_perfil_1.jpg), [perfil intacto](evidencias/E2E-08_perfil_2.jpg) |
| E2E-09 | Reenviar el CV | Enviar el CV otra vez con la entrevista ya respondida | No repite preguntas ya respondidas | DoD perfil versionado | BUG-26 | ✅ | 2026-10-08 | [solo pregunta inglés](evidencias/E2E-06_pdf_pregunta.jpg), [perfil: falta solo inglés](evidencias/E2E-06_perfil_2.jpg) · ejecutado junto con E2E-06 |
| E2E-10 | `/completar_perfil` | Con todo respondido | "No tengo preguntas pendientes…" | Comandos spec | BUG-30 | ✅ | 2026-10-08 | [/completar_perfil](evidencias/E2E-10_completar_perfil.jpg) |
| E2E-11 | `/perfil` y `/corregir` | `/perfil`; luego `/corregir ciudad` y responder | Muestra el perfil; la corrección se guarda y aparece en `/perfil` | DoD inferencia corregible | | ✅ | 2026-10-08 | [/corregir salario](evidencias/E2E-11_corregir_salario.jpg), [perfil corregido](evidencias/E2E-11_perfil_corregido.jpg) |

### C. Radar: fuentes y duplicados
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-12 | Vacante por correo | Esperar una alerta real de LinkedIn/Indeed en la etiqueta Radar (NO reenviarla: el lector se elige por el remitente) y revisar Ejecuciones de `radar-correo` en n8n | Aviso por Telegram con la vacante y su link | DoD 3 fuentes | radar-correo | ✅ | 2026-10-08 | [aviso 1:24 pm](evidencias/E2E-12_aviso_telegram.jpg), [ejecuciones n8n](evidencias/E2E-12_n8n_ejecuciones.png) · la ejecución de 13:24 envió el aviso; la de 14:36 paró en "¿Hay vacantes nuevas?" = falso (correo sin vacantes nuevas, no avisa de nuevo) |
| E2E-13 | Get on Board | Ejecutar `radar-getonbrd` a mano | Las nuevas que coinciden con tus palabras llegan por Telegram | DoD 3 fuentes | 2026-10-03 | ✅ | 2026-10-08 | [ejecución manual](evidencias/E2E-13_getonbrd_flujo.png): 156 vacantes revisadas en 4 categorías, 0 nuevas para el usuario; [aviso enviado el 6 oct](evidencias/E2E-13_getonbrd_aviso_6oct.png) (Telegram en verde); [ejecuciones cada hora el 8 oct](evidencias/E2E-13_getonbrd_ejecuciones_8oct.png) |
| E2E-14 | URL manual | `/vacante <link>` | Vacante guardada con número | DoD 3 fuentes | | ❌ ([BUG-33](../bitacora-bugs.md)) | 2026-10-08 | [vacante nueva](evidencias/E2E-14_vacante_nueva.jpg) · la guarda (quedó como #367, verificado en [/nuevas](evidencias/E2E-16_nuevas_1.jpg)) y limpia el link, pero no muestra el número |
| E2E-15 | **Vacante duplicada** entre fuentes | `/vacante` con el link de una vacante que ya llegó por Get on Board o correo | "👌 Esa vacante ya la tenías guardada" (mismo número); no crea otra | E2E spec, DoD dedup | | ✅ | 2026-10-08 | [duplicado y link con parámetros](evidencias/E2E-15_duplicado.jpg) · no duplica, ni con `?refId=…&trackingId=…` (prueba exploratoria). El número no se muestra (BUG-33); verificado en `/nuevas` que no apareció otra BairesDev |
| E2E-16 | Filtro de palabras | Revisar los avisos del día | Solo títulos con tus palabras clave (sin "nómina", "recepcionista"…) | — | BUG-28, BUG-29 | ✅ | 2026-10-08 | [nuevas 1](evidencias/E2E-16_nuevas_1.jpg), [nuevas 2](evidencias/E2E-16_nuevas_2.jpg), [nuevas 3](evidencias/E2E-16_nuevas_3.jpg) · las 10 más recientes (#357–#367) tienen alguna palabra clave en el título |
| E2E-17 | Filtro de ubicación | Revisar avisos | Sin vacantes de otros países (ej. México), aunque sean remotas | — | BUG-18 | ✅ | 2026-10-08 | [nuevas 1](evidencias/E2E-16_nuevas_1.jpg), [nuevas 2](evidencias/E2E-16_nuevas_2.jpg), [nuevas 3](evidencias/E2E-16_nuevas_3.jpg) · todas en Colombia (Bogotá, Medellín) o remotas; ninguna de otro país |

### D. Consultas y gestión por Telegram
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-18 | `/nuevas` y `/mejores` | Escribir ambos | Listas con número, puntaje y link | DoD consulta | | ✅ | 2026-10-08 | [nuevas 1](evidencias/E2E-18_nuevas_1.jpg), [nuevas 2](evidencias/E2E-18_nuevas_2.jpg), [mejores 1](evidencias/E2E-18_mejores_1.jpg), [mejores 2](evidencias/E2E-18_mejores_2.jpg) |
| E2E-19 | `/detalle`, `/guardar`, `/descartar` | Con un número de la lista | Detalle completo; guardada aparece en `/guardadas`; descartada sale de `/mejores` y no se puntúa | DoD guardado y descarte | BUG-29 | ✅ | 2026-10-08 | [detalle](evidencias/E2E-19_detalle.jpg), [guardar y guardadas](evidencias/E2E-19_guardar_guardadas.jpg), [descartar y nuevas](evidencias/E2E-19_descartar_nuevas.jpg) |
| E2E-20 | `/buscar` | `/buscar bogota` (sin tilde) | Encuentra "Bogotá"; ordena por puntaje | Comandos spec | 2026-10-06 | ✅ | 2026-10-08 | [buscar 1](evidencias/E2E-20_buscar_1.jpg), [buscar 2](evidencias/E2E-20_buscar_2.jpg) |
| E2E-21 | `/preferencias` | Ver y cambiar las palabras | Responde con las palabras nuevas; los próximos avisos las usan | — | BUG-28 | ❌ ([BUG-32](../bitacora-bugs.md)) | 2026-10-08 | [ver y reemplazar](evidencias/E2E-21_preferencias_1.jpg), [lista con 1 palabra](evidencias/E2E-21_preferencias_2.jpg), [16 palabras, guarda 15](evidencias/E2E-21_preferencias_3.jpg) |
| E2E-22 | Comando mal escrito / sticker | `/ayudaa` y un sticker | Responde la lista de comandos; nunca se queda callado | — | 2026-10-06 | ✅ | 2026-10-08 | [/ayudaa](evidencias/E2E-22_ayudaa.jpg), [sticker](evidencias/E2E-22_sticker.jpg) |
| E2E-23 | `/pausar` y `/reanudar` | Pausar; esperar el resumen; reanudar | Pausada no recibe avisos ni resumen; al reanudar vuelven | — | multiusuario | ⬜ | | |

### E. Resumen diario
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-24 | Resumen por Telegram y correo | Esperar las 11 am (o `/resumen` + ejecutar el flujo) | Llega por Telegram y aparece en Mailpit | DoD resumen | 2026-10-06 | ⬜ | | |
| E2E-25 | **Resumen sin repetir** | Ejecutar `radar-resumen-diario` a mano después del de las 11 am | No llega un segundo resumen ese día | E2E spec reintento | probar-idempotencia | ⬜ | | |

### F. Fallos y recuperación
| ID | Caso | Pasos | Resultado esperado | Cubre | Antecedente | Estado | Fecha | Evidencia |
|---|---|---|---|---|---|---|---|---|
| E2E-26 | Groq falla → Gemini | Ver `/telemetria/ia` tras unas horas de radar | Llamadas con proveedor gemini y fallback; puntajes guardados igual | DoD telemetría | 2026-10-06/07 | ✅ | 2026-10-08 | [2 días](evidencias/E2E-26_telemetria_2dias.png), [7 días](evidencias/E2E-26_telemetria_7dias.png) · 97 llamadas, Gemini respondió 22 (23 %) por fallo de Groq, 0 errores, costo US$ 0 |
| E2E-27 | Corte de la IA / de profile-api | Apagar profile-api (`docker compose … stop profile-api`) durante una vuelta del radar; volver a prenderlo | Alerta por Telegram; la vuelta siguiente procesa lo pendiente **sin duplicar** vacantes ni avisos | DoD fallos recuperables | caso real 2026-10-07 9:29 | ✅ | 2026-10-08 | [corte y alertas](evidencias/E2E-27_corte_alertas.jpg), [recuperado 1](evidencias/E2E-27_recuperado_1.jpg), [recuperado 2](evidencias/E2E-27_recuperado_2.jpg) · corte de ~1 min con `docker compose stop/start profile-api`; 2 alertas por Telegram; al volver, `/nuevas` igual que antes, sin duplicados |
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
| E2E-20 | `/buscar` solo busca en título y empresa, no en la ubicación. `/buscar bogota` no muestra vacantes como la #303 (BairesDev, 70 pts) o la #359 (Capgemini), que son de Bogotá pero no lo dicen en el título. El bot lo avisa en su ayuda, pero un usuario que busca una ciudad probablemente espera verlas todas. | Baja (mejora) | Pendiente de decidir: incluir la ubicación en la búsqueda |
| E2E-21 | `/preferencias tester` **reemplazó** las 15 palabras por una sola, sin aviso, y las categorías de Get on Board bajaron de 4 a 1. Funciona como está diseñado, pero un usuario que quiere *agregar* una palabra deja el radar casi ciego sin darse cuenta (pasó en la prueba real). | Media (mejora) | Pendiente de decidir: pedir confirmación al reemplazar, o comandos separados para agregar y quitar |
| E2E-22 | Ante un comando mal escrito el bot muestra la lista de comandos, pero no dice que no entendió ("No conozco /ayudaa"). Además la lista no incluye `/vacante <link>` ni `/corregir <tema>`, que sí existen (casos E2E-11 y E2E-14). | Baja (mejora) | Pendiente de decidir: decir qué no entendió y completar la ayuda |
| E2E-06 | La entrevista aceptó "1000000" como aspiración salarial (error al responder; está por debajo del salario mínimo) sin advertir nada. La IA usa el salario al puntuar, así que un dato equivocado puede afectar los puntajes. | Media (mejora) | Pendiente de decidir: validar el rango y pedir confirmación si es muy bajo o muy alto |
| E2E-06 | Pregunta el nivel de inglés aunque el CV dice "lectura básica de documentación técnica". Se defiende porque el CV no dice escritura ni conversación, pero podría usar lo que ya sabe: "Tu CV dice lectura básica; ¿y escritura y conversación?". | Baja (mejora) | Pendiente de decidir |
| E2E-07 | Tras recibir el CV, el bot responde "No tengo preguntas pendientes… Si todavía no me has enviado tu hoja de vida, usa /subir_cv". La segunda frase es genérica (viene de `/completar_perfil`) y no tiene sentido justo después de enviar el CV. | Baja (mejora) | Pendiente de decidir: mensaje propio para "CV recibido y perfil completo" |
| E2E-07 / E2E-08 | El mismo CV en PDF (E2E-06) y en DOCX (E2E-07) dio listas de habilidades distintas: con DOCX aparecen "gestión de defectos en JIRA", "colecciones de API", "códigos de estado HTTP". La extracción con IA no es determinista: el mismo documento puede dar un perfil algo diferente cada vez. | Informativa | Sin cambio por ahora; tenerlo en cuenta al comparar perfiles |
| E2E-14 | ✅ Hallazgo positivo: un link largo de búsqueda de LinkedIn (`/jobs/search-results/?currentJobId=4477446145&…`) se guardó limpio como `/jobs/view/4477446145/`. | Informativa | — |
| E2E-15 | ✅ Prueba exploratoria (fuera del plan): el link de la #303 con `?refId=abc123&trackingId=xyz` se reconoce como la misma vacante. | Informativa | Agregar como caso al plan |
| E2E-16 | En `/buscar bogota` (E2E-20) aparecieron vacantes sin ninguna palabra clave en el título (#188 "Especialista de nómina", #223 "Topógrafo", #225 "Diseño geométrico", #178 "Especialista EWM"). Llegaron hace 4–5 días, antes del filtro de BUG-28; siguen guardadas con 0–15 pts. | Baja | Pendiente de decidir: limpiarlas o dejarlas como histórico |
| E2E-17 | El filtro de ubicación solo saca otros países: llegan vacantes presenciales en Bogotá (ej. #354 "Presencial") aunque la preferencia es Remoto / Medellín. La IA las deja con puntaje bajo, pero igual se notifican. | Baja (mejora) | Pendiente de decidir: filtrar presenciales fuera de la ciudad elegida |
| E2E-13 | La respuesta de `/radar/getonbrd` en modo multiusuario solo trae `found` y `avisos`. Cuando `avisos` sale vacío no se puede saber si fue porque nada pasó los filtros (palabras, nivel, ubicación, ≤ 3 días) o porque todo ya estaba guardado. El docstring dice "misma respuesta que /radar/email + skipped", pero esa rama no los devuelve. | Baja (observabilidad) | Pendiente de decidir: devolver por usuario `filtradas`, `duplicadas` y `created` |
| E2E-13 | Falsa alarma descartada: una pestaña vieja de n8n mostraba la última ejecución el 6 oct 16:00 y parecía que el radar no corría desde entonces. Al refrescar, aparecen ejecuciones cada hora hasta hoy. Lección: confirmar con datos frescos antes de reportar. | Informativa | — |
| E2E-13 | El 8 oct hay dos ejecuciones a las 10:00 (10:00:22 y 10:00:42). Posible doble disparo del reloj (¿al despertar el Mac?). La deduplicación evita vacantes repetidas, pero podría duplicar llamadas a la API. | Informativa | Vigilar si se repite |
| E2E-26 | Latencia máxima de 149 932 ms (2,5 min) frente a una mediana de 1 094 ms. Una llamada tardó 137 veces más que la típica. Posibles causas: reintentos de Groq antes de pasar a Gemini, o el Mac suspendido en medio de la llamada. | Baja | Pendiente: identificar la llamada en `ai_calls` |
| E2E-26 | El respaldo bajó de 30 % (7 oct) a 23 % (2 días), pero sigue alto: casi 1 de cada 4 puntajes depende de Gemini. Ver limitación conocida (sección 8). | Informativa | Vigilar |
| E2E-26 | `?dias=2` y `?dias=7` dan exactamente lo mismo: la telemetría empezó a registrar hace menos de 2 días, así que aún no hay histórico para ver tendencias. | Informativa | — |
| E2E-27 | Durante el corte el usuario que escribió `/nuevas` no recibe ninguna respuesta (las alertas van solo a la admin). Para cualquier otro usuario el bot simplemente se queda callado, y el comando se pierde: no se reintenta al volver. | Media (mejora) | Pendiente de decidir: responder "El servicio no está disponible, intenta en unos minutos" desde n8n cuando profile-api no responde |
| E2E-27 | Una sola causa (profile-api apagado) generó 2 alertas: `verificar-acceso` y `telegram-invitacion` (que llama al primero). En un corte largo, cada mensaje de cada usuario dispara 2 alertas. | Baja | Pendiente de decidir: alertar una sola vez por causa / agrupar |
| E2E-27 | El texto de la alerta ("incorrect host (domain) value") es el error técnico de n8n y despista: el host está bien, el servicio está apagado. | Informativa | Agregar a la alerta una pista: "¿está prendido profile-api?" |
| E2E-27 | La #367 (agregada con `/vacante`, sin título ni descripción) recibió 15 pts en la vuelta de las 15:00. La IA puntuó una vacante de la que no sabe nada: ese número no tiene sustento. | Baja (mejora) | Pendiente de decidir: no puntuar vacantes sin título ni descripción, o marcarlas "sin datos" |
| E2E-01 | El perfil de un usuario que no es de QA (Tech Lead / AI Engineer) queda incompleto: el esquema de habilidades es de QA (`QA`, `Automatización`, `Bases de datos`, `Herramientas`), así que sus lenguajes, frameworks e IA no tienen dónde ir y "QA" y "Automatización" salen vacíos. Además, 4 de 8 experiencias quedaron con fechas "? – ?" y 3 sin cargo ("— en Dale"). | Media (mejora) | Pendiente de decidir: esquema de habilidades general para multiusuario y revisar la extracción de experiencias |
| E2E-01 | La entrevista del ayudante solo hizo 2 preguntas (salario y contrato). Aceptó "10000 USD" y "Todos" sin validar ni pedir confirmación (mismo tema de la observación de salario del E2E-06). | Baja | Ver observación E2E-06 |
| E2E-01 | Las palabras clave que la IA sacó del CV del ayudante eran solo 3 ("tech lead, ai engineer, ai"); él tuvo que escribir las suyas. Con 3 palabras el radar le traería muy pocas vacantes. | Baja (mejora) | Pendiente de decidir: sugerir más palabras desde el CV |

### Pendientes de corrección
Se corrigen al terminar de ejecutar todo el plan. Después de cada corrección:
**re-test** del caso que falló y **regresión** (pruebas unitarias e integración).

| Bug / observación | Caso | Re-test | Estado |
|---|---|---|---|
| BUG-32 · `/preferencias` descarta en silencio la palabra 16 | E2E-21 | E2E-21 | Abierto |
| BUG-33 · `/vacante` no muestra el número de la vacante | E2E-14 | E2E-14 y E2E-15 | Abierto |
| Observaciones de la sección 9 | — | El caso de cada una | Por decidir cuáles se corrigen |

## 10. Siguiente nivel (opcional): mutation testing
Romper el código a propósito para comprobar que las pruebas lo detectan
(ej. quitar la deduplicación, invertir el filtro de ubicación, saltar la
idempotencia). Si al "mutar" el código ninguna prueba falla, esa prueba no
está protegiendo nada. Herramienta posible: `mutmut` sobre profile-api.
