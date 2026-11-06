# ADR-008: Control de acceso por rol con el encabezado X-Rol

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N16

## Contexto
Cada área solo debe ejecutar sus operaciones (por ejemplo, solo Limpieza libera habitaciones).

## Decisión
Una tabla de permisos por acción en la capa de aplicación y un encabezado X-Rol en la API.

## Alternativas consideradas
JWT con usuarios y contraseñas (correcto para producción, pero fuera del alcance de esta iteración).

## Consecuencias
Es simple y probado, pero no es autenticación real: cualquiera puede enviar el rol. Se documenta como limitación y se deja JWT como siguiente paso.
