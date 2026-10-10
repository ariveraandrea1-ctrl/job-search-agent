# ADR 006. Resumen por correo: Mailpit en local y SMTP real en producción

Fecha: 2026-10-06. Estado: aceptada. Decidió: Andrea.

## Contexto

La definición de terminado pide el resumen por Telegram y por correo. El correo de cada usuario se saca de su CV (`contacto.email`).

## Decisión

En local, el nodo "Enviar resumen por correo" usa la credencial SMTP de Mailpit (host `mailpit`, puerto 1025, sin SSL). Mailpit atrapa los correos y los muestra en http://localhost:8025, sin enviarlos de verdad.

## Por qué

Así puedo probar el envío completo sin mandar correos reales a usuarios de prueba y sin que Gmail marque la cuenta como spam.

Tampoco hace falta guardar la contraseña de un correo real en el entorno local.

## Consecuencias

Para pasar a producción (todavía pendiente) hay que cambiar la credencial del nodo por un SMTP real, por ejemplo Gmail con contraseña de aplicación o un servicio de envío, y revisar el remitente, SPF y DKIM, y los límites diarios.

El resumen por correo tiene la misma protección contra repetidos que el de Telegram: uno por usuario y por día.

## Cuándo revisarla

Al desplegar en un servidor, o cuando haya usuarios reales esperando el correo.
