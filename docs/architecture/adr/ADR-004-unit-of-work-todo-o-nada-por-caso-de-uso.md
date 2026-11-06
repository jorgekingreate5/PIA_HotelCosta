# ADR-004: Unit of Work: todo o nada por caso de uso

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** RNF-01

## Contexto
Casos como el check-out cambian la cuenta, la reservación y la habitación; si una parte falla no debe quedar nada a medias.

## Decisión
Cada método de servicio abre una Unit of Work, carga los agregados, ejecuta la regla y llama a guardar_cambios() al final. Si ocurre un rechazo o un error, se hace rollback.

## Alternativas consideradas
Un commit por repositorio (riesgo de estados parciales).

## Consecuencias
Consistencia garantizada y probada (por ejemplo, el pago se revierte si queda saldo). Una Unit of Work por petición.
