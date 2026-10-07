# ADR 006 · Resumen por correo: Mailpit en local, SMTP real en producción

**Fecha:** 2026-10-06 · **Estado:** aceptada · **Decidió:** Andrea

## Contexto
La definición de terminado pide "resumen por Telegram y correo". El correo
de cada usuario sale de su CV (`contacto.email`).

## Decisión
En local, el nodo "Enviar resumen por correo" usa la credencial SMTP
**Mailpit** (host `mailpit`, puerto 1025, sin SSL). Mailpit atrapa los
correos y los muestra en http://localhost:8025 sin enviarlos de verdad.

## Por qué
- Permite probar el envío completo sin riesgo de mandar correos reales a
  usuarios de prueba ni que Gmail marque la cuenta como spam.
- No hace falta guardar una contraseña de correo real en el entorno local.

## Consecuencias
- **Paso a producción (pendiente, va en el README):** cambiar la credencial
  del nodo a un SMTP real (ej. Gmail con contraseña de aplicación, o un
  servicio de envío) y revisar remitente, SPF/DKIM y límites diarios.
- El resumen por correo usa la misma idempotencia que el de Telegram: uno
  por usuario y día.

## Cuándo revisarla
- Al desplegar en un servidor o al tener usuarios reales que esperen el
  correo.
