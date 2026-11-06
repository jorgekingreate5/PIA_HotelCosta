"""API REST de Hotel Costa Azul (FastAPI). Las rutas solo traducen HTTP <-> casos de uso."""
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Header, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field

from ..application.comandos import (CambiarHabitacion, RealizarCheckIn, RealizarCheckOut,
                                    RegistrarCargo, SolicitarReservacion)
from ..application.permisos import exigir_permiso
from ..domain.errores import ErrorDeDominio
from ..domain.valor import EstadoReservacion, Garantia
from ..infrastructure.composicion import crear_contenedor
from ..infrastructure.configuracion import Configuracion
from .manejo_errores import codigo_http, cuerpo_de_error
from .serializadores import (cambio_a_dict, categoria_a_dict, cuenta_a_dict, evento_a_dict,
                             habitacion_a_dict, reservacion_a_dict, reservacion_con_revision)


class LineaIn(BaseModel):
    categoria_id: str
    cantidad: int = Field(gt=0)


class SolicitudReservacionIn(BaseModel):
    huesped_id: str
    lineas: list[LineaIn] = Field(min_length=1)
    reservacion_id: Optional[str] = None
    referencia: str = ""
    promocion_activa: bool = False


class GarantiaIn(BaseModel):
    tipo: str = Field(min_length=1)
    referencia: str = Field(min_length=1)


class CheckInIn(BaseModel):
    habitacion_id: str
    identidad_verificada: bool
    garantia: Optional[GarantiaIn] = None


class CargoIn(BaseModel):
    concepto: str = Field(min_length=1)
    monto: Decimal = Field(gt=0)
    empleado_id: str = Field(min_length=1)
    autorizacion_administracion: bool = False  # CAMBIO PIA


class CancelarIn(BaseModel):  # CAMBIO PIA: política de cancelación de 48 h
    fecha_llegada: Optional[datetime] = None
    autorizacion_jefe: bool = False


class CambioHabitacionIn(BaseModel):
    nueva_habitacion_id: str
    motivo: str = Field(min_length=1)
    responsable: str = Field(min_length=1)


class CheckOutIn(BaseModel):
    monto_pagado: Decimal = Field(default=Decimal("0"), ge=0)


def crear_app(contenedor=None):
    c = contenedor or crear_contenedor(Configuracion.desde_entorno())
    app = FastAPI(
        title="Hotel Costa Azul – API de Reservaciones",
        version="1.0.0",
        description=("Reservación, check-in, estancia, check-out y limpieza. "
                     "Envía el rol en el encabezado X-Rol (RESERVACIONES, RECEPCION, LIMPIEZA "
                     "o ADMINISTRACION)."),
    )

    @app.exception_handler(ErrorDeDominio)
    async def manejar_error_de_dominio(request: Request, error: ErrorDeDominio):
        return JSONResponse(status_code=codigo_http(error), content=cuerpo_de_error(error))

    @app.get("/", include_in_schema=False)
    def panel():  # CAMBIO PIA: pantalla sencilla para clientes y jefes (no es parte del contrato REST)
        return HTMLResponse((Path(__file__).parent / "static" / "panel.html").read_text(encoding="utf-8"))

    @app.get("/health", tags=["Sistema"])
    def salud():
        return {"estado": "ok"}

    @app.get("/categorias", tags=["Consultas"])
    def consultar_categorias(x_rol: Optional[str] = Header(default=None)):
        return [categoria_a_dict(x) for x in c.consultas.consultar_categorias(x_rol)]

    @app.post("/reservaciones", status_code=201, tags=["Reservaciones"])
    def solicitar_reservacion(datos: SolicitudReservacionIn,
                              x_rol: Optional[str] = Header(default=None)):
        comando = SolicitarReservacion(
            huesped_id=datos.huesped_id,
            lineas=[(x.categoria_id, x.cantidad) for x in datos.lineas],
            reservacion_id=datos.reservacion_id, referencia=datos.referencia,
            promocion_activa=datos.promocion_activa)
        return reservacion_a_dict(c.reservaciones.solicitar_reservacion(x_rol, comando))

    @app.get("/reservaciones", tags=["Reservaciones"])
    def listar_reservaciones(estado: Optional[EstadoReservacion] = Query(default=None),
                             x_rol: Optional[str] = Header(default=None)):
        return [reservacion_a_dict(x) for x in c.consultas.listar_reservaciones(x_rol, estado)]

    @app.get("/reservaciones/{reservacion_id}", tags=["Reservaciones"])
    def consultar_reservacion(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        reservacion, huesped = c.consultas.consultar_reservacion_con_huesped(x_rol, reservacion_id)
        return reservacion_con_revision(reservacion, huesped)

    @app.post("/reservaciones/{reservacion_id}/autorizar", tags=["Reservaciones"])
    def autorizar(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return reservacion_a_dict(c.reservaciones.autorizar_reservacion(x_rol, reservacion_id))

    @app.post("/reservaciones/{reservacion_id}/confirmar", tags=["Reservaciones"])
    def confirmar(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return reservacion_a_dict(c.reservaciones.confirmar_reservacion(x_rol, reservacion_id))

    @app.post("/reservaciones/{reservacion_id}/cancelar", tags=["Reservaciones"])
    def cancelar(reservacion_id: str, datos: Optional[CancelarIn] = None,
                 x_rol: Optional[str] = Header(default=None)):
        datos = datos or CancelarIn()
        return reservacion_a_dict(c.reservaciones.cancelar_reservacion(
            x_rol, reservacion_id, datos.fecha_llegada, datos.autorizacion_jefe))

    @app.post("/reservaciones/{reservacion_id}/no-show", tags=["Reservaciones"])
    def no_show(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return reservacion_a_dict(c.reservaciones.registrar_no_show(x_rol, reservacion_id))

    @app.post("/reservaciones/{reservacion_id}/check-in", tags=["Estancia"])
    def check_in(reservacion_id: str, datos: CheckInIn,
                 x_rol: Optional[str] = Header(default=None)):
        garantia = Garantia(datos.garantia.tipo, datos.garantia.referencia) \
            if datos.garantia else None
        comando = RealizarCheckIn(reservacion_id, datos.habitacion_id,
                                  datos.identidad_verificada, garantia)
        return reservacion_a_dict(c.recepcion.realizar_check_in(x_rol, comando))

    @app.post("/reservaciones/{reservacion_id}/cargos", status_code=201, tags=["Estancia"])
    def registrar_cargo(reservacion_id: str, datos: CargoIn,
                        x_rol: Optional[str] = Header(default=None)):
        comando = RegistrarCargo(reservacion_id, datos.concepto, datos.monto, datos.empleado_id,
                                 datos.autorizacion_administracion)
        return cuenta_a_dict(c.recepcion.registrar_cargo(x_rol, comando))

    @app.get("/reservaciones/{reservacion_id}/cuenta", tags=["Estancia"])
    def consultar_cuenta(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return cuenta_a_dict(c.consultas.cuenta_de_estancia(x_rol, reservacion_id))

    @app.post("/reservaciones/{reservacion_id}/cambio-habitacion", tags=["Estancia"])
    def cambiar_habitacion(reservacion_id: str, datos: CambioHabitacionIn,
                           x_rol: Optional[str] = Header(default=None)):
        comando = CambiarHabitacion(reservacion_id, datos.nueva_habitacion_id, datos.motivo,
                                    datos.responsable)
        return reservacion_a_dict(c.recepcion.cambiar_habitacion(x_rol, comando))

    @app.get("/reservaciones/{reservacion_id}/historial-cambios", tags=["Estancia"])
    def historial(reservacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return [cambio_a_dict(x) for x in c.consultas.historial_de_cambios(x_rol, reservacion_id)]

    @app.post("/reservaciones/{reservacion_id}/check-out", tags=["Estancia"])
    def check_out(reservacion_id: str, datos: CheckOutIn,
                  x_rol: Optional[str] = Header(default=None)):
        comando = RealizarCheckOut(reservacion_id, datos.monto_pagado)
        return reservacion_a_dict(c.recepcion.realizar_check_out(x_rol, comando))

    @app.get("/habitaciones", tags=["Habitaciones"])
    def estatus_habitaciones(x_rol: Optional[str] = Header(default=None)):
        return [habitacion_a_dict(x) for x in c.consultas.estatus_de_habitaciones(x_rol)]

    @app.post("/habitaciones/{habitacion_id}/limpieza-terminada", tags=["Habitaciones"])
    def limpieza_terminada(habitacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return habitacion_a_dict(c.limpieza.marcar_habitacion_disponible(x_rol, habitacion_id))

    @app.post("/habitaciones/{habitacion_id}/fuera-de-servicio", tags=["Habitaciones"])
    def fuera_de_servicio(habitacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return habitacion_a_dict(c.administracion.marcar_fuera_de_servicio(x_rol, habitacion_id))

    @app.post("/habitaciones/{habitacion_id}/reactivar", tags=["Habitaciones"])
    def reactivar(habitacion_id: str, x_rol: Optional[str] = Header(default=None)):
        return habitacion_a_dict(c.administracion.reactivar_habitacion(x_rol, habitacion_id))

    @app.get("/reportes/ocupacion", tags=["Reportes"])
    def reporte_ocupacion(x_rol: Optional[str] = Header(default=None)):
        return c.consultas.reporte_de_ocupacion(x_rol)

    @app.get("/eventos", tags=["Reportes"])
    def eventos(x_rol: Optional[str] = Header(default=None)):
        exigir_permiso(x_rol, "ver_eventos")
        return [evento_a_dict(e) for e in c.publicador.eventos[-100:]]

    return app


app = None


def obtener_app():
    """Fábrica para uvicorn: uvicorn src.api.app:obtener_app --factory."""
    global app
    if app is None:
        app = crear_app()
    return app
