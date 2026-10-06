# Bitácora de bugs y hallazgos

Registro de los defectos y hallazgos encontrados mientras se construía el
proyecto: qué se vio, por qué pasaba, cómo se corrigió y cómo se evita que
vuelva a pasar. Se actualiza cada vez que aparece uno nuevo.

**Tipos:** 🐞 bug de código · ⚙️ configuración (n8n / Docker / Gmail) ·
🔍 hallazgo de prueba · 🧭 proceso

**Cómo se detectó:** prueba manual en Telegram · prueba con curl ·
revisión del JSON exportado · prueba automatizada (pytest) · observación de
datos reales · error en uso normal

---

## Resumen

| ID | Fecha | Tipo | Título | Estado |
|---|---|---|---|---|
| BUG-01 | 2026-09-23 | 🐞 | HTTP 500 en /documents después de que el Mac se duerme | Corregido |
| BUG-02 | 2026-09-24 | 🐞 | Mensaje "extraje  caracteres" sin número | Corregido |
| BUG-03 | 2026-09 | ⚙️ | Espacio escondido en expresiones de n8n rompía comparaciones y URLs | Corregido |
| BUG-04 | 2026-09 | 🧭 | Docker usaba código viejo (capas en caché) | Corregido (proceso) |
| BUG-05 | 2026-09-30 | ⚙️ | /perfil sin preferencias: el cambio no estaba publicado en n8n | Corregido (proceso) |
| BUG-06 | 2026-09-30 | 🐞 | /corregir sin tema fallaba en silencio | Corregido |
| BUG-07 | 2026-09-30 | ⚙️ | El If "¿Era corrección?" quedó conectado a la rama equivocada | Corregido |
| BUG-08 | 2026-09-30 | 🐞 | Lector de LinkedIn corría los campos (título = empresa) | Corregido + test |
| BUG-09 | 2026-10-01 | 🐞 | Aviso del radar no llegaba: correos de Indeed sin lector | Corregido + tests |
| BUG-10 | 2026-10-01 | 🐞 | Regresión: /perfil y /corregir dejaron de funcionar | Corregido |
| BUG-11 | 2026-10-01 | 🐞 | Get on Board traía vacantes de 24 a 43 días | Corregido + test |
| BUG-12 | 2026-10-03 | 🔍 | Pre-filtro por idioma no detectaba inglés exigido en el texto | Corregido (IA + regla fija) |
| BUG-13 | 2026-10-03 | 🔍 | Sospecha: la IA ponía 30 a todas las vacantes | Descartado (no era bug) |
| BUG-14 | 2026-10-03 | 🐞 | Listas de Telegram sin link a la vacante | Corregido + test |
| BUG-15 | 2026-10-03 | 🐞 | Texto "5 por hora" quedó desactualizado al cambiar el límite | Corregido |
| BUG-16 | 2026-10-01 / 10-03 | 🧭 | Archivo .git/index.lock bloqueaba los commits | Corregido (proceso) |
| BUG-17 | 2026-10-03 | 🐞 | Prueba de restauración daba PASO revisando solo 1 de 8 tablas (falso positivo) | Corregido + control |
| BUG-18 | 2026-10-03 | 🔍 | Llegaban vacantes de México por LinkedIn: no hay filtro de ubicación para fuentes de correo | Corregido + tests |
| BUG-19 | 2026-10-05 | ⚙️ | Alertas de radar-correo cada ~30 min con "Nodo" y "Error" vacíos | Corregido + probado |
| BUG-20 | 2026-10-05 | ⚙️ | Alerta salió vacía (hasta el nombre del flujo) y Gmail cortaba con otro texto de error | Corregido + probado |
| BUG-21 | 2026-10-05 | 🔍 | El resumen de las 7 am nunca corrió: el Mac estaba en reposo | Causa confirmada (pendiente servidor) |
| BUG-22 | 2026-10-05 | 🔍 | Datos de prueba (usuario 123) mezclados con datos reales | Limpiado (proceso) |
| BUG-23 | 2026-10-05 | 🐞 | /start de alguien ya registrado respondía su apellido (o texto vacío → error) | Corregido |
| BUG-24 | 2026-10-05 | 🐞 | CV escaneado (0 caracteres) seguía el flujo y creaba un perfil vacío | Corregido |
| BUG-25 | 2026-10-05 | 🔍 | Prueba de aislamiento fallaba con "Connection reset" justo después de reiniciar profile-api | Corregido |
| BUG-26 | 2026-10-05 | 🐞 | Al reenviar el CV, la entrevista volvía a hacer las preguntas ya respondidas | Corregido |
| BUG-27 | 2026-10-05 | 🔍 | Prueba de restauración marcaba DIFERENTE porque el radar guardó vacantes durante el respaldo | Corregido |
| BUG-28 | 2026-10-06 | 🐞 | Llegaban vacantes de correo sin relación con la búsqueda (ej. "Analista de nómina") | Corregido + tests |
| BUG-29 | 2026-10-06 | 🐞 | La IA seguía puntuando 111 vacantes viejas sin relación (anteriores a BUG-28) y también las descartadas | Corregido + limpieza |

---

## Detalle

### BUG-01 · HTTP 500 en /documents después de que el Mac se duerme
- **Síntoma:** al mandar el CV por Telegram después de una pausa, profile-api respondía 500 ("terminating connection due to administrator command").
- **Causa raíz:** al dormirse el Mac, Docker reinicia Postgres; profile-api seguía usando una conexión que ya estaba muerta.
- **Corrección:** `pool_pre_ping=True` en `app/db.py` (SQLAlchemy prueba la conexión antes de usarla y la renueva si murió).
- **Cómo se detectó:** error en uso normal.
- **Lección:** al volver de una pausa, correr `bash scripts/start-local.sh`.

### BUG-02 · Mensaje "extraje  caracteres" sin número
- **Síntoma:** el bot respondía "¡Recibí tu archivo y extraje  caracteres…" (sin el número).
- **Causa raíz:** el nodo usaba `{{ $json.char_count }}`, pero el nodo anterior (/documents) no devuelve ese campo; el dato venía de un nodo más atrás.
- **Corrección:** `{{ $('HTTP Request').item.json.char_count }}` (leer el dato del nodo que sí lo tiene).
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-03 · Espacio escondido en expresiones de n8n
- **Síntoma:** comparaciones del If que nunca daban true; una URL que fallaba.
- **Causa raíz:** un espacio invisible antes del texto (`"= {{ $json.step }}"`, URL con espacios al inicio).
- **Corrección:** limpiar los campos; revisar el JSON del nodo (copiar el nodo y mirar el texto).
- **Cómo se detectó:** revisión del JSON exportado.

### BUG-04 · Docker usaba código viejo
- **Síntoma:** después de cambiar el código, la API seguía comportándose igual.
- **Causa raíz:** Docker reutilizaba capas en caché y el contenedor no se recreaba.
- **Corrección:** reconstruir siempre con `up -d --build --force-recreate profile-api`; verificar con `docker compose exec profile-api grep …` que el cambio está adentro.
- **Cómo se detectó:** prueba con curl.

### BUG-05 · /perfil sin preferencias (cambio no publicado)
- **Síntoma:** el editor de n8n tenía el cambio, pero el bot respondía como antes.
- **Causa raíz:** el workflow no se había publicado; el bot corre la última versión **publicada**.
- **Corrección:** publicar y verificar que el punto de Publish quede **verde**. Diagnóstico: pestaña Executions → abrir el nodo → OUTPUT real.
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-06 · /corregir sin tema fallaba en silencio
- **Síntoma:** al escribir `/corregir` solo, el bot no respondía nada.
- **Causa raíz:** el parámetro de la consulta SQL quedaba vacío y el nodo Postgres fallaba sin mostrar error.
- **Corrección:** usar `|| 'ninguno'` cuando el tema queda vacío, para que la consulta corra y el flujo explique cómo usar /corregir.
- **Cómo se detectó:** prueba manual en Telegram (caso negativo).

### BUG-07 · If "¿Era corrección?" conectado a la rama equivocada
- **Síntoma:** después de una corrección, la entrevista seguía con la siguiente pregunta.
- **Causa raíz:** al insertar un If en una conexión, n8n conecta automáticamente el nodo siguiente a la salida **true**.
- **Corrección:** mover la conexión a la salida **false**.
- **Cómo se detectó:** prueba manual en Telegram.

### BUG-08 · Lector de LinkedIn corría los campos
- **Síntoma:** una vacante quedó guardada con título "Rappi" y empresa "Bogotá".
- **Causa raíz:** una línea extra del correo ("3 personas estudiaron en la misma institución…") se tomaba como título, y todo se corría una posición.
- **Corrección:** ampliar la regex de "ruido" (contactos, exalumnos, personas, solicitantes…). Se borró el registro malo y se reprocesó el correo.
- **Prueba de regresión:** `test_linkedin_ignora_personas_de_tu_institucion`.
- **Cómo se detectó:** observación de datos reales.

### BUG-09 · El aviso del radar no llegaba a Telegram
- **Síntoma:** al probar el workflow radar-correo no llegaba ningún aviso.
- **Causa raíz (dos):** (1) el trigger de correo solo reacciona a correos que **llegan nuevos**; marcar como no leído uno viejo no lo dispara. (2) El correo que sí llegó era de Indeed, que todavía no tenía lector (`source: null`).
- **Corrección:** se escribió `parse_indeed`. Para probar se usó *pin data* (fijar la salida de un nodo), porque "Execute step" reutiliza resultados viejos.
- **Pruebas:** 4 tests de Indeed (`test_indeed_*`).
- **Cómo se detectó:** prueba manual + Executions de n8n.

### BUG-10 · Regresión: /perfil y /corregir dejaron de funcionar
- **Síntoma:** las reglas 4 y 5 del Switch decían `perfil` y `corregir`, sin la barra `/`.
- **Causa raíz:** al ponerle nombre a las salidas, se escribió el nombre en la caja del **valor** en lugar de en "Output Name".
- **Corrección:** valor `/perfil` y `/corregir`; Output Name `perfil` y `corregir`.
- **Cómo se detectó:** revisión del JSON exportado **antes** de guardarlo en git.

### BUG-11 · Get on Board traía vacantes de 24 a 43 días
- **Síntoma:** en Telegram aparecían vacantes "nuevas" que en realidad eran viejas.
- **Causa raíz:** "nueva" significaba "nueva para el sistema", no "recién publicada". La API de Get on Board incluye vacantes antiguas entre las 50 que devuelve.
- **Corrección:** ignorar las publicadas hace más de 3 días (`published_at`); mostrar la antigüedad en las listas; Get on Board cada hora en vez de cada 4. Las viejas ya guardadas se descartaron con un `UPDATE`.
- **Prueba de regresión:** `test_getonbrd_ignora_las_publicadas_hace_mas_de_3_dias`.
- **Cómo se detectó:** observación de Andrea al usar el bot.
- **Limitación conocida:** los correos de LinkedIn e Indeed no traen fecha de publicación (solo se sabe cuándo llegaron).

### BUG-12 · El pre-filtro por idioma no detectaba inglés exigido en el texto
- **Síntoma:** "QA & Support Engineer" (Niuro) pasó el filtro aunque pide inglés C1.
- **Causa raíz:** el aviso no estaba marcado como "en inglés" (`lang`); el requisito estaba dentro de la descripción.
- **Corrección:** el puntaje con IA detecta el nivel de inglés exigido, y una **regla fija en código** limita el puntaje a 35 si piden inglés avanzado.
- **Prueba:** `test_tope_por_ingles_avanzado`.
- **Cómo se detectó:** revisión manual de los resultados del radar.

### BUG-13 · Sospecha: la IA ponía 30 a todas las vacantes (descartado)
- **Síntoma:** las 5 primeras vacantes puntuadas sacaron exactamente 30.
- **Hipótesis:** la IA no diferenciaba y repetía un valor.
- **Verificación:** se creó una vacante de prueba "ideal" (QA Junior en Medellín, sin inglés, 4 M COP). Resultado: **95**; otras sacaron 15 y 45.
- **Conclusión:** no era un bug. Las 5 primeras eran realmente malas para el perfil (senior, 4 años de experiencia, inglés C1). La vacante de prueba se borró.
- **Cómo se detectó:** observación de resultados + caso de prueba controlado.

### BUG-14 · Listas de Telegram sin link a la vacante
- **Síntoma:** /mejores, /nuevas y /guardadas mostraban la vacante pero no cómo abrirla.
- **Causa raíz:** el link solo se incluía en /detalle.
- **Corrección:** cada línea de las listas y del resumen diario trae el link debajo.
- **Prueba de regresión:** assert del link en `test_lista_muestra_numero_puntaje_y_ayuda`.
- **Cómo se detectó:** observación de Andrea al usar el bot.

### BUG-15 · Texto "5 por hora" desactualizado
- **Síntoma:** el resumen decía "va 5 por hora" cuando el límite ya era 10.
- **Causa raíz:** el número estaba escrito fijo en el texto, separado del lugar donde se configura (n8n).
- **Corrección:** texto genérico ("las va puntuando cada hora").
- **Cómo se detectó:** revisión del mensaje en Telegram.

### BUG-16 · .git/index.lock bloqueaba los commits
- **Síntoma:** git no dejaba hacer commit.
- **Causa raíz:** el asistente corrió `git status` desde su terminal; eso dejó el archivo de bloqueo y no lo pudo borrar.
- **Corrección:** `rm -f .git/index.lock`. Regla: el asistente no corre comandos de git; los corre Andrea.
- **Cómo se detectó:** error al hacer commit.

### BUG-17 · Prueba de restauración con falso positivo
- **Síntoma:** `probar-restauracion.sh` dijo "PASO: el respaldo se restaura completo", pero la tabla comparativa mostraba solo `opportunities`; faltaban 7 de las 8 tablas.
- **Causa raíz:** el ciclo `while read ... done < archivo.conteo` comparte la entrada con `docker compose exec -T`, que se leyó el resto del archivo en la primera vuelta. El ciclo terminó después de una tabla y, como esa coincidía, no había fallas.
- **Corrección:** `< /dev/null` en el comando de docker para que no lea la entrada del ciclo. Además, un control nuevo: si las tablas revisadas no son todas las del conteo, la prueba FALLA.
- **Lección:** una prueba que pasa también hay que revisarla; un PASO sin verificar cuánto se probó puede esconder el bug.
- **Cómo se detectó:** revisión de la salida de la prueba (Andrea la pegó y la tabla estaba incompleta).

### BUG-18 · Vacantes de otros países (México) en Telegram
- **Síntoma:** en /nuevas y en los avisos aparecían vacantes ubicadas en México.
- **Causa raíz:** el filtro de ubicación (remota o Colombia) solo existe para Get on Board. Lo que llega por correo (LinkedIn, Indeed, Workana) se guarda tal cual; depende de cómo esté configurada la alerta en cada portal. La IA baja el puntaje por ubicación pero no excluye.
- **Corrección:** (1) Andrea ajustó sus alertas de LinkedIn; (2) regla fija `ubicacion_sirve()` en `parsers.py`, aplicada en POST /radar/email: si la ubicación nombra otro país (o una ciudad conocida de otro país) NO se guarda, aunque diga "remoto" ("México (En remoto)" casi siempre exige vivir allá). Pasan: Colombia, LATAM/Latinoamérica, "Remoto" sin país y ubicación desconocida (decide la IA). La respuesta trae "skipped". /vacante manual no se filtra (la eligió la usuaria).
- **Prueba de regresión:** 16 casos parametrizados en `test_parsers.py` (9 que sirven, 7 de otro país). 69 tests en total.
- **Cómo se detectó:** observación de Andrea al revisar Telegram + consulta SQL por `location`.

### BUG-19 · Alertas ruidosas y vacías de radar-correo
- **Síntoma:** cada 30-40 minutos llegaba "⚠️ Falló el flujo radar-correo" con Nodo y Error vacíos; aun así las vacantes seguían llegando.
- **Causa raíz (2):** (1) Gmail cierra la conexión IMAP cada cierto tiempo ("This socket has been ended by the other party"); n8n desactiva el flujo y lo reactiva solo, es transitorio. (2) Cuando falla el **disparador**, el Error Trigger trae los datos en `trigger.error`, no en `execution`, y el mensaje solo leía `execution`.
- **Corrección:** If "¿Es corte normal de Gmail?" en alertas-errores (si la descripción contiene "socket has been ended" no avisa) y el texto ahora lee `execution` o, si no existe, `trigger.error`.
- **Prueba:** datos fijados (pin) en el Error Trigger: (1) con el error real de Gmail → rama true, no avisa; (2) con un error de disparador inventado → rama false, llega el aviso con nodo y error.
- **Lección:** una alarma que avisa de cosas que se arreglan solas genera "fatiga de alertas"; hay que filtrar el ruido sin esconder los errores reales.
- **Cómo se detectó:** observación de Andrea en Telegram + JSON de la ejecución de alertas-errores.

### BUG-20 · Alerta vacía en producción + otra variante del corte de Gmail
- **Síntoma:** a las 14:02 llegó "Falló el flujo \"\"" con Nodo y Error vacíos, aunque el arreglo del BUG-19 se había probado con éxito.
- **Causa raíz (2):** (1) el texto usaba `$('Cuando un flujo falla').item...`; con datos fijados (pin) funcionó, pero en la ejecución real no resolvió el item y devolvió vacío. **La prueba con pin no representaba el caso real.** (2) Gmail también corta con "IMAP connection closed unexpectedly", texto que el filtro no reconocía.
- **Corrección:** texto con `$json` (lee igual con pin y en real); filtro con regex `socket has been ended|closed unexpectedly|automatically retry` sobre descripción + causa; y la solución de raíz que sugiere el propio n8n: **Force Reconnect = 20 min** en el Timbre de radar-correo (los cortes eran cada 30-40 min).
- **Prueba:** pin con el JSON REAL de la ejecución de las 14:02 → true (no avisa); mismo JSON con un error inventado → false y el mensaje llega con flujo, nodo y error llenos. ("Copy to editor" de una ejecución real requiere plan pago.)
- **Lección:** los datos de prueba deben copiarse de un caso real, y una prueba que pasa con datos simulados no garantiza el comportamiento en producción.
- **Cómo se detectó:** alerta vacía en Telegram + JSON de la ejecución.

### BUG-21 · El resumen de las 7 am nunca se envió
- **Síntoma:** no llegó el resumen ni el 4 ni el 5 de octubre.
- **Causa raíz:** en Executions de radar-resumen-diario solo existía la ejecución manual del 3/10: a las 7 am el Mac estaba en reposo y n8n no recupera los horarios perdidos.
- **Prueba:** se movió el reloj a las 2 pm con el Mac despierto → el resumen llegó. El reloj funciona; la causa es el reposo.
- **Corrección temporal:** hora de la mañana con el Mac prendido (Andrea la elige). De fondo: servidor (riesgo ya anotado).
- **Cómo se detectó:** observación de Andrea + pestaña Executions.

### BUG-22 · Datos de prueba mezclados con los reales
- **Síntoma:** al crear la tabla users (migración 0011) apareció un usuario "123" que no es una persona.
- **Causa raíz:** en semanas anteriores se probaron endpoints con curl usando telegram_user_id = 123 y ese documento quedó en la base real; la migración registra como usuario a todo el que tenga datos.
- **Corrección:** conteo por tabla con `UNION ALL` (solo 1 fila en documents) y `DELETE` del documento y del usuario.
- **Prevención:** las pruebas con curl usan ids claramente falsos (900000001, 900000002…) y se borran al terminar; la prueba de aislamiento limpia lo que crea.
- **Cómo se detectó:** verificación de la migración con SQL (Andrea).

### BUG-23 · /start de un usuario ya registrado respondía su apellido
- **Síntoma:** al revisar el flujo para multiusuario, el nodo de la salida "start" del Switch enviaba `message.chat.last_name`.
- **Causa raíz:** quedó de las primeras pruebas de la Semana 2 y nunca se cambió. Si la persona no tiene apellido en Telegram, el texto queda vacío, Telegram lo rechaza y salta la alarma.
- **Corrección:** nodo "Saludo: ya registrado" con un texto fijo de ayuda.
- **Cómo se detectó:** revisión del JSON exportado. (Al corregirlo, la nota de otro nodo quedó pegada en el campo Text por error; se vio al probar /start y se corrigió.)

### BUG-24 · CV sin texto (PDF escaneado) creaba un perfil vacío
- **Síntoma:** el perfil de un usuario de prueba (Ludwing) mostraba nombre, experiencia y habilidades vacíos; solo las preferencias de la entrevista.
- **Causa raíz:** su PDF era una imagen: el extractor sacó 0 caracteres y el flujo siguió igual (guardó el documento, llamó a la IA con texto vacío y guardó un perfil vacío). Nunca se había probado con un archivo sin texto.
- **Corrección:** If "¿Se pudo leer el CV?" después de extraer el texto: menos de 200 caracteres → avisa cómo enviar el archivo y no guarda nada. (Leer escaneados con OCR queda para el Proyecto 2.)
- **Cómo se detectó:** prueba con un usuario real + `SELECT filename, char_count FROM documents` → 0.

### BUG-25 · La prueba automática arrancaba antes que la API
- **Síntoma:** `probar-aislamiento.py` se caía en el primer llamado con `ConnectionResetError` (no era un fallo de aislamiento).
- **Causa raíz:** se corrió justo después de recrear el contenedor; profile-api aún aplicaba migraciones y arrancaba. La prueba no esperaba a que el sistema estuviera listo (prueba "inestable" por tiempos).
- **Corrección:** el script espera a que `/health` responda (hasta 60 s) antes de empezar.
- **Resultado:** 42 de 42 casos pasan (5 usuarios aislados).
- **Cómo se detectó:** primera corrida del script.

### BUG-26 · La entrevista repetía preguntas ya respondidas
- **Síntoma:** al reenviar el CV (prueba de MinIO), el bot volvió a hacer las 8 preguntas de siempre.
- **Causa raíz:** "Buscar primera/siguiente pregunta" solo miraban los `faltantes` del perfil NUEVO (lo que el CV no dice), sin revisar las respuestas que la persona ya había dado en `interview_answers`. Existía desde la Semana 4; no se notaba porque casi nunca se reenvía el CV.
- **Corrección:** ambas consultas excluyen los temas ya respondidos (`AND topic NOT IN (SELECT topic FROM interview_answers WHERE telegram_user_id = … )`). Para cambiar un dato ya respondido está /corregir.
- **Lección:** probar también el "segundo uso" de un flujo (reenviar, repetir), no solo el primero.
- **Cómo se detectó:** observación de Andrea al probar MinIO.

### BUG-27 · Falso negativo en la prueba de restauración
- **Síntoma:** `opportunities` esperado 281, restaurado 283 → "FALLO", aunque el respaldo estaba bien (MinIO OK).
- **Causa raíz:** el script contaba las filas y DESPUÉS sacaba el respaldo; entre los dos momentos el radar de n8n guardó 2 vacantes. Se comparaban dos fotos tomadas en momentos distintos (condición de carrera en el diseño de la prueba).
- **Corrección:** se cuenta antes Y después del respaldo; es válido si lo restaurado queda entre los dos números (archivo .conteo: "tabla antes despues"). Compatible con respaldos viejos (un solo número).
- **Lección:** con BUG-17 (falso positivo) son las dos caras: una prueba debe fallar cuando hay error real y NO fallar cuando el sistema está bien.
- **Cómo se detectó:** primera prueba de restauración con el radar multiusuario corriendo.

### BUG-28 · Vacantes de correo que no tienen nada que ver
- **Síntoma:** a Telegram llegaban avisos como "Analista de nómina" que no sirven y llenan el chat.
- **Causa raíz:** en la búsqueda por usuario (multiusuario parte 4) las palabras clave solo se aplicaron a Get on Board; las vacantes de LinkedIn/Indeed/Workana por correo se guardaban sin revisar el título.
- **Corrección:** `busqueda.filtrar_por_palabras()` en POST /radar/email con las palabras del dueño del buzón (sin palabras configuradas no filtra). Se cuentan en "skipped".
- **Prueba de regresión:** 2 tests en `test_busqueda.py` (114 en total).
- **Cómo se detectó:** observación de Andrea al usar el bot.

---

### BUG-29 · La IA puntuaba vacantes viejas que no sirven
- **Síntoma:** al probar la telemetría, radar-puntaje mandó a la IA "Recepcionista hotel", "Ejecutivo(a) de Negocios", etc.
- **Causa raíz:** (1) BUG-28 filtró solo las vacantes nuevas; las que ya estaban en la fila de puntaje (111, del 30-sep y 1-oct, confirmado con una consulta SQL GROUP BY por día) seguían ahí. (2) /opportunities/pending-score no excluía las de estado "descartada": gastaba IA en vacantes que la persona ya había descartado.
- **Corrección:** pending-score ahora excluye `status = 'descartada'`. Limpieza única con `python -m app.limpiar_pendientes` (vista previa) y `--aplicar`: les pasa el mismo filtro de palabras de cada usuario y marca como descartadas las que no coinciden (no borra nada).
- **Prueba de regresión:** el filtro ya tiene tests (BUG-28); se verificó con la vista previa antes de aplicar y con la consulta SQL después.
- **Cómo se detectó:** revisando la salida del nodo "Pedir vacantes sin puntaje" durante la prueba de telemetría.
- **Lección:** cuando se agrega un filtro, revisar también los datos que ya estaban guardados, no solo los nuevos.
- **Hallazgo extra (falso negativo):** la vista previa mostró que las palabras de Andrea descartaban vacantes de QA ("Test Analyst", "Junior SDET", "Test Automation", "Automatizador") y de servicio/soporte. Se ajustaron las palabras (test, sdet, automatiza, automation, soporte, mesa de ayuda, servicio al cliente, ia, ai, artificial) y el máximo de palabras subió de 12 a 15 (`MAX_PALABRAS`). Lección: el prefijo "tester" no atrapa "test"; conviene usar la raíz más corta.

---

## Riesgos y limitaciones conocidas (pendientes)

- **El sistema depende de que el Mac esté prendido.** Si está dormido a las 7 am, el resumen diario no se envía, y n8n no lo reenvía después. Mientras tanto: Mac conectado, Docker abierto y sin suspensión automática. Solución de fondo: servidor (Semana 7).
- **El túnel de Cloudflare cambia de URL** al reiniciarse; si se cae, el bot no recibe comandos (los avisos que salen sí funcionan).
- **LinkedIn por correo no trae descripción ni fecha** → el puntaje de esas vacantes es menos preciso.
- **`remote_local` de Get on Board** puede estar limitado a un país (no se lee `location_tenants`).
- **chat_id fijo (8553351572)** en varios workflows → decidir multiusuario en Semana 7.
- **Si falla n8n entero o Telegram, la alerta tampoco llega** (alertas-errores usa el mismo n8n y el mismo bot). Detecta fallas de un flujo, no caídas del sistema completo.
