"""Ejecuta las 20 transiciones del PIA sobre el sistema completo (servicios + memoria)."""
from datetime import datetime
from decimal import Decimal

from ..application.comandos import RealizarCheckIn, RealizarCheckOut
from ..domain.errores import ErrorDeDominio
from ..domain.valor import EstadoHabitacion, Garantia
from .composicion import crear_contenedor
from .configuracion import Configuracion
from .datos_pia import DatosPIA, cargar_datos

RELOJ_FIJO = lambda: datetime(2026, 10, 25, 10, 0)  # noqa: E731


def _habitacion_libre(contenedor, reservacion):
    categorias = reservacion.cantidades_por_categoria()
    for habitacion in contenedor.consultas.estatus_de_habitaciones("RECEPCION"):
        if (habitacion.categoria_id in categorias
                and habitacion.estado == EstadoHabitacion.DISPONIBLE):
            return habitacion
    return None


def _flujo(contenedor, operacion_id, accion):
    reservaciones, recepcion = contenedor.reservaciones, contenedor.recepcion
    if accion == "aprobar":
        reservaciones.confirmar_reservacion("RESERVACIONES", operacion_id)
    elif accion == "cancelar":
        reservaciones.cancelar_reservacion("RESERVACIONES", operacion_id)
    elif accion == "repetir_aprobacion":
        reservaciones.confirmar_reservacion("RESERVACIONES", operacion_id)
        reservaciones.confirmar_reservacion("RESERVACIONES", operacion_id)
    elif accion == "saltar_estado":
        reservacion = contenedor.consultas.consultar_reservacion("RECEPCION", operacion_id)
        habitacion = _habitacion_libre(contenedor, reservacion)
        recepcion.realizar_check_in("RECEPCION", RealizarCheckIn(
            operacion_id, habitacion.id, True, Garantia("tarjeta", "TC-0001")))
    elif accion == "completar":
        reservaciones.confirmar_reservacion("RESERVACIONES", operacion_id)
        reservacion = contenedor.consultas.consultar_reservacion("RECEPCION", operacion_id)
        habitacion = _habitacion_libre(contenedor, reservacion)
        recepcion.realizar_check_in("RECEPCION", RealizarCheckIn(
            operacion_id, habitacion.id, True, Garantia("tarjeta", "TC-0001")))
        recepcion.realizar_check_out("RECEPCION", RealizarCheckOut(operacion_id, reservacion.total))
    else:
        raise ValueError(f"Acción desconocida: {accion}")


def ejecutar_transiciones(carpeta="datos", umbral=Decimal("1500")):
    datos = DatosPIA(carpeta)
    resultados = []
    for caso in datos.transiciones:
        contenedor = crear_contenedor(Configuracion(umbral_beneficio_mxn=umbral),
                                      reloj=RELOJ_FIJO)
        cargar_datos(contenedor.nueva_uow, datos)
        operacion_id, accion = caso["operacion_id"], caso["accion_sugerida"]
        try:
            _flujo(contenedor, operacion_id, accion)
            resultado, detalle = "OK", ""
        except ErrorDeDominio as error:
            resultado, detalle = "RECHAZADA", f"{type(error).__name__}: {error}"
        estado_final = contenedor.consultas.consultar_reservacion("ADMINISTRACION", operacion_id)
        resultados.append({
            "caso_id": caso["caso_id"], "operacion_id": operacion_id, "accion": accion,
            "estado_inicial": caso["estado_inicial"], "estado_final": estado_final.estado.value,
            "resultado": resultado, "detalle": detalle})
    return resultados
