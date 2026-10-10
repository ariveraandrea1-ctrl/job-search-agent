# Bitácora de bugs y hallazgos

Aquí voy anotando los errores y hallazgos que encuentro mientras construyo y pruebo el proyecto: qué pasaba, por qué, cómo lo corregí y qué hice para que no vuelva a pasar. La actualizo cada vez que aparece uno nuevo.

Uso cuatro tipos: Bug (error en el código), Configuración (n8n, Docker o Gmail), Hallazgo (algo que salió en una prueba o revisando datos) y Proceso (una forma de trabajar que causaba el problema).

En cada uno anoto también cómo lo detecté: probando en Telegram, con curl, revisando el JSON exportado de n8n, con pytest, mirando datos reales o simplemente usando el bot.

## Resumen

| ID | Fecha | Tipo | Título | Estado |
|---|---|---|---|---|
| BUG-01 | 2026-09-23 | Bug | HTTP 500 en /documents después de que el Mac se duerme | Corregido |
| BUG-02 | 2026-09-24 | Bug | Mensaje "extraje  caracteres" sin número | Corregido |
| BUG-03 | 2026-09 | Configuración | Espacio escondido en expresiones de n8n rompía comparaciones y URLs | Corregido |
| BUG-04 | 2026-09 | Proceso | Docker usaba código viejo (capas en caché) | Corregido (proceso) |
| BUG-05 | 2026-09-30 | Configuración | /perfil sin preferencias: el cambio no estaba publicado en n8n | Corregido (proceso) |
| BUG-06 | 2026-09-30 | Bug | /corregir sin tema fallaba en silencio | Corregido |
| BUG-07 | 2026-09-30 | Configuración | El If "¿Era corrección?" quedó conectado a la rama equivocada | Corregido |
| BUG-08 | 2026-09-30 | Bug | Lector de LinkedIn corría los campos (título = empresa) | Corregido, con test |
| BUG-09 | 2026-10-01 | Bug | Aviso del radar no llegaba: correos de Indeed sin lector | Corregido, con tests |
| BUG-10 | 2026-10-01 | Bug | Regresión: /perfil y /corregir dejaron de funcionar | Corregido |
| BUG-11 | 2026-10-01 | Bug | Get on Board traía vacantes de 24 a 43 días | Corregido, con test |
| BUG-12 | 2026-10-03 | Hallazgo | Pre-filtro por idioma no detectaba inglés exigido en el texto | Corregido (IA y regla fija) |
| BUG-13 | 2026-10-03 | Hallazgo | Sospecha: la IA ponía 30 a todas las vacantes | Descartado (no era bug) |
| BUG-14 | 2026-10-03 | Bug | Listas de Telegram sin link a la vacante | Corregido, con test |
| BUG-15 | 2026-10-03 | Bug | Texto "5 por hora" quedó desactualizado al cambiar el límite | Corregido |
| BUG-16 | 2026-10-01 / 10-03 | Proceso | Archivo .git/index.lock bloqueaba los commits | Corregido (proceso) |
| BUG-17 | 2026-10-03 | Bug | Prueba de restauración daba PASO revisando solo 1 de 8 tablas (falso positivo) | Corregido, con un control nuevo |
| BUG-18 | 2026-10-03 | Hallazgo | Llegaban vacantes de México por LinkedIn: no hay filtro de ubicación para fuentes de correo | Corregido, con tests |
| BUG-19 | 2026-10-05 | Configuración | Alertas de radar-correo cada ~30 min con "Nodo" y "Error" vacíos | Corregido y probado |
| BUG-20 | 2026-10-05 | Configuración | Alerta salió vacía (hasta el nombre del flujo) y Gmail cortaba con otro texto de error | Corregido y probado |
| BUG-21 | 2026-10-05 | Hallazgo | El resumen de las 7 am nunca corrió: el Mac estaba en reposo | Causa confirmada (pendiente servidor) |
| BUG-22 | 2026-10-05 | Hallazgo | Datos de prueba (usuario 123) mezclados con datos reales | Limpiado (proceso) |
| BUG-23 | 2026-10-05 | Bug | /start de alguien ya registrado respondía su apellido (o texto vacío: error) | Corregido |
| BUG-24 | 2026-10-05 | Bug | CV escaneado (0 caracteres) seguía el flujo y creaba un perfil vacío | Corregido |
| BUG-25 | 2026-10-05 | Hallazgo | Prueba de aislamiento fallaba con "Connection reset" justo después de reiniciar profile-api | Corregido |
| BUG-26 | 2026-10-05 | Bug | Al reenviar el CV, la entrevista volvía a hacer las preguntas ya respondidas | Corregido |
| BUG-27 | 2026-10-05 | Hallazgo | Prueba de restauración marcaba DIFERENTE porque el radar guardó vacantes durante el respaldo | Corregido |
| BUG-28 | 2026-10-06 | Bug | Llegaban vacantes de correo sin relación con la búsqueda (ej. "Analista de nómina") | Corregido, con tests |
| BUG-29 | 2026-10-06 | Bug | La IA seguía puntuando 111 vacantes viejas sin relación (anteriores a BUG-28) y también las descartadas | Corregido, con limpieza |
| BUG-30 | 2026-10-06 | Bug | /completar_perfil fallaba: Telegram rechazaba mensajes con "_" ("can't parse entities") | Corregido, con tests |
| BUG-31 | 2026-10-07 | Bug | El sistema no se podía reconstruir desde el repo sin pasos ocultos (prueba de reconstrucción) | Corregido y probado desde cero |
| BUG-32 | 2026-10-08 | Bug | /preferencias descarta en silencio las palabras después de la 15 | Abierto |
| BUG-33 | 2026-10-08 | Bug | /vacante no muestra el número (#) de la vacante guardada o repetida | Abierto |
| BUG-34 | 2026-10-09 | Bug | Con el radar en pausa siguen llegando avisos de vacantes por correo (LinkedIn/Indeed) | Abierto |
| BUG-35 | 2026-10-09 | Bug | El filtro de ubicación deja pasar vacantes de México escritas como "MEX" o "CMX" (regresión de BUG-18) | Abierto |
| BUG-36 | 2026-10-10 | Configuración | El bot no recibe mensajes tras reiniciar: Telegram queda sin webhook y `start-local.sh` dice "Listo" igual | Corregido y probado |

## Detalle de cada bug

### BUG-01. HTTP 500 en /documents después de que el Mac se duerme

Síntoma: al mandar el CV por Telegram después de una pausa, profile-api respondía 500 ("terminating connection due to administrator command").

Causa: al dormirse el Mac, Docker reinicia Postgres; profile-api seguía usando una conexión que ya estaba muerta.

Cómo lo corregí: `pool_pre_ping=True` en `app/db.py` (SQLAlchemy prueba la conexión antes de usarla y la renueva si murió).

Cómo lo detecté: error en uso normal.

Lo que aprendí: al volver de una pausa, correr `bash scripts/start-local.sh`.

### BUG-02. Mensaje "extraje  caracteres" sin número

Síntoma: el bot respondía "¡Recibí tu archivo y extraje  caracteres…" (sin el número).

Causa: el nodo usaba `{{ $json.char_count }}`, pero el nodo anterior (/documents) no devuelve ese campo; el dato venía de un nodo más atrás.

Cómo lo corregí: `{{ $('HTTP Request').item.json.char_count }}` (leer el dato del nodo que sí lo tiene).

Cómo lo detecté: prueba manual en Telegram.

### BUG-03. Espacio escondido en expresiones de n8n

Síntoma: comparaciones del If que nunca daban true; una URL que fallaba.

Causa: un espacio invisible antes del texto (`"= {{ $json.step }}"`, URL con espacios al inicio).

Cómo lo corregí: limpiar los campos; revisar el JSON del nodo (copiar el nodo y mirar el texto).

Cómo lo detecté: revisión del JSON exportado.

### BUG-04. Docker usaba código viejo

Síntoma: después de cambiar el código, la API seguía comportándose igual.

Causa: Docker reutilizaba capas en caché y el contenedor no se recreaba.

Cómo lo corregí: reconstruir siempre con `up -d --build --force-recreate profile-api`; verificar con `docker compose exec profile-api grep …` que el cambio está adentro.

Cómo lo detecté: prueba con curl.

### BUG-05. /perfil sin preferencias (cambio no publicado)

Síntoma: el editor de n8n tenía el cambio, pero el bot respondía como antes.

Causa: el workflow no se había publicado; el bot corre la última versión publicada.

Cómo lo corregí: publicar y verificar que el punto de Publish quede verde. Para diagnosticarlo: pestaña Executions, abrir el nodo y mirar el OUTPUT real.

Cómo lo detecté: prueba manual en Telegram.

### BUG-06. /corregir sin tema fallaba en silencio

Síntoma: al escribir `/corregir` solo, el bot no respondía nada.

Causa: el parámetro de la consulta SQL quedaba vacío y el nodo Postgres fallaba sin mostrar error.

Cómo lo corregí: usar `|| 'ninguno'` cuando el tema queda vacío, para que la consulta corra y el flujo explique cómo usar /corregir.

Cómo lo detecté: prueba manual en Telegram (caso negativo).

### BUG-07. If "¿Era corrección?" conectado a la rama equivocada

Síntoma: después de una corrección, la entrevista seguía con la siguiente pregunta.

Causa: al insertar un If en una conexión, n8n conecta automáticamente el nodo siguiente a la salida true.

Cómo lo corregí: mover la conexión a la salida false.

Cómo lo detecté: prueba manual en Telegram.

### BUG-08. Lector de LinkedIn corría los campos

Síntoma: una vacante quedó guardada con título "Rappi" y empresa "Bogotá".

Causa: una línea extra del correo ("3 personas estudiaron en la misma institución…") se tomaba como título, y todo se corría una posición.

Cómo lo corregí: ampliar la regex de "ruido" (contactos, exalumnos, personas, solicitantes…). Se borró el registro malo y se reprocesó el correo.

Prueba de regresión: `test_linkedin_ignora_personas_de_tu_institucion`.

Cómo lo detecté: observación de datos reales.

### BUG-09. El aviso del radar no llegaba a Telegram

Síntoma: al probar el workflow radar-correo no llegaba ningún aviso.

Causas (fueron dos): (1) el trigger de correo solo reacciona a correos que llegan nuevos; marcar como no leído uno viejo no lo dispara. (2) El correo que sí llegó era de Indeed, que todavía no tenía lector (`source: null`).

Cómo lo corregí: se escribió `parse_indeed`. Para probar se usó pin data (fijar la salida de un nodo), porque "Execute step" reutiliza resultados viejos.

Pruebas: 4 tests de Indeed (`test_indeed_*`).

Cómo lo detecté: prueba manual y revisando Executions en n8n.

### BUG-10. Regresión: /perfil y /corregir dejaron de funcionar

Síntoma: las reglas 4 y 5 del Switch decían `perfil` y `corregir`, sin la barra `/`.

Causa: al ponerle nombre a las salidas, se escribió el nombre en la caja del valor en lugar de en "Output Name".

Cómo lo corregí: valor `/perfil` y `/corregir`; Output Name `perfil` y `corregir`.

Cómo lo detecté: revisión del JSON exportado antes de guardarlo en git.

### BUG-11. Get on Board traía vacantes de 24 a 43 días

Síntoma: en Telegram aparecían vacantes "nuevas" que en realidad eran viejas.

Causa: "nueva" significaba "nueva para el sistema", no "recién publicada". La API de Get on Board incluye vacantes antiguas entre las 50 que devuelve.

Cómo lo corregí: ignorar las publicadas hace más de 3 días (`published_at`); mostrar la antigüedad en las listas; Get on Board cada hora en vez de cada 4. Las viejas ya guardadas se descartaron con un `UPDATE`.

Prueba de regresión: `test_getonbrd_ignora_las_publicadas_hace_mas_de_3_dias`.

Cómo lo detecté: lo noté usando el bot.

Limitación conocida: los correos de LinkedIn e Indeed no traen fecha de publicación (solo se sabe cuándo llegaron).

### BUG-12. El pre-filtro por idioma no detectaba inglés exigido en el texto

Síntoma: "QA & Support Engineer" (Niuro) pasó el filtro aunque pide inglés C1.

Causa: el aviso no estaba marcado como "en inglés" (`lang`); el requisito estaba dentro de la descripción.

Cómo lo corregí: el puntaje con IA detecta el nivel de inglés exigido, y una regla fija en código limita el puntaje a 35 si piden inglés avanzado.

Prueba: `test_tope_por_ingles_avanzado`.

Cómo lo detecté: revisión manual de los resultados del radar.

### BUG-13. Sospecha: la IA ponía 30 a todas las vacantes (descartado)

Síntoma: las 5 primeras vacantes puntuadas sacaron exactamente 30.

Hipótesis: la IA no diferenciaba y repetía un valor.

Verificación: se creó una vacante de prueba "ideal" (QA Junior en Medellín, sin inglés, 4 M COP). Resultado: 95; otras sacaron 15 y 45.

Conclusión: no era un bug. Las 5 primeras eran realmente malas para el perfil (senior, 4 años de experiencia, inglés C1). La vacante de prueba se borró.

Cómo lo detecté: observación de resultados y caso de prueba controlado.

### BUG-14. Listas de Telegram sin link a la vacante

Síntoma: /mejores, /nuevas y /guardadas mostraban la vacante pero no cómo abrirla.

Causa: el link solo se incluía en /detalle.

Cómo lo corregí: cada línea de las listas y del resumen diario trae el link debajo.

Prueba de regresión: assert del link en `test_lista_muestra_numero_puntaje_y_ayuda`.

Cómo lo detecté: lo noté usando el bot.

### BUG-15. Texto "5 por hora" desactualizado

Síntoma: el resumen decía "va 5 por hora" cuando el límite ya era 10.

Causa: el número estaba escrito fijo en el texto, separado del lugar donde se configura (n8n).

Cómo lo corregí: texto genérico ("las va puntuando cada hora").

Cómo lo detecté: revisión del mensaje en Telegram.

### BUG-16. .git/index.lock bloqueaba los commits

Síntoma: git no me dejaba hacer commit.

Causa: se corrió `git status` desde una terminal distinta a la mía, eso dejó el archivo de bloqueo `.git/index.lock` y no se pudo borrar desde allá.

Cómo lo corregí: con `rm -f .git/index.lock`. Desde entonces la regla es que los comandos de git los corro yo, desde mi terminal.

Cómo lo detecté: al hacer un commit.

### BUG-17. Prueba de restauración con falso positivo

Síntoma: `probar-restauracion.sh` dijo "PASO: el respaldo se restaura completo", pero la tabla comparativa mostraba solo `opportunities`; faltaban 7 de las 8 tablas.

Causa: el ciclo `while read ... done < archivo.conteo` comparte la entrada con `docker compose exec -T`, que se leyó el resto del archivo en la primera vuelta. El ciclo terminó después de una tabla y, como esa coincidía, no había fallas.

Cómo lo corregí: `< /dev/null` en el comando de docker para que no lea la entrada del ciclo. Además, un control nuevo: si las tablas revisadas no son todas las del conteo, la prueba FALLA.

Lo que aprendí: una prueba que pasa también hay que revisarla; un PASO sin verificar cuánto se probó puede esconder el bug.

Cómo lo detecté: revisión de la salida de la prueba (la pegué y vi que la tabla estaba incompleta).

### BUG-18. Vacantes de otros países (México) en Telegram

Síntoma: en /nuevas y en los avisos aparecían vacantes ubicadas en México.

Causa: el filtro de ubicación (remota o Colombia) solo existe para Get on Board. Lo que llega por correo (LinkedIn, Indeed, Workana) se guarda tal cual; depende de cómo esté configurada la alerta en cada portal. La IA baja el puntaje por ubicación pero no excluye.

Cómo lo corregí: (1) ajusté mis alertas de LinkedIn; (2) regla fija `ubicacion_sirve()` en `parsers.py`, aplicada en POST /radar/email: si la ubicación nombra otro país (o una ciudad conocida de otro país) NO se guarda, aunque diga "remoto" ("México (En remoto)" casi siempre exige vivir allá). Pasan: Colombia, LATAM/Latinoamérica, "Remoto" sin país y ubicación desconocida (decide la IA). La respuesta trae "skipped". /vacante manual no se filtra (la eligió la usuaria).

Prueba de regresión: 16 casos parametrizados en `test_parsers.py` (9 que sirven, 7 de otro país). 69 tests en total.

Cómo lo detecté: lo noté revisando Telegram y lo confirmé con una consulta SQL por `location`.

### BUG-19. Alertas ruidosas y vacías de radar-correo

Síntoma: cada 30-40 minutos llegaba "Falló el flujo radar-correo" con Nodo y Error vacíos; aun así las vacantes seguían llegando.

Causas (fueron dos): (1) Gmail cierra la conexión IMAP cada cierto tiempo ("This socket has been ended by the other party"); n8n desactiva el flujo y lo reactiva solo, es transitorio. (2) Cuando falla el disparador, el Error Trigger trae los datos en `trigger.error`, no en `execution`, y el mensaje solo leía `execution`.

Cómo lo corregí: If "¿Es corte normal de Gmail?" en alertas-errores (si la descripción contiene "socket has been ended" no avisa) y el texto ahora lee `execution` o, si no existe, `trigger.error`.

Prueba: datos fijados (pin) en el Error Trigger: (1) con el error real de Gmail: rama true, no avisa; (2) con un error de disparador inventado: rama false, llega el aviso con nodo y error.

Lo que aprendí: una alarma que avisa de cosas que se arreglan solas genera "fatiga de alertas"; hay que filtrar el ruido sin esconder los errores reales.

Cómo lo detecté: lo noté en Telegram y lo confirmé en el JSON de la ejecución de alertas-errores.

### BUG-20. Alerta vacía en producción y otra variante del corte de Gmail

Síntoma: a las 14:02 llegó "Falló el flujo \"\"" con Nodo y Error vacíos, aunque el arreglo del BUG-19 se había probado con éxito.

Causas (fueron dos): (1) el texto usaba `$('Cuando un flujo falla').item...`; con datos fijados (pin) funcionó, pero en la ejecución real no resolvió el item y devolvió vacío. La prueba con pin no representaba el caso real. (2) Gmail también corta con "IMAP connection closed unexpectedly", texto que el filtro no reconocía.

Cómo lo corregí: texto con `$json` (lee igual con pin y en real); filtro con regex `socket has been ended|closed unexpectedly|automatically retry` sobre descripción y causa; y la solución de raíz que sugiere el propio n8n: Force Reconnect = 20 min en el Timbre de radar-correo (los cortes eran cada 30-40 min).

Prueba: pin con el JSON REAL de la ejecución de las 14:02: true (no avisa); mismo JSON con un error inventado: false y el mensaje llega con flujo, nodo y error llenos. ("Copy to editor" de una ejecución real requiere plan pago.)

Lo que aprendí: los datos de prueba deben copiarse de un caso real, y una prueba que pasa con datos simulados no garantiza el comportamiento en producción.

Cómo lo detecté: por la alerta vacía en Telegram y el JSON de la ejecución.

### BUG-21. El resumen de las 7 am nunca se envió

Síntoma: no llegó el resumen ni el 4 ni el 5 de octubre.

Causa: en Executions de radar-resumen-diario solo existía la ejecución manual del 3/10: a las 7 am el Mac estaba en reposo y n8n no recupera los horarios perdidos.

Prueba: se movió el reloj a las 2 pm con el Mac despierto: el resumen llegó. El reloj funciona; la causa es el reposo.

Corrección temporal: hora de la mañana con el Mac prendido (la elijo yo). De fondo: servidor (riesgo ya anotado).

Cómo lo detecté: lo noté yo y lo confirmé en la pestaña Executions.

### BUG-22. Datos de prueba mezclados con los reales

Síntoma: al crear la tabla users (migración 0011) apareció un usuario "123" que no es una persona.

Causa: en semanas anteriores se probaron endpoints con curl usando telegram_user_id = 123 y ese documento quedó en la base real; la migración registra como usuario a todo el que tenga datos.

Cómo lo corregí: conteo por tabla con `UNION ALL` (solo 1 fila en documents) y `DELETE` del documento y del usuario.

Para que no se repita: las pruebas con curl usan ids claramente falsos (900000001, 900000002…) y se borran al terminar; la prueba de aislamiento limpia lo que crea.

Cómo lo detecté: revisando la migración con SQL.

### BUG-23. /start de un usuario ya registrado respondía su apellido

Síntoma: al revisar el flujo para multiusuario, el nodo de la salida "start" del Switch enviaba `message.chat.last_name`.

Causa: quedó de las primeras pruebas de la Semana 2 y nunca se cambió. Si la persona no tiene apellido en Telegram, el texto queda vacío, Telegram lo rechaza y salta la alarma.

Cómo lo corregí: nodo "Saludo: ya registrado" con un texto fijo de ayuda.

Cómo lo detecté: revisión del JSON exportado. (Al corregirlo, la nota de otro nodo quedó pegada en el campo Text por error; se vio al probar /start y se corrigió.)

### BUG-24. CV sin texto (PDF escaneado) creaba un perfil vacío

Síntoma: el perfil de un usuario de prueba (Ludwing) mostraba nombre, experiencia y habilidades vacíos; solo las preferencias de la entrevista.

Causa: su PDF era una imagen: el extractor sacó 0 caracteres y el flujo siguió igual (guardó el documento, llamó a la IA con texto vacío y guardó un perfil vacío). Nunca se había probado con un archivo sin texto.

Cómo lo corregí: If "¿Se pudo leer el CV?" después de extraer el texto: menos de 200 caracteres: avisa cómo enviar el archivo y no guarda nada. (Leer escaneados con OCR queda para el Proyecto 2.)

Cómo lo detecté: prueba con un usuario real y `SELECT filename, char_count FROM documents`: 0.

### BUG-25. La prueba automática arrancaba antes que la API

Síntoma: `probar-aislamiento.py` se caía en el primer llamado con `ConnectionResetError` (no era un fallo de aislamiento).

Causa: se corrió justo después de recrear el contenedor; profile-api aún aplicaba migraciones y arrancaba. La prueba no esperaba a que el sistema estuviera listo (prueba "inestable" por tiempos).

Cómo lo corregí: el script espera a que `/health` responda (hasta 60 s) antes de empezar.

Resultado: 42 de 42 casos pasan (5 usuarios aislados).

Cómo lo detecté: primera corrida del script.

### BUG-26. La entrevista repetía preguntas ya respondidas

Síntoma: al reenviar el CV (prueba de MinIO), el bot volvió a hacer las 8 preguntas de siempre.

Causa: "Buscar primera/siguiente pregunta" solo miraban los `faltantes` del perfil NUEVO (lo que el CV no dice), sin revisar las respuestas que la persona ya había dado en `interview_answers`. Existía desde la Semana 4; no se notaba porque casi nunca se reenvía el CV.

Cómo lo corregí: ambas consultas excluyen los temas ya respondidos (`AND topic NOT IN (SELECT topic FROM interview_answers WHERE telegram_user_id = … )`). Para cambiar un dato ya respondido está /corregir.

Lo que aprendí: probar también el "segundo uso" de un flujo (reenviar, repetir), no solo el primero.

Cómo lo detecté: lo noté probando MinIO.

### BUG-27. Falso negativo en la prueba de restauración

Síntoma: `opportunities` esperado 281, restaurado 283: "FALLO", aunque el respaldo estaba bien (MinIO OK).

Causa: el script contaba las filas y DESPUÉS sacaba el respaldo; entre los dos momentos el radar de n8n guardó 2 vacantes. Se comparaban dos fotos tomadas en momentos distintos (condición de carrera en el diseño de la prueba).

Cómo lo corregí: se cuenta antes Y después del respaldo; es válido si lo restaurado queda entre los dos números (archivo .conteo: "tabla antes despues"). Compatible con respaldos viejos (un solo número).

Lo que aprendí: con BUG-17 (falso positivo) son las dos caras: una prueba debe fallar cuando hay error real y NO fallar cuando el sistema está bien.

Cómo lo detecté: primera prueba de restauración con el radar multiusuario corriendo.

### BUG-28. Vacantes de correo que no tienen nada que ver

Síntoma: a Telegram llegaban avisos como "Analista de nómina" que no sirven y llenan el chat.

Causa: en la búsqueda por usuario (multiusuario parte 4) las palabras clave solo se aplicaron a Get on Board; las vacantes de LinkedIn/Indeed/Workana por correo se guardaban sin revisar el título.

Cómo lo corregí: `busqueda.filtrar_por_palabras()` en POST /radar/email con las palabras del dueño del buzón (sin palabras configuradas no filtra). Se cuentan en "skipped".

Prueba de regresión: 2 tests en `test_busqueda.py` (114 en total).

Cómo lo detecté: lo noté usando el bot.

### BUG-29. La IA puntuaba vacantes viejas que no sirven

Síntoma: al probar la telemetría, radar-puntaje mandó a la IA "Recepcionista hotel", "Ejecutivo(a) de Negocios", etc.

Causa: (1) BUG-28 filtró solo las vacantes nuevas; las que ya estaban en la fila de puntaje (111, del 30-sep y 1-oct, confirmado con una consulta SQL GROUP BY por día) seguían ahí. (2) /opportunities/pending-score no excluía las de estado "descartada": gastaba IA en vacantes que la persona ya había descartado.

Cómo lo corregí: pending-score ahora excluye `status = 'descartada'`. Limpieza única con `python -m app.limpiar_pendientes` (vista previa) y `--aplicar`: les pasa el mismo filtro de palabras de cada usuario y marca como descartadas las que no coinciden (no borra nada).

Prueba de regresión: el filtro ya tiene tests (BUG-28); se verificó con la vista previa antes de aplicar y con la consulta SQL después.

Cómo lo detecté: revisando la salida del nodo "Pedir vacantes sin puntaje" durante la prueba de telemetría.

Lo que aprendí: cuando se agrega un filtro, revisar también los datos que ya estaban guardados, no solo los nuevos.

Hallazgo extra, un falso negativo: la vista previa mostró que mis palabras clave descartaban vacantes de QA ("Test Analyst", "Junior SDET", "Test Automation", "Automatizador") y de servicio/soporte. Ajusté las palabras (test, sdet, automatiza, automation, soporte, mesa de ayuda, servicio al cliente, ia, ai, artificial) y el máximo de palabras subió de 12 a 15 (`MAX_PALABRAS`). Aprendí que el prefijo "tester" no atrapa "test"; conviene usar la raíz más corta.

### BUG-30. Telegram rechaza mensajes con "_" (Markdown)

Síntoma: al usar `/completar_perfil` llegó la alerta "Bad request" en "Avisar: perfil completo". El detalle de Telegram: `can't parse entities: Can't find end of the entity starting at byte offset 136`.

Causa: el nodo Telegram de n8n manda los mensajes con `parse_mode` Markdown (legacy) aunque no se configure. Un `_` suelto (el nuevo texto decía `/subir_cv`) abre una cursiva que nunca cierra y Telegram rechaza todo el mensaje. Era un bug latente: cualquier vacante con `_`, `*`, `` ` `` o `[` en el título (ej. "Analista de Transformación Operacional, Bogotá_9740") rompía /nuevas, /mejores, /buscar o el resumen; y la nueva /ayuda tiene `/subir_cv` y `/completar_perfil`.

Primera hipótesis, que descarté: el Chat ID con `.item` tras un Postgres sin filas (como BUG-20). Se cambió a `.first()` y siguió fallando: el error real estaba en el detalle de la ejecución, no en el resumen de la alerta.

Cómo lo corregí: `comandos.escapar_md()` antepone `\` a `_`, `*`, `` ` `` y `[`. Se aplica en UN solo lugar a todo campo `telegram_text` de cualquier respuesta (`_RutaTelegram`, una ruta de FastAPI que procesa la respuesta) y al texto de /profiles/{id}/summary. En n8n, los textos fijos con `_` se escriben `\_`.

Prueba de regresión: 3 tests en `test_comandos.py` (escapado, solo el campo telegram_text y no el correo, la ayuda sin `_` sueltos).

Cómo lo detecté: probando los comandos nuevos con el bot real.

Lo que aprendí: leer el detalle completo del error (`errorDescription`) antes de cambiar cosas; y los datos externos (títulos de vacantes) pueden traer caracteres especiales.

### BUG-31. Lo que impedía reconstruir el sistema desde el repo

Estos problemas aparecieron cuando hice la prueba de reconstrucción (el punto de la definición de terminado "reconstrucción desde repositorio y .env.example") en una carpeta nueva, sin tocar la instalación real.

- `test-conexion-postgres.json` tenía el mismo id que `telegram-invitacion`, así que al importar en un n8n vacío uno pisaba al otro. Lo quité del repo, porque era una prueba vieja.
- Las alertas de errores tenían escrito fijo el chat de la admin, y en otra instalación le habrían avisado a otra persona. Ahora `importar-n8n.py` lo reemplaza por `ADMIN_TELEGRAM_USER_ID`.
- `start-local.sh` tenía dos comandos sin `--env-file .env`. En una segunda copia del proyecto habrían reiniciado el túnel de la instalación equivocada. Ya lo agregué.
- Las credenciales de n8n no viajan en el repo, porque son secretos, y había que crearlas a mano en 8 flujos. Ahora `scripts/importar-n8n.py` las crea a partir del `.env` con los mismos ids que usan los flujos.
- El `.env.example` estaba desactualizado: todavía hablaba de NVIDIA NIM, tenía variables que no se usaban y no tenía las de Groq y Gemini. Lo reescribí con explicaciones.
- Al correr la prueba, `import:credentials` falló con `EACCES`, porque `docker cp` conserva los permisos del Mac (solo el usuario del Mac puede leer) y n8n corre como `node`. Lo arreglé con `chown -R node:node` después de copiar. El archivo con secretos sí se borró aunque la importación había fallado.

Prueba de regresión: repetí la reconstrucción completa y funcionó (ver `docs/runbooks/reconstruccion.md`).

Efecto secundario: como el n8n de prueba usa la misma dirección (localhost:5678), se perdió la sesión del n8n original y no recordaba la contraseña. Lo resolví con `n8n user-management:reset`, que conserva los flujos y las credenciales, después de sacar un respaldo. Lo dejé anotado en el runbook.

Lo que aprendí: que algo funcione en mi Mac no prueba que el proyecto se pueda instalar. Hay que probarlo en un entorno limpio, igual que cualquier caso de prueba.

### BUG-32. /preferencias descarta en silencio las palabras después de la 15

Cómo lo detecté: prueba manual en Telegram (caso E2E-21 del plan de pruebas).

Pasos para reproducir:
1. Escribir `/preferencias` con 16 palabras separadas por coma (las 15 actuales y `tester`).
2. Leer la respuesta del bot.

Resultado esperado: el bot guarda las 16 palabras, o avisa que el máximo es 15 y cuál quedó por fuera.

Resultado real: responde "Listo, actualicé tu búsqueda" con solo 15 palabras; `tester` desaparece sin ningún aviso.

Evidencia: `docs/testing/evidencias/E2E-21_preferencias_3.jpg`.

Causa: `leer_palabras()` en `services/profile-api/app/busqueda.py` recorta la lista a `MAX_PALABRAS = 15` (`palabras[:MAX_PALABRAS]`) y el mensaje no informa el recorte.

Severidad baja y prioridad media. En este caso no afectó el radar ("test" ya atrapa "tester" por prefijo), pero cualquier usuario puede perder una palabra importante sin saberlo, y el "Listo" le hace creer que quedó guardada.

Corrección propuesta: si llegan más de 15 palabras, responder con un aviso ("El máximo es 15; no guardé: tester") o no guardar y pedir que quite algunas. Agregar un test unitario con 16 palabras.

Estado: abierto.

### BUG-33. /vacante no muestra el número de la vacante

Cómo lo detecté: prueba manual en Telegram (casos E2E-14 y E2E-15 del plan de pruebas).

Pasos para reproducir:
1. Escribir `/vacante <link de una vacante nueva>`.
2. Escribir `/vacante https://www.linkedin.com/jobs/view/4258064259/` (la #303, ya guardada).

Resultado esperado: "Guardé la vacante #N…" y "Esa vacante ya la tenías guardada (#303)", para poder usar `/detalle`, `/guardar` o `/descartar` de inmediato.

Resultado real: las dos respuestas muestran fuente, título y link, pero ningún número. Para gestionarla hay que buscarla en `/nuevas`.

Evidencia: `docs/testing/evidencias/E2E-14_vacante_nueva.jpg`, `E2E-15_duplicado.jpg`.

Causa: `radar_url()` en `services/profile-api/app/main.py` arma el texto con `oportunidad.title` y `oportunidad.url`, sin `numero` (el resto de comandos sí lo usan: `#{v['numero']}` en `comandos.py`).

Severidad baja y prioridad media. La vacante se guarda y la deduplicación funciona; el problema es de usabilidad y de verificación (no se puede comprobar "mismo número" en el duplicado).

Corrección propuesta: incluir `#{numero}` en los dos mensajes y agregar un test que lo verifique.

Estado: abierto.

### BUG-34. Con el radar en pausa siguen llegando avisos por correo

Cómo lo detecté: prueba manual en Telegram (caso E2E-23 del plan de pruebas).

Pasos para reproducir:
1. Escribir `/pausar`. El bot responde: "pausé tu radar: no te llegarán vacantes nuevas ni el resumen de la mañana".
2. Esperar a que llegue una alerta de LinkedIn o Indeed a la etiqueta Radar de Gmail.

Resultado esperado: la vacante se guarda, pero no llega ningún aviso por Telegram mientras el radar está en pausa.

Resultado real: a las 9:47 p. m. y 10:28 p. m. (unas 4 horas después de pausar) llegaron avisos de Indeed y LinkedIn, y siguieron llegando en la mañana.

Evidencia: `docs/testing/evidencias/E2E-23_pausado_llegan_avisos.jpg`.

Causa: `radar_email()` en `services/profile-api/app/main.py` asigna el correo a la admin (`_admin(db)`) y nunca revisa `estado`. Los otros caminos sí lo respetan: Get on Board y el puntaje usan `_usuarios_activos()` (`estado == "activo"`). El flujo `radar-correo` avisa siempre que `created > 0`.

Severidad media y prioridad alta. El bot le promete algo al usuario ("no te llegarán vacantes nuevas") y no lo cumple. No se pierde información, pero rompe la confianza en el comando.

Corrección propuesta: si el dueño del buzón está pausado, guardar las vacantes pero responder sin `new_items` para avisar (o con una marca `pausado: true` que el IF de n8n respete). Agregar un test: usuario pausado y correo con vacantes nuevas: se guardan y no se avisa.

Lo que aprendí: cuando una regla (pausa) se aplica en varios caminos, hay que probarla en todos. El caso E2E-23 del plan solo mencionaba el resumen y los avisos en general; la fuente correo era el camino distinto.

Estado: abierto.

### BUG-35. El filtro de ubicación deja pasar México escrito como "MEX" o "CMX"

Cómo lo detecté: revisando los avisos de Telegram durante el caso E2E-23; contradice el caso E2E-17 (filtro de ubicación), que había pasado con la muestra del 8 oct a las 14:33.

Pasos para reproducir:
1. Que llegue una alerta de LinkedIn con vacantes en México cuya ubicación venga abreviada.
2. O, directo en código: `ubicacion_sirve("Polanco, CMX")` y `ubicacion_sirve("Huixquilucán, MEX")`.

Resultado esperado: `False`: la vacante no se guarda ni se avisa (regla de BUG-18: nada de otros países).

Resultado real: `True`: el 8 oct a las 5:24 p. m. llegó un aviso con "Tester Automatizador con IA (axity - Huixquilucán, MEX)" y "OTA Automotive test analyst (Cognizant - Polanco, CMX)". En cambio `"Ciudad de México, México"` sí da `False`.

Evidencia: `docs/testing/evidencias/E2E-17_avisos_mexico.jpg`.

Causa: `ubicacion_sirve()` en `services/profile-api/app/parsers.py` usa una lista negra (`_UBICACION_OTRO_PAIS`) con nombres completos (`méxico`, `cdmx`, `guadalajara`…). Las abreviaturas `MEX` y `CMX`, y ciudades como Huixquilucán o Polanco, no están en la lista, y lo que no está en la lista pasa.

Severidad media y prioridad media. Llegan vacantes que la usuaria descartó explícitamente (solo remoto o Medellín). Es una regresión de BUG-18 con otra forma de escribir el país.

Corrección propuesta: a corto plazo, agregar `mex`, `cmx` y códigos de país de 3 letras (ARG, CHL, PER, ECU, BRA, USA…) con `\b`, más tests con estos dos casos reales. A mediano plazo, invertir la lógica a lista blanca: aceptar solo si dice Colombia/ciudad colombiana/remoto LATAM; si no se reconoce, no avisar (o marcar "ubicación dudosa").

Lo que aprendí: un caso que pasó con una muestra pequeña (10 avisos) puede fallar con el siguiente dato real. Las listas negras siempre dejan huecos.

Estado: abierto.

### BUG-36. Tras reiniciar, el bot no recibe mensajes y `start-local.sh` dice "Listo" igual

Cómo lo detecté: durante el caso E2E-23 (10 oct). El bot no respondía a `/reanudar`, `hola` ni nada, pero los avisos de vacantes y el resumen sí salían.

Pasos para reproducir:
1. Que el Mac se duerma o se reinicie Docker (el túnel de Cloudflare cambia de URL).
2. Correr `bash scripts/start-local.sh`: termina con "Listo. El bot debería estar respondiendo".
3. Escribirle al bot.

Resultado esperado: el bot responde, o el script avisa que algo falló.

Resultado real: el bot no responde. `getWebhookInfo` de Telegram mostraba `"url": ""`: no había ningún webhook registrado. Los mensajes enviados en ese tiempo se perdieron (`pending_update_count: 0`).

Diagnóstico: lo que sale (avisos, resumen) funcionaba porque lo disparan relojes internos; lo que entra (comandos) depende de que Telegram conozca la URL pública. `.env` sí tenía la URL nueva; lo que falló fue el registro del webhook al arrancar n8n (probablemente el túnel recién creado aún no respondía).

Lo que hice para arreglarlo: desactivar y activar el flujo `telegram-invitacion` en n8n: n8n vuelve a registrar el webhook: `getWebhookInfo` muestra la URL nueva y el bot responde.

Severidad media y prioridad alta. El sistema queda "medio caído" sin ninguna alerta: los flujos no fallan, simplemente no les llega nada.

Cómo lo corregí: cambié `start-local.sh` para que, antes de reiniciar n8n, espere a que la URL nueva del túnel responda desde internet (`/healthz` con 200). Después de reiniciar n8n le pregunta a Telegram con `getWebhookInfo` si ya tiene la URL nueva. Si no la tiene, reinicia n8n una vez más; si sigue sin tenerla, ya no dice "Listo": muestra un aviso de que el bot no va a recibir mensajes, lo que respondió Telegram y cómo arreglarlo a mano.

Re-test (10 oct): borré el webhook a propósito con `deleteWebhook` (quedó `url` vacía, igual que en el fallo), corrí el script y terminó con "Telegram ya tiene la URL nueva". El bot respondió a `hola`. Queda pendiente para más adelante un chequeo periódico que avise si el webhook se vacía con el sistema ya andando.

Lo que aprendí: un mensaje de "Listo" que no verifica nada es un falso positivo. Ya estaba en riesgos ("el túnel cambia de URL"), pero sin forma de detectarlo.

Estado: corregido y probado el 10 oct.

## Riesgos y limitaciones que siguen abiertos

- Todo depende de que el Mac esté prendido. Si está dormido a la hora del resumen (11 a. m.), el resumen no sale a tiempo y n8n no lo recupera después (BUG-21). Mientras tanto dejo el Mac conectado, con Docker abierto y sin suspensión automática. La solución de fondo es pasar a un servidor.
- El túnel de Cloudflare cambia de URL cada vez que se reinicia. Si Telegram se queda con una URL vieja o vacía, el bot no recibe comandos, aunque los avisos que salen sí sigan funcionando. Desde el BUG-36, `start-local.sh` lo revisa al arrancar, pero si pasa con el sistema ya andando nadie avisa.
- Los correos de LinkedIn no traen descripción ni fecha de publicación, así que el puntaje de esas vacantes es menos preciso.
- El campo `remote_local` de Get on Board puede estar limitado a un país, y hoy no leo `location_tenants`.
- Hay un chat_id fijo (8553351572) en varios flujos. Hay que revisarlo para el paso a varios usuarios.
- Si se cae n8n entero o Telegram, la alerta tampoco llega, porque `alertas-errores` usa el mismo n8n y el mismo bot. Sirve para detectar fallas de un flujo, no caídas de todo el sistema.
