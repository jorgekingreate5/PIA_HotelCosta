# ADR-007: Eventos de dominio publicados después de guardar

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N7

## Contexto
Otras áreas necesitan enterarse de hechos como HabitacionDisponible sin acoplarse al dominio.

## Decisión
Los agregados acumulan eventos y el servicio los publica en un PublicadorDeEventos solo después de guardar los cambios. Hoy el publicador guarda los eventos en memoria (GET /eventos).

## Alternativas consideradas
Notificar desde dentro del dominio (acopla el dominio) o publicar antes de guardar (puede avisar de algo que no se guardó).

## Consecuencias
Se evita avisar de operaciones rechazadas. Limitación: los eventos se pierden al reiniciar; el siguiente paso es una tabla outbox.
