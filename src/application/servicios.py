"""Application Services: un método por caso de uso. Coordinan; las reglas viven en el dominio."""
from collections import Counter
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from ..domain.cuenta_estancia import CuentaEstancia
from ..domain.errores import PrecondicionNoCumplidaError, ServicioExternoNoDisponibleError
from ..domain.reservacion import Reservacion
from ..domain.valor import EstadoHabitacion, EstadoReservacion, LineaReservacion
from .permisos import exigir_permiso


class _ServicioBase:
    def __init__(self, nueva_unidad_de_trabajo, publicador, reloj=datetime.now,
                 umbral_beneficio=Decimal("1500"), pasarela=None):
        self._nueva_uow = nueva_unidad_de_trabajo
        self._publicador = publicador
        self._reloj = reloj
        self._umbral = Decimal(umbral_beneficio)
        self._pasarela = pasarela

    def _publicar(self, *agregados):
        for agregado in agregados:
            for evento in agregado.sacar_eventos():
                self._publicador.publicar(evento)

    @staticmethod
    def _categorias_de(uow, reservacion):
        return {cid: uow.categorias.obtener(cid) for cid in reservacion.cantidades_por_categoria()}


class ServicioDeReservaciones(_ServicioBase):
    """Atiende al área de Reservaciones."""

    def solicitar_reservacion(self, rol, cmd):  # US-02
        exigir_permiso(rol, "solicitar_reservacion")
        with self._nueva_uow() as uow:
            uow.huespedes.obtener(cmd.huesped_id)
            lineas = []
            for categoria_id, cantidad in cmd.lineas:
                categoria = uow.categorias.obtener(categoria_id)
                lineas.append(LineaReservacion(categoria_id, cantidad, categoria.tarifa))
            reservacion = Reservacion.solicitar(
                cmd.reservacion_id or f"RES-{uuid4().hex[:8].upper()}", cmd.huesped_id, lineas,
                referencia=cmd.referencia,
                fecha_solicitud=cmd.fecha_solicitud or self._reloj().date(),
                autorizada=cmd.autorizada, promocion_activa=cmd.promocion_activa)
            uow.reservaciones.guardar(reservacion)
            uow.guardar_cambios()
        self._publicar(reservacion)
        return reservacion

    def autorizar_reservacion(self, rol, reservacion_id):  # US-03
        exigir_permiso(rol, "autorizar_reservacion")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(reservacion_id)
            reservacion.autorizar()
            uow.reservaciones.guardar(reservacion)
            uow.guardar_cambios()
        self._publicar(reservacion)
        return reservacion

    def confirmar_reservacion(self, rol, reservacion_id):  # US-04
        exigir_permiso(rol, "confirmar_reservacion")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(reservacion_id)
            huesped = uow.huespedes.obtener(reservacion.huesped_id)
            categorias = self._categorias_de(uow, reservacion)
            reservacion.confirmar(huesped, categorias, self._umbral)
            uow.reservaciones.guardar(reservacion)
            for categoria in categorias.values():
                uow.categorias.guardar(categoria)
            uow.guardar_cambios()
        self._publicar(reservacion, *categorias.values())
        return reservacion

    def cancelar_reservacion(self, rol, reservacion_id, fecha_llegada=None,
                             autorizacion_jefe=False):  # US-05 (CAMBIO PIA: penalidad 48 h)
        exigir_permiso(rol, "cancelar_reservacion")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(reservacion_id)
            categorias = self._categorias_de(uow, reservacion)
            reservacion.cancelar(categorias, self._reloj(), fecha_llegada, autorizacion_jefe)
            uow.reservaciones.guardar(reservacion)
            for categoria in categorias.values():
                uow.categorias.guardar(categoria)
            uow.guardar_cambios()
        self._publicar(reservacion, *categorias.values())
        return reservacion

    def registrar_no_show(self, rol, reservacion_id):  # US-06
        exigir_permiso(rol, "registrar_no_show")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(reservacion_id)
            categorias = self._categorias_de(uow, reservacion)
            reservacion.registrar_no_show(categorias)
            uow.reservaciones.guardar(reservacion)
            for categoria in categorias.values():
                uow.categorias.guardar(categoria)
            uow.guardar_cambios()
        self._publicar(reservacion, *categorias.values())
        return reservacion


class ServicioDeRecepcion(_ServicioBase):
    """Atiende a Recepción: llegada, estancia y salida del huésped."""

    def _validar_garantia(self, garantia):
        if garantia is None or self._pasarela is None:
            return
        try:
            aprobada = self._pasarela.validar(garantia)
        except TimeoutError as error:
            raise ServicioExternoNoDisponibleError(
                "No se pudo validar la garantía; intente de nuevo"
            ) from error
        if not aprobada:
            raise PrecondicionNoCumplidaError("La garantía fue rechazada")

    def realizar_check_in(self, rol, cmd):  # US-07
        exigir_permiso(rol, "realizar_check_in")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(cmd.reservacion_id)
            habitacion = uow.habitaciones.obtener(cmd.habitacion_id)
            if cmd.identidad_verificada:
                self._validar_garantia(cmd.garantia)
            reservacion.registrar_check_in(habitacion, cmd.identidad_verificada, cmd.garantia)
            cuenta = CuentaEstancia.abrir(f"CTA-{reservacion.id}", reservacion.id,
                                          reservacion.total, self._reloj())
            uow.reservaciones.guardar(reservacion)
            uow.habitaciones.guardar(habitacion)
            uow.cuentas.guardar(cuenta)
            uow.guardar_cambios()
        self._publicar(reservacion, habitacion, cuenta)
        return reservacion

    def registrar_cargo(self, rol, cmd):  # US-08
        exigir_permiso(rol, "registrar_cargo")
        with self._nueva_uow() as uow:
            cuenta = uow.cuentas.obtener_por_reservacion(cmd.reservacion_id)
            cuenta.registrar_cargo(cmd.concepto, cmd.monto, cmd.empleado_id, self._reloj(),
                                   cmd.autorizacion_administracion)
            uow.cuentas.guardar(cuenta)
            uow.guardar_cambios()
        self._publicar(cuenta)
        return cuenta

    def cambiar_habitacion(self, rol, cmd):  # US-09
        exigir_permiso(rol, "cambiar_habitacion")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(cmd.reservacion_id)
            actual = uow.habitaciones.obtener(reservacion.habitacion_id)
            nueva = uow.habitaciones.obtener(cmd.nueva_habitacion_id)
            reservacion.cambiar_habitacion(actual, nueva, cmd.motivo, cmd.responsable,
                                           self._reloj())
            uow.reservaciones.guardar(reservacion)
            uow.habitaciones.guardar(actual)
            uow.habitaciones.guardar(nueva)
            uow.guardar_cambios()
        self._publicar(reservacion, actual, nueva)
        return reservacion

    def realizar_check_out(self, rol, cmd):  # US-10
        exigir_permiso(rol, "realizar_check_out")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(cmd.reservacion_id)
            habitacion = uow.habitaciones.obtener(reservacion.habitacion_id)
            cuenta = uow.cuentas.obtener_por_reservacion(cmd.reservacion_id)
            cuenta.registrar_pago(cmd.monto_pagado)
            cuenta.cerrar()
            reservacion.registrar_check_out(habitacion)
            uow.cuentas.guardar(cuenta)
            uow.reservaciones.guardar(reservacion)
            uow.habitaciones.guardar(habitacion)
            uow.guardar_cambios()
        self._publicar(reservacion, habitacion, cuenta)
        return reservacion


class ServicioDeLimpieza(_ServicioBase):
    """Atiende al área de Limpieza."""

    def marcar_habitacion_disponible(self, rol, habitacion_id):  # US-11
        exigir_permiso(rol, "marcar_habitacion_disponible")
        with self._nueva_uow() as uow:
            habitacion = uow.habitaciones.obtener(habitacion_id)
            habitacion.marcar_disponible()
            uow.habitaciones.guardar(habitacion)
            uow.guardar_cambios()
        self._publicar(habitacion)
        return habitacion


class ServicioDeAdministracion(_ServicioBase):
    """Atiende a Administración: estado operativo de las habitaciones."""

    def marcar_fuera_de_servicio(self, rol, habitacion_id):  # US-12
        exigir_permiso(rol, "marcar_fuera_de_servicio")
        with self._nueva_uow() as uow:
            habitacion = uow.habitaciones.obtener(habitacion_id)
            habitacion.marcar_fuera_de_servicio()
            uow.habitaciones.guardar(habitacion)
            uow.guardar_cambios()
        self._publicar(habitacion)
        return habitacion

    def reactivar_habitacion(self, rol, habitacion_id):  # US-12
        exigir_permiso(rol, "reactivar_habitacion")
        with self._nueva_uow() as uow:
            habitacion = uow.habitaciones.obtener(habitacion_id)
            habitacion.reactivar()
            uow.habitaciones.guardar(habitacion)
            uow.guardar_cambios()
        self._publicar(habitacion)
        return habitacion


class ServicioDeConsultas(_ServicioBase):
    """Lado de lectura (CQRS básico): no modifica ni guarda nada."""

    def consultar_categorias(self, rol):  # US-01
        exigir_permiso(rol, "consultar_catalogo")
        with self._nueva_uow() as uow:
            return list(uow.categorias.listar())

    def consultar_reservacion(self, rol, reservacion_id):  # US-13
        exigir_permiso(rol, "consultar_reservacion")
        with self._nueva_uow() as uow:
            return uow.reservaciones.obtener(reservacion_id)

    def consultar_reservacion_con_huesped(self, rol, reservacion_id):
        exigir_permiso(rol, "consultar_reservacion")
        with self._nueva_uow() as uow:
            reservacion = uow.reservaciones.obtener(reservacion_id)
            return reservacion, uow.huespedes.obtener(reservacion.huesped_id)

    def listar_reservaciones(self, rol, estado=None):
        exigir_permiso(rol, "consultar_reservacion")
        with self._nueva_uow() as uow:
            reservaciones = list(uow.reservaciones.listar())
        if estado is not None:
            reservaciones = [r for r in reservaciones if r.estado == estado]
        return reservaciones

    def estatus_de_habitaciones(self, rol):  # US-14
        exigir_permiso(rol, "ver_estatus_habitaciones")
        with self._nueva_uow() as uow:
            return list(uow.habitaciones.listar())

    def cuenta_de_estancia(self, rol, reservacion_id):  # US-15
        exigir_permiso(rol, "consultar_cuenta")
        with self._nueva_uow() as uow:
            return uow.cuentas.obtener_por_reservacion(reservacion_id)

    def historial_de_cambios(self, rol, reservacion_id):  # US-16
        exigir_permiso(rol, "consultar_reservacion")
        with self._nueva_uow() as uow:
            return list(uow.reservaciones.obtener(reservacion_id).cambios)

    def reporte_de_ocupacion(self, rol):  # US-17
        exigir_permiso(rol, "ver_reporte_ocupacion")
        with self._nueva_uow() as uow:
            habitaciones = list(uow.habitaciones.listar())
            reservaciones = list(uow.reservaciones.listar())
        por_estado = Counter(h.estado for h in habitaciones)
        total = len(habitaciones)
        ocupadas = por_estado[EstadoHabitacion.OCUPADA]
        return {
            "habitaciones_total": total,
            "habitaciones_por_estado": {e.value: por_estado[e] for e in EstadoHabitacion},
            "ocupacion_porcentaje": round(ocupadas * 100 / total, 2) if total else 0.0,
            "reservaciones_por_estado": {
                e.value: sum(1 for r in reservaciones if r.estado == e)
                for e in EstadoReservacion
            },
        }
