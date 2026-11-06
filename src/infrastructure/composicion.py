"""Punto único donde se arman las piezas (el dominio no conoce nada de esto)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..application.servicios import (ServicioDeAdministracion, ServicioDeConsultas,
                                     ServicioDeLimpieza, ServicioDeRecepcion,
                                     ServicioDeReservaciones)
from .configuracion import Configuracion
from .datos_pia import DatosPIA, cargar_datos
from .en_memoria import Almacen, PublicadorEnMemoria, UnidadDeTrabajoEnMemoria
from .pasarela_simulada import PasarelaDeGarantiaSimulada


@dataclass
class Contenedor:
    reservaciones: Any
    recepcion: Any
    limpieza: Any
    administracion: Any
    consultas: Any
    publicador: PublicadorEnMemoria
    nueva_uow: Any
    configuracion: Configuracion


def crear_contenedor(configuracion=None, reloj=datetime.now, pasarela=None):
    configuracion = configuracion or Configuracion()
    if configuracion.database_url == "memory":
        almacen = Almacen()

        def nueva_uow():
            return UnidadDeTrabajoEnMemoria(almacen)
    else:
        from .sql import UnidadDeTrabajoSql, crear_fabrica, crear_motor
        fabrica = crear_fabrica(crear_motor(configuracion.database_url))

        def nueva_uow():
            return UnidadDeTrabajoSql(fabrica)

    publicador = PublicadorEnMemoria()
    pasarela = pasarela or PasarelaDeGarantiaSimulada()
    comunes = {"publicador": publicador, "reloj": reloj,
               "umbral_beneficio": configuracion.umbral_beneficio_mxn, "pasarela": pasarela}
    contenedor = Contenedor(
        reservaciones=ServicioDeReservaciones(nueva_uow, **comunes),
        recepcion=ServicioDeRecepcion(nueva_uow, **comunes),
        limpieza=ServicioDeLimpieza(nueva_uow, **comunes),
        administracion=ServicioDeAdministracion(nueva_uow, **comunes),
        consultas=ServicioDeConsultas(nueva_uow, **comunes),
        publicador=publicador, nueva_uow=nueva_uow, configuracion=configuracion)
    if configuracion.cargar_datos_demo:
        cargar_datos(nueva_uow, DatosPIA(configuracion.ruta_datos),
                     configuracion.habitaciones_por_categoria)
    return contenedor
