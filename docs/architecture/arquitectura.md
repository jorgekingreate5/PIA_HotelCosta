# Arquitectura del sistema

## 1. Vista general
Arquitectura por capas con diseño guiado por el dominio. La dependencia apunta siempre hacia el dominio (ver `diagramas/arquitectura_capas.png`).

| Capa | Carpeta | Responsabilidad | Depende de |
|---|---|---|---|
| API | `src/api` | Rutas HTTP, validación de entrada, traducción de errores a códigos HTTP. | Aplicación |
| Aplicación | `src/application` | Un método por caso de uso: permisos, Unit of Work, publicación de eventos. Sin reglas de negocio. | Dominio |
| Dominio | `src/domain` | Agregados, entidades, value objects, specifications, máquina de estados, eventos y contratos de repositorio. | Nada |
| Infraestructura | `src/infrastructure` | Repositorios SQL y en memoria, Unit of Work, pasarela simulada, configuración, carga de datos. | Aplicación y dominio |

`src/infrastructure/composicion.py` es el único lugar donde se arman las piezas.

## 2. Bloques de DDD
| Bloque | Elementos |
|---|---|
| Aggregate roots | Reservacion, Habitacion, CategoriaHabitacion, CuentaEstancia |
| Entidades | CambioDeHabitacion (dentro de Reservacion), Cargo (dentro de CuentaEstancia), Huesped |
| Value objects | LineaReservacion, Garantia, EstadoReservacion, EstadoHabitacion, Rol |
| Specifications | HuespedActivo, HuespedPreferente, DetalleNoVacio, ReservacionAutorizada, PromocionActiva, TotalMinimo, CategoriasHabilitadas, CupoSuficiente, combinadas en puede_procesarse, puede_confirmarse, beneficio_preferente y requiere_revision |
| Máquinas de estados | Reservación (6 estados) y habitación (4 estados) |
| Domain events | 13 eventos (ver mapa de dominio) |

## 3. Reglas que protege el dominio
| ID | Regla | Dónde |
|---|---|---|
| R1 | Una habitación solo se entrega si está disponible. | Habitacion.entregar |
| R2 | No se confirma más cupo del que existe. | Reservacion.confirmar, CupoSuficiente |
| R3 | Cada operación depende del estado de la reservación. | MAQUINA_RESERVACION |
| R4 | El check-in exige identidad verificada y garantía aprobada. | Reservacion.registrar_check_in, ServicioDeRecepcion |
| R5 | Solo se agregan cargos a una cuenta abierta y con monto mayor a cero. | CuentaEstancia.registrar_cargo |
| R6 | No se cierra la cuenta con saldo pendiente. | CuentaEstancia.cerrar |
| R7 | Todo cambio de habitación deja registro. | Reservacion.cambiar_habitacion |
| R8 | La habitación liberada queda pendiente de limpieza y solo Limpieza la pasa a disponible. | MAQUINA_HABITACION, permisos |
| R9 | Una habitación fuera de servicio no acepta reservas ni entregas. | MAQUINA_HABITACION, Habitacion.entregar |

## 4. Patrones aplicados
| Patrón | Dónde | Para qué |
|---|---|---|
| Repository | `domain/repositorios.py`, `infrastructure` | Que el dominio no conozca la base de datos. |
| Unit of Work | `application/puertos.py`, `en_memoria.py`, `sql.py` | Guardar todo o nada. |
| Service Layer | `application/servicios.py` | Un método por caso de uso. |
| CQRS básico | `ServicioDeConsultas` frente a los demás servicios | Separar lo que lee de lo que modifica. |
| Specification | `domain/especificaciones.py` | Reglas combinables con Y, O y No. |
| State | `domain/maquina_estados.py` | Transiciones válidas explícitas. |
| Domain Events | `domain/eventos.py` | Avisar hechos del negocio sin acoplar. |
| Ports and Adapters | `PasarelaDeGarantia`, `PublicadorDeEventos` | Sustituir servicios externos por simulados. |
| Factory | `Reservacion.solicitar`, `CuentaEstancia.abrir` | Crear objetos válidos y con su evento. |

## 5. Principios SOLID
| Principio | Cómo se aplica |
|---|---|
| S | Un servicio por actor y un método por caso de uso; las reglas viven en el dominio. |
| O | Un caso de uso nuevo es un método y un comando nuevos; una regla nueva es una especificación nueva. |
| L | Cualquier Unit of Work o repositorio (memoria o SQL) sustituye a otro sin tocar los servicios. |
| I | Repositorios pequeños por agregado y puertos con un solo método. |
| D | Los servicios dependen de contratos (UnidadDeTrabajo, PublicadorDeEventos, PasarelaDeGarantia). |

## 6. Configuración y entornos
| Variable | Uso | Valor por omisión |
|---|---|---|
| DATABASE_URL | Base de datos (`memory` usa memoria) | memory |
| CARGAR_DATOS_DEMO | Carga los datos del PIA al arrancar | 0 |
| BENEFICIO_UMBRAL_MXN | Umbral del beneficio preferente | 1500 |
| RUTA_DATOS | Carpeta de los CSV | datos |
| HABITACIONES_POR_CATEGORIA | Habitaciones físicas por categoría (20 × 6 = 120) | 6 |

## 7. Alineación con el paquete del PIA
El paquete propone el flujo SOLICITADA → CONFIRMADA → CHECK_IN → CHECK_OUT y CANCELADA. Se respetó y se agregó NO_SHOW, que viene del caso. El catálogo del paquete se modela como categorías con cupo; las habitaciones físicas (6 por categoría, 120 en total) se generan al cargar los datos porque el paquete no las trae. Las diferencias de interpretación están en el BRD, sección 9.

## 8. Limitaciones conocidas
- La autenticación es un encabezado de rol, no usuarios reales (ADR-008).
- Los eventos se guardan en memoria y se pierden al reiniciar (ADR-007).
- Las tablas se crean al arrancar; no hay migraciones.
- La pasarela de garantías es simulada.
- Las políticas de cancelación, penalización, salida anticipada y extensión no están definidas por el negocio.
