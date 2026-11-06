# BRD – Hotel Costa Azul (Caso 09)

Documento de requerimientos de negocio del PIA de Componentes de Lógica de Negocios. Parte del análisis de la Unidad 2 y del diseño de la Unidad 3. Lo que el caso no define se marca como **supuesto** o **pregunta abierta**; no se inventaron políticas.

## 1. Contexto
Hotel Costa Azul tiene 120 habitaciones. Sus ingresos vienen del hospedaje y de servicios adicionales. Las tarifas dependen de la temporada, el tipo de habitación y las condiciones comerciales. El proceso central es: reservación → check-in → estancia → check-out → limpieza, con las excepciones de cancelación, no-show, salida anticipada, extensión de estancia, habitación fuera de servicio, cambio de habitación y llegada anticipada.

## 2. Problemas y oportunidades
| # | Problema observado | Oportunidad |
|---|---|---|
| P1 | Recepción no ve de inmediato qué habitaciones libera Limpieza. | Un solo estatus por habitación, actualizado por Limpieza y visible para todos. |
| P2 | Riesgo de inconsistencias entre la disponibilidad mostrada y la real. | Cupo por categoría que se descuenta al confirmar y se devuelve al cancelar. |
| P3 | Los cambios de habitación son difíciles de rastrear. | Historial de cada cambio (origen, destino, motivo, responsable, fecha). |
| P4 | Los cargos de la estancia están dispersos. | Una cuenta única por estancia, con el empleado que capturó cada cargo. |

## 3. Stakeholders
| Rol | Interés |
|---|---|
| Huésped | Reservar, hospedarse y pagar sin errores. |
| Reservaciones | Confirmar, autorizar y cancelar reservaciones con disponibilidad real. |
| Recepción | Check-in, cargos, cambios de habitación y check-out; ver el estatus de habitaciones. |
| Limpieza | Marcar habitaciones como listas. |
| Administración | Supervisar ocupación, sacar habitaciones de servicio y auditar. |

## 4. Alcance
**Dentro (esta iteración):** consulta de categorías y cupo; solicitud, autorización, confirmación, cancelación y no-show de reservaciones; check-in con identidad y garantía validada por un servicio externo; cargos y cuenta de estancia; cambio de habitación con historial; check-out con liquidación; ciclo de limpieza; habitación fuera de servicio; reporte de ocupación; beneficio para huésped preferente; control de acceso por rol; API REST, persistencia en PostgreSQL, Docker y CI/CD.

**Diferido (backlog):** salida anticipada, extensión de estancia, llegada anticipada (early check-in), cargos por penalización de no-show, expiración de la pre-reserva a las 24 h, tarifas por temporada. **[CAMBIO]** Ya no se difiere la penalidad por cancelación tardía (48 h) ni el tope de crédito de $3,000 MXN: se implementaron en esta versión.

**Fuera de alcance:** contabilidad general, nómina, facturación fiscal electrónica, pagos reales con tarjeta, interfaz gráfica.

## 5. Necesidades
| ID | Necesidad |
|---|---|
| N1 | Consultar categorías de habitación con su tarifa y cupo disponible. |
| N2 | Solicitar y confirmar reservaciones sin vender más cupo del que existe. |
| N3 | Hacer el check-in verificando identidad y garantía, y entregando una habitación lista. |
| N4 | Registrar los consumos de la estancia en una sola cuenta. |
| N5 | Revisar y liquidar los cargos en el check-out. |
| N6 | Mandar la habitación a limpieza al terminar la estancia. |
| N7 | Que Recepción vea de inmediato cuando Limpieza libera una habitación. |
| N8 | Rastrear los cambios de habitación. |
| N9 | Gestionar cancelaciones y no-show devolviendo el cupo. |
| N12 | Sacar de servicio una habitación y volver a activarla. |
| N14 | Que Administración vea la ocupación del hotel. |
| N15 | Reconocer a los huéspedes preferentes con un beneficio (regla del paquete de pruebas del PIA, por confirmar con el negocio). |
| N16 | Que cada rol solo pueda ejecutar las operaciones que le corresponden. |
| N10, N11, N13 | Salida anticipada, extensión y llegada anticipada (diferidas). |

## 6. Requisitos funcionales
| ID | Requisito | Necesidad |
|---|---|---|
| RF-01 | El sistema lista las categorías con tarifa, cupo y si están habilitadas. | N1 |
| RF-02 | El sistema registra una solicitud de reservación con una o más líneas (categoría y cantidad) y toma la tarifa del catálogo. | N2 |
| RF-03 | Reservaciones puede autorizar una reservación solicitada. | N2 |
| RF-04 | Una reservación solo se confirma si el huésped está activo, tiene detalle, está autorizada, sus categorías están habilitadas y hay cupo; al confirmar se descuenta el cupo. | N2 |
| RF-05 | Una reservación solicitada o confirmada puede cancelarse; si estaba confirmada, el cupo se devuelve. **[CAMBIO]** Si estaba confirmada y la llegada es en menos de 48 h, se cobra 1 noche de penalidad, salvo excepción autorizada por el Jefe de Reservaciones/Administración. | N9 |
| RF-06 | Una reservación confirmada puede marcarse como no-show; el cupo se devuelve. | N9 |
| RF-07 | El check-in exige identidad verificada y una garantía aprobada por el servicio externo; entrega una habitación disponible de la categoría reservada y abre la cuenta con el hospedaje. | N3 |
| RF-08 | Durante la estancia se registran cargos con concepto, monto y empleado. **[CAMBIO]** Los consumos (sin hospedaje) tienen un tope de crédito de $3,000 MXN; se supera con pago parcial previo o autorización de Administración. | N4 |
| RF-09 | Durante la estancia se puede cambiar de habitación; la anterior pasa a limpieza y el cambio queda en el historial. | N8 |
| RF-10 | El check-out registra el pago y cierra la cuenta solo si no queda saldo; la habitación pasa a pendiente de limpieza. | N5, N6 |
| RF-11 | Solo Limpieza puede marcar una habitación pendiente de limpieza como disponible, y el cambio queda visible de inmediato. | N7 |
| RF-12 | Administración puede sacar de servicio una habitación (no ocupada) y reactivarla. | N12 |
| RF-13 | Cualquier rol puede consultar una reservación; el sistema indica si requiere revisión. | N2 |
| RF-14 | Los roles pueden consultar el estatus de todas las habitaciones. | N7 |
| RF-15 | Recepción y Administración pueden consultar la cuenta de una estancia. | N4 |
| RF-16 | Se puede consultar el historial de cambios de una reservación. | N8 |
| RF-17 | Administración obtiene un reporte de ocupación con habitaciones y reservaciones por estado. | N14 |
| RF-18 | Al confirmar, si el huésped es preferente, el total llega al umbral y no hay promoción activa, se otorga el beneficio preferente. | N15 |
| RF-19 | Cada operación valida el rol; Administración puede consultar los eventos del sistema. | N16 |

## 7. Requisitos no funcionales
| ID | Requisito |
|---|---|
| RNF-01 | Consistencia: cada caso de uso guarda todos sus cambios o ninguno (Unit of Work). |
| RNF-02 | Mantenibilidad: capas separadas; el dominio no depende de frameworks ni de la base de datos. |
| RNF-03 | Verificabilidad: cobertura mínima de 80% medida con pytest-cov. |
| RNF-04 | Configuración por variables de entorno; sin secretos en el código ni en GitHub. |
| RNF-05 | Despliegue reproducible con Docker y Docker Compose. |
| RNF-06 | Documentación de la API generada automáticamente (OpenAPI en /docs). |
| RNF-07 | Los errores devuelven códigos HTTP coherentes: 400, 403, 404, 409, 422 y 503. |
| RNF-08 | Importes monetarios con precisión decimal (no con números de punto flotante). |

## 8. Restricciones
- Hotel de 120 habitaciones.
- Una sola moneda (pesos mexicanos).
- Python 3.12, FastAPI, SQLAlchemy y PostgreSQL.
- Los datos del paquete del PIA son ficticios y solo sirven para probar.

## 9. Supuestos
- Cada categoría tiene un **cupo** de habitaciones-noche disponibles; confirmar una reservación lo descuenta y cancelar o no-show lo devuelve. El cupo del paquete (capacidad_o_stock) se tomó con ese significado.
- La **cantidad** de cada línea se entiende como habitaciones-noche; el total de la reservación es la suma de tarifa por cantidad (regla del paquete).
- En esta iteración una estancia usa una habitación física, que debe ser de una de las categorías reservadas.
- La **autorización** de una reservación la da el área de Reservaciones; el caso no dice con qué criterio.
- La matriz de permisos por rol es una propuesta de diseño y debe validarse con el negocio.
- El **umbral de beneficio** (1,500 MXN) viene del paquete del PIA y es configurable (variable BENEFICIO_UMBRAL_MXN).
- **[CAMBIO]** Tope de crédito: se calcula sobre los consumos (sin el hospedaje) menos lo ya pagado; la "autorización de Administración" se modeló como un indicador en la petición (no existe un rol "Jefe de Reservaciones" aparte; su excepción de cancelación también es un indicador). La penalidad de cancelación se devuelve en la respuesta y en el evento, pero no se guarda en la base.
- **[CAMBIO]** La expiración de la pre-reserva a las 24 h y la llegada anticipada/salida anticipada/extensión no se implementan en esta iteración (la expiración sí se implementó en el laboratorio de la Actividad 5).
- La validación de garantía usa una pasarela simulada; el negocio aún no define el proveedor.
- Se aplica un hospedaje igual al total de la reservación como primer cargo de la cuenta; los impuestos no se modelaron.

## 10. Criterios de éxito
| Criterio | Cómo se verifica |
|---|---|
| Cero confirmaciones por encima del cupo | Pruebas de confirmación sin cupo y de la última suite. |
| Recepción ve el estatus actualizado de inmediato | Prueba del ciclo check-out → limpieza → disponible y consulta de habitaciones. |
| 100% de los cambios de habitación con historial | Pruebas de cambio de habitación e historial. |
| Una cuenta única por estancia | Pruebas de cuenta, cargos y cierre. |
| Ninguna operación guarda cambios a medias | Pruebas de rechazo con reversión. |
| Los 120 casos y las 20 transiciones del PIA coinciden con un cálculo independiente | tests/unit/test_datos_pia.py |
| Cobertura mínima de 80% | pytest-cov en CI. |

## 11. Riesgos
| Riesgo | Mitigación |
|---|---|
| Políticas sin definir (penalización de no-show, garantías). **[CAMBIO]** La cancelación y el tope de crédito ya están definidos. | Se documentan como preguntas abiertas; el modelo las recibe como configuración. |
| Autenticación basada solo en un encabezado de rol. | Se documenta como limitación (ADR-008); siguiente paso: JWT. |
| Eventos en memoria que se pierden al reiniciar. | Se documenta (ADR-007); siguiente paso: tabla outbox. |
| Sin migraciones de base de datos. | Las tablas se crean al arrancar; siguiente paso: Alembic. |

## 12. Preguntas abiertas para el stakeholder
1. ~~¿Cuál es el plazo de cancelación sin penalización y qué se cobra después?~~ **[CAMBIO]** Respondida por el BRD del equipo: 48 h y una noche de penalidad (excepción del Jefe de Reservaciones/Administración).
2. ¿Qué se cobra por un no-show?
3. ¿Qué criterio usa Reservaciones para autorizar una reservación?
4. ¿Qué tipos de garantía se aceptan y quién las valida?
5. ¿Quién autoriza el cambio a una habitación de otra categoría?
6. ¿Qué beneficio concreto recibe un huésped preferente y con qué umbral?
7. ¿Cómo se cobran la salida anticipada y la extensión?
8. ¿Qué reportes necesita Administración además de la ocupación?
