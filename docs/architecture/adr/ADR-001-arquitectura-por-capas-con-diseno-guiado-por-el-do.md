# ADR-001: Arquitectura por capas con diseño guiado por el dominio (DDD)

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N2, N3, N7

## Contexto
El negocio tiene reglas que se repiten en varios casos de uso y cambian el estado de reservaciones, habitaciones y cuentas (por ejemplo, que una habitación solo se entregue si está disponible).

## Decisión
Se organiza el código en cuatro capas: dominio, aplicación, infraestructura y API. El dominio contiene agregados (Reservacion, Habitacion, CategoriaHabitacion, CuentaEstancia), value objects, specifications, máquina de estados y eventos, y no importa nada de las otras capas.

## Alternativas consideradas
Transaction Script (reglas copiadas en cada caso de uso) y Table Module (las reglas que cruzan entidades no tienen lugar claro).

## Consecuencias
Las reglas viven en un solo lugar y se prueban sin base de datos ni HTTP. A cambio hay más archivos y una curva de aprendizaje mayor.
