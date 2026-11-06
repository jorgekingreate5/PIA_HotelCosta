# Historias de usuario y criterios de aceptación

Formato: Como [rol], quiero [capacidad], para [beneficio]. Criterios en Gherkin (Given/When/Then). Las historias US-01 a US-19 están implementadas y probadas; US-20 a US-22 quedan en el backlog.

## US-01 · Consultar categorías y cupo

**Como** Reservaciones, **quiero** consultar las categorías de habitación con su tarifa y cupo, **para** ofrecer solo lo que realmente se puede reservar.

Necesidad: N1 · Requisito: RF-01

```gherkin
Feature: Consultar categorías y cupo

  Scenario: Consulta del catálogo
    Given que el hotel tiene categorías cargadas
    When Reservaciones consulta las categorías
    Then recibe cada categoría con tarifa, cupo disponible y si está habilitada

  Scenario: Rol no reconocido
    Given una petición sin rol o con un rol desconocido
    When consulta las categorías
    Then el sistema responde 403
```

## US-02 · Solicitar una reservación

**Como** Reservaciones, **quiero** registrar la solicitud de reservación de un huésped con sus líneas, **para** dejar constancia de lo que pidió y a qué tarifa.

Necesidad: N2 · Requisito: RF-02

```gherkin
Feature: Solicitar una reservación

  Scenario: Solicitud válida
    Given un huésped y una categoría existentes
    When Reservaciones registra una solicitud con cantidad 2
    Then la reservación queda SOLICITADA con la tarifa del catálogo y el total calculado

  Scenario: Huésped o categoría inexistente
    Given un huésped o una categoría que no existen
    When se registra la solicitud
    Then el sistema responde 404 y no guarda nada

  Scenario: Cantidad inválida
    Given una línea con cantidad 0
    When se envía la solicitud
    Then el sistema responde 422
```

## US-03 · Autorizar una reservación

**Como** Reservaciones, **quiero** autorizar una reservación solicitada, **para** poder confirmarla después.

Necesidad: N2 · Requisito: RF-03

```gherkin
Feature: Autorizar una reservación

  Scenario: Autorización
    Given una reservación SOLICITADA sin autorizar
    When Reservaciones la autoriza
    Then queda autorizada

  Scenario: Ya confirmada
    Given una reservación CONFIRMADA
    When se intenta autorizar
    Then el sistema responde 409
```

## US-04 · Confirmar una reservación

**Como** Reservaciones, **quiero** confirmar una reservación que cumple las condiciones, **para** comprometer la habitación sin vender más cupo del que existe.

Necesidad: N2 · Requisito: RF-04

```gherkin
Feature: Confirmar una reservación

  Scenario: Confirmación correcta
    Given una reservación autorizada de un huésped activo con cupo suficiente
    When Reservaciones la confirma
    Then queda CONFIRMADA y el cupo baja en la cantidad reservada

  Scenario: No cumple las condiciones
    Given una reservación sin autorización, sin detalle o de un huésped inactivo
    When se intenta confirmar
    Then el sistema responde 422 con el motivo y no cambia nada

  Scenario: Sin cupo
    Given una categoría con 1 de cupo y una reservación por 2
    When se intenta confirmar
    Then el sistema responde 409 y el cupo no cambia

  Scenario: Confirmar dos veces
    Given una reservación ya CONFIRMADA
    When se intenta confirmar de nuevo
    Then el sistema responde 409 por transición inválida
```

## US-05 · Cancelar una reservación

**Como** Reservaciones, **quiero** cancelar una reservación solicitada o confirmada, **para** liberar el cupo para otros huéspedes.

Necesidad: N9 · Requisito: RF-05

```gherkin
Feature: Cancelar una reservación

  Scenario: Cancelar una confirmada
    Given una reservación CONFIRMADA
    When Reservaciones la cancela
    Then queda CANCELADA y el cupo se devuelve

  Scenario: Cancelar en estancia
    Given una reservación en CHECK_IN
    When se intenta cancelar
    Then el sistema responde 409

  # [CAMBIO vs. entrega anterior] Escenarios agregados: política de cancelación de 48 h (BRD, N4 de la Act. 5)
  Scenario: Cancelación con 48 horas o más de anticipación
    Given una reservación CONFIRMADA con llegada en 48 horas o más
    When Reservaciones la cancela
    Then no se cobra penalidad

  Scenario: Cancelación tardía
    Given una reservación CONFIRMADA con llegada en menos de 48 horas
    When Reservaciones la cancela sin autorización especial
    Then se cobra una noche (la tarifa de la primera línea) como penalidad

  Scenario: Excepción del Jefe de Reservaciones o Administración
    Given una cancelación tardía con autorización del Jefe de Reservaciones o Administración
    When se cancela
    Then la penalidad es cero
```

## US-06 · Registrar un no-show

**Como** Recepción, **quiero** marcar como no-show una reservación a la que el huésped no llegó, **para** recuperar el cupo.

Necesidad: N9 · Requisito: RF-06

```gherkin
Feature: Registrar un no-show

  Scenario: No-show
    Given una reservación CONFIRMADA
    When Recepción registra el no-show
    Then queda NO_SHOW y el cupo se devuelve

  Scenario: No aplica a solicitadas
    Given una reservación SOLICITADA
    When se registra un no-show
    Then el sistema responde 409
```

## US-07 · Hacer el check-in

**Como** Recepción, **quiero** hacer el check-in verificando identidad y garantía y entregando una habitación, **para** recibir al huésped sin errores.

Necesidad: N3 · Requisito: RF-07

```gherkin
Feature: Hacer el check-in

  Scenario: Check-in correcto
    Given una reservación CONFIRMADA y una habitación disponible de la categoría reservada
    When Recepción hace el check-in con identidad verificada y garantía aprobada
    Then la reservación pasa a CHECK_IN, la habitación queda OCUPADA y se abre la cuenta

  Scenario: Falta identidad o garantía
    Given una reservación CONFIRMADA
    When se intenta el check-in sin identidad verificada o sin garantía
    Then el sistema responde 422 y la habitación sigue disponible

  Scenario: Garantía rechazada
    Given una garantía que el servicio externo rechaza
    When se intenta el check-in
    Then el sistema responde 422 y no ocupa la habitación

  Scenario: El servicio externo no responde
    Given que el servicio de garantías no responde
    When se intenta el check-in
    Then el sistema responde 503 y no cambia nada

  Scenario: Habitación no disponible
    Given una habitación pendiente de limpieza
    When se intenta el check-in en ella
    Then el sistema responde 409
```

## US-08 · Registrar cargos

**Como** Recepción, **quiero** registrar los consumos del huésped en su cuenta, **para** que los cargos queden en un solo lugar.

Necesidad: N4 · Requisito: RF-08

```gherkin
Feature: Registrar cargos

  Scenario: Cargo válido
    Given un huésped en estancia con cuenta abierta
    When Recepción registra un cargo de 250 por Restaurante
    Then el total de la cuenta aumenta 250 y queda el empleado que lo capturó

  Scenario: Cuenta cerrada
    Given una cuenta ya cerrada por el check-out
    When se intenta registrar un cargo
    Then el sistema responde 409

  Scenario: Monto inválido
    Given un cargo con monto 0
    When se envía
    Then el sistema responde 422

  # [CAMBIO vs. entrega anterior] Escenarios agregados: tope de crédito de $3,000 MXN (BRD, N10)
  Scenario: Consumo que supera el tope de crédito
    Given consumos acumulados de 3,000 MXN y ningún pago parcial
    When Recepción intenta registrar otro cargo
    Then el sistema responde 409 y el cargo no se guarda

  Scenario: Pago parcial o autorización de Administración
    Given un consumo que superaría el tope
    When el huésped hizo un pago parcial que libera crédito, o Administración autoriza el excedente
    Then el cargo se registra
```

## US-09 · Cambiar de habitación

**Como** Recepción, **quiero** cambiar al huésped de habitación dejando registro, **para** poder rastrear cada cambio.

Necesidad: N8 · Requisito: RF-09

```gherkin
Feature: Cambiar de habitación

  Scenario: Cambio correcto
    Given un huésped en estancia y otra habitación disponible
    When Recepción registra el cambio con motivo y responsable
    Then la nueva queda OCUPADA, la anterior pasa a pendiente de limpieza y el cambio queda en el historial

  Scenario: Habitación destino no disponible
    Given una habitación destino fuera de servicio
    When se intenta el cambio
    Then el sistema responde 409 y el huésped sigue en su habitación
```

## US-10 · Hacer el check-out

**Como** Recepción, **quiero** revisar y liquidar los cargos al salir el huésped, **para** cerrar la estancia sin saldos pendientes.

Necesidad: N5, N6 · Requisito: RF-10

```gherkin
Feature: Hacer el check-out

  Scenario: Check-out con saldo liquidado
    Given una cuenta con saldo y un pago por el total
    When Recepción hace el check-out
    Then la cuenta se cierra, la reservación queda en CHECK_OUT y la habitación pasa a pendiente de limpieza

  Scenario: Saldo pendiente
    Given un pago menor al saldo
    When se intenta el check-out
    Then el sistema responde 409 y revierte el pago: la cuenta sigue abierta y la habitación ocupada
```

## US-11 · Marcar la habitación como disponible

**Como** Limpieza, **quiero** marcar una habitación como lista al terminar la limpieza, **para** que Recepción lo sepa de inmediato.

Necesidad: N7 · Requisito: RF-11

```gherkin
Feature: Marcar la habitación como disponible

  Scenario: Limpieza termina
    Given una habitación pendiente de limpieza
    When Limpieza la marca como disponible
    Then queda DISPONIBLE y se publica el evento HabitacionDisponible

  Scenario: Otro rol
    Given una habitación pendiente de limpieza
    When Recepción intenta marcarla como disponible
    Then el sistema responde 403

  Scenario: Habitación que no estaba pendiente
    Given una habitación ocupada
    When Limpieza intenta marcarla disponible
    Then el sistema responde 409
```

## US-12 · Sacar de servicio y reactivar una habitación

**Como** Administración, **quiero** sacar de servicio una habitación y reactivarla, **para** no ofrecer habitaciones con problemas.

Necesidad: N12 · Requisito: RF-12

```gherkin
Feature: Sacar de servicio y reactivar una habitación

  Scenario: Fuera de servicio y reactivar
    Given una habitación disponible
    When Administración la saca de servicio y luego la reactiva
    Then pasa a FUERA_DE_SERVICIO y después a pendiente de limpieza

  Scenario: Habitación ocupada
    Given una habitación ocupada
    When se intenta sacar de servicio
    Then el sistema responde 409
```

## US-13 · Consultar una reservación

**Como** Reservaciones, **quiero** consultar el detalle de una reservación y si requiere revisión, **para** atender al huésped con la información correcta.

Necesidad: N2 · Requisito: RF-13

```gherkin
Feature: Consultar una reservación

  Scenario: Consulta
    Given una reservación existente
    When se consulta
    Then se muestra estado, líneas, total y requiere_revision

  Scenario: Inexistente
    Given un identificador que no existe
    When se consulta
    Then el sistema responde 404
```

## US-14 · Ver el estatus de las habitaciones

**Como** Recepción, **quiero** ver el estatus de todas las habitaciones, **para** asignar solo las que están listas.

Necesidad: N7 · Requisito: RF-14

```gherkin
Feature: Ver el estatus de las habitaciones

  Scenario: Estatus en tiempo real
    Given una habitación que Limpieza acaba de liberar
    When Recepción consulta las habitaciones
    Then la ve como DISPONIBLE sin esperar avisos manuales
```

## US-15 · Consultar la cuenta de la estancia

**Como** Recepción, **quiero** consultar total, pagado y saldo de una estancia, **para** cobrar correctamente en el check-out.

Necesidad: N4 · Requisito: RF-15

```gherkin
Feature: Consultar la cuenta de la estancia

  Scenario: Consulta de la cuenta
    Given una estancia con hospedaje y un cargo de restaurante
    When Recepción consulta la cuenta
    Then ve los cargos, el total, lo pagado y el saldo

  Scenario: Sin cuenta
    Given una reservación que aún no hace check-in
    When se consulta su cuenta
    Then el sistema responde 404
```

## US-16 · Ver el historial de cambios de habitación

**Como** Administración, **quiero** ver el historial de cambios de habitación de una reservación, **para** auditar y resolver aclaraciones.

Necesidad: N8 · Requisito: RF-16

```gherkin
Feature: Ver el historial de cambios de habitación

  Scenario: Historial
    Given una reservación con un cambio de habitación
    When se consulta su historial
    Then aparecen origen, destino, motivo, responsable y fecha
```

## US-17 · Ver el reporte de ocupación

**Como** Administración, **quiero** ver cuántas habitaciones hay por estatus y cuántas reservaciones por estado, **para** supervisar la operación del hotel.

Necesidad: N14 · Requisito: RF-17

```gherkin
Feature: Ver el reporte de ocupación

  Scenario: Reporte
    Given habitaciones en distintos estatus
    When Administración pide el reporte
    Then recibe el total, el conteo por estatus y el porcentaje de ocupación

  Scenario: Otro rol
    Given un usuario de Recepción
    When pide el reporte
    Then el sistema responde 403
```

## US-18 · Otorgar el beneficio preferente

**Como** Administración, **quiero** que el sistema reconozca a los huéspedes preferentes con un beneficio al confirmar, **para** premiar a los clientes que cumplen las condiciones.

Necesidad: N15 · Requisito: RF-18

```gherkin
Feature: Otorgar el beneficio preferente

  Scenario: Beneficio en el umbral
    Given un huésped preferente, un total igual al umbral y sin promoción activa
    When se confirma la reservación
    Then se otorga el beneficio y se publica BeneficioPreferenteOtorgado

  Scenario: Un centavo por debajo
    Given un total un centavo menor al umbral
    When se confirma la reservación
    Then no se otorga el beneficio

  Scenario: Promoción activa
    Given un huésped preferente con promoción activa
    When se confirma la reservación
    Then no se otorga el beneficio
```

## US-19 · Controlar el acceso por rol y auditar eventos

**Como** Administración, **quiero** que cada rol solo ejecute sus operaciones y poder ver los eventos del sistema, **para** proteger la operación y auditarla.

Necesidad: N16 · Requisito: RF-19

```gherkin
Feature: Controlar el acceso por rol y auditar eventos

  Scenario: Rol sin permiso
    Given un usuario de Limpieza
    When intenta hacer un check-out
    Then el sistema responde 403

  Scenario: Eventos
    Given operaciones recientes
    When Administración consulta los eventos
    Then ve los últimos eventos de dominio publicados
```

## Backlog

### US-20 · Salida anticipada

**Como** Recepción, **quiero** registrar la salida anticipada de un huésped, **para** ajustar los cargos según la política.

Necesidad: N10. Pendiente: Depende de la política de cobro de noches no utilizadas.

### US-21 · Extensión de estancia

**Como** Recepción, **quiero** extender la estancia si la habitación sigue disponible, **para** no perder la venta.

Necesidad: N11. Pendiente: Depende de la disponibilidad por fechas y de reubicar al huésped.

### US-22 · Llegada anticipada

**Como** Recepción, **quiero** recibir a un huésped antes de la hora estándar, **para** mejorar su experiencia sin comprometer la habitación.

Necesidad: N13. Pendiente: Depende de definir la hora estándar y la regla de cobro.
