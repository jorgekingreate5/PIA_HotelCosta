# ADR-010: Los datos del paquete del PIA solo se usan para pruebas

- **Estado:** Aceptado
- **Fecha:** 2026-11-01
- **Relacionado con:** N15

## Contexto
El paquete trae huéspedes, catálogo, operaciones, 120 casos y 20 transiciones ficticios, con reglas ilustrativas que no sustituyen los requerimientos del equipo.

## Decisión
Los datos se cargan en la base de demostración y se usan para pruebas. Las 120 verificaciones y las 20 transiciones se ejecutan sobre el sistema y se comparan contra un cálculo independiente hecho directamente sobre los CSV. Las diferencias de interpretación (cupo, cantidad como habitaciones-noche, umbral de 1,500 MXN) se documentan en el BRD como supuestos.

## Alternativas consideradas
Adoptar las reglas del paquete como requisitos del negocio.

## Consecuencias
Se prueba con volumen realista sin inventar políticas del hotel. Los supuestos quedan visibles para validarlos.
