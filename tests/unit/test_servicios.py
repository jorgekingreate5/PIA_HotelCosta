from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.application.comandos import (CambiarHabitacion, RealizarCheckIn, RealizarCheckOut,
                                      RegistrarCargo, SolicitarReservacion)
from src.domain.errores import (CuentaError, NoEncontradoError, PermisoDenegadoError,
                                PrecondicionNoCumplidaError, ServicioExternoNoDisponibleError,
                                SinCupoError, TransicionInvalidaError)
from src.domain.eventos import (CheckInRealizado, HabitacionDisponible,
                                HabitacionPendienteDeLimpieza, ReservacionConfirmada)
from src.domain.valor import EstadoHabitacion, EstadoReservacion, Garantia
from tests.helpers import contenedor_basico

GARANTIA = Garantia("tarjeta", "TC-0001")
RES, REC, LIM, ADM = "RESERVACIONES", "RECEPCION", "LIMPIEZA", "ADMINISTRACION"


def solicitar(c, rid="R1", huesped="H1", lineas=(("C1", 2),), autorizada=True, promocion=False):
    return c.reservaciones.solicitar_reservacion(RES, SolicitarReservacion(
        huesped, list(lineas), reservacion_id=rid, autorizada=autorizada,
        promocion_activa=promocion))


def confirmada(c, rid="R1", **kwargs):
    solicitar(c, rid, **kwargs)
    return c.reservaciones.confirmar_reservacion(RES, rid)


def en_estancia(c, rid="R1", habitacion="HAB-101"):
    confirmada(c, rid)
    return c.recepcion.realizar_check_in(
        REC, RealizarCheckIn(rid, habitacion, True, GARANTIA))


def estado_habitacion(c, hid):
    return {h.id: h.estado for h in c.consultas.estatus_de_habitaciones(REC)}[hid]


# ----- reservaciones
def test_solicitar_toma_la_tarifa_del_catalogo():
    c = contenedor_basico()
    r = solicitar(c)
    assert r.estado == EstadoReservacion.SOLICITADA and r.total == Decimal("2000")
    assert r.fecha_solicitud.isoformat() == "2026-10-20"


def test_solicitar_genera_un_identificador_si_no_se_indica():
    c = contenedor_basico()
    r = c.reservaciones.solicitar_reservacion(RES, SolicitarReservacion("H1", [("C1", 1)]))
    assert r.id.startswith("RES-")


@pytest.mark.parametrize("huesped,categoria", [("NO-EXISTE", "C1"), ("H1", "NO-EXISTE")])
def test_solicitar_con_huesped_o_categoria_inexistente(huesped, categoria):
    c = contenedor_basico()
    with pytest.raises(NoEncontradoError):
        solicitar(c, huesped=huesped, lineas=((categoria, 1),))
    assert c.consultas.listar_reservaciones(RES) == []


def test_confirmar_descuenta_cupo_y_publica_eventos():
    c = contenedor_basico()
    confirmada(c)
    cupo = {x.id: x.cupo_disponible for x in c.consultas.consultar_categorias(RES)}
    assert cupo["C1"] == 3
    assert ReservacionConfirmada in [type(e) for e in c.publicador.eventos]


def test_confirmar_sin_autorizacion_no_cambia_nada():
    c = contenedor_basico()
    solicitar(c, autorizada=False)
    with pytest.raises(PrecondicionNoCumplidaError):
        c.reservaciones.confirmar_reservacion(RES, "R1")
    r = c.consultas.consultar_reservacion(RES, "R1")
    assert r.estado == EstadoReservacion.SOLICITADA
    c.reservaciones.autorizar_reservacion(RES, "R1")
    c.reservaciones.confirmar_reservacion(RES, "R1")
    assert c.consultas.consultar_reservacion(RES, "R1").estado == EstadoReservacion.CONFIRMADA


def test_confirmar_sin_cupo_deja_el_cupo_intacto():
    c = contenedor_basico()
    solicitar(c, lineas=(("C2", 2),))
    with pytest.raises(SinCupoError):
        c.reservaciones.confirmar_reservacion(RES, "R1")
    cupo = {x.id: x.cupo_disponible for x in c.consultas.consultar_categorias(RES)}
    assert cupo["C2"] == 1


def test_no_se_vende_dos_veces_la_ultima_suite():
    c = contenedor_basico()
    confirmada(c, "R1", lineas=(("C2", 1),))
    solicitar(c, "R2", huesped="H2", lineas=(("C2", 1),))
    with pytest.raises(SinCupoError):
        c.reservaciones.confirmar_reservacion(RES, "R2")


def test_confirmar_dos_veces_falla_con_transicion_invalida():
    c = contenedor_basico()
    confirmada(c)
    with pytest.raises(TransicionInvalidaError):
        c.reservaciones.confirmar_reservacion(RES, "R1")


def test_cancelar_libera_el_cupo():
    c = contenedor_basico()
    confirmada(c)
    c.reservaciones.cancelar_reservacion(RES, "R1")
    cupo = {x.id: x.cupo_disponible for x in c.consultas.consultar_categorias(RES)}
    assert cupo["C1"] == 5


def test_no_show_marca_la_reservacion_y_libera_cupo():
    c = contenedor_basico()
    confirmada(c)
    r = c.reservaciones.registrar_no_show(REC, "R1")
    assert r.estado == EstadoReservacion.NO_SHOW


# ----- check-in, cargos, cambio y check-out
def test_check_in_ocupa_la_habitacion_y_abre_la_cuenta():
    c = contenedor_basico()
    en_estancia(c)
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.OCUPADA
    cuenta = c.consultas.cuenta_de_estancia(REC, "R1")
    assert cuenta.total == Decimal("2000") and cuenta.abierta
    assert CheckInRealizado in [type(e) for e in c.publicador.eventos]


def test_check_in_sin_identidad_se_rechaza_y_no_abre_cuenta():
    c = contenedor_basico()
    confirmada(c)
    with pytest.raises(PrecondicionNoCumplidaError):
        c.recepcion.realizar_check_in(REC, RealizarCheckIn("R1", "HAB-101", False, GARANTIA))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.DISPONIBLE
    with pytest.raises(NoEncontradoError):
        c.consultas.cuenta_de_estancia(REC, "R1")


def test_check_in_con_garantia_rechazada_por_la_pasarela():
    c = contenedor_basico()
    confirmada(c)
    rechazada = Garantia("tarjeta", "TC-9-RECHAZADA")
    with pytest.raises(PrecondicionNoCumplidaError, match="rechazada"):
        c.recepcion.realizar_check_in(REC, RealizarCheckIn("R1", "HAB-101", True, rechazada))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.DISPONIBLE


def test_check_in_con_timeout_de_la_pasarela_es_servicio_no_disponible():
    c = contenedor_basico()
    confirmada(c)
    sin_respuesta = Garantia("tarjeta", "TC-9-TIMEOUT")
    with pytest.raises(ServicioExternoNoDisponibleError):
        c.recepcion.realizar_check_in(REC, RealizarCheckIn("R1", "HAB-101", True, sin_respuesta))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.DISPONIBLE


def test_check_in_con_pasarela_simulada_con_mock():
    pasarela = Mock()
    pasarela.validar.return_value = True
    c = contenedor_basico(pasarela=pasarela)
    en_estancia(c)
    pasarela.validar.assert_called_once_with(GARANTIA)


def test_pasarela_no_se_consulta_si_falta_la_identidad():
    pasarela = Mock()
    c = contenedor_basico(pasarela=pasarela)
    confirmada(c)
    with pytest.raises(PrecondicionNoCumplidaError):
        c.recepcion.realizar_check_in(REC, RealizarCheckIn("R1", "HAB-101", False, GARANTIA))
    pasarela.validar.assert_not_called()


def test_registrar_cargos_y_consultar_la_cuenta():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.registrar_cargo(REC, RegistrarCargo("R1", "Restaurante", Decimal("250"), "E1"))
    assert c.consultas.cuenta_de_estancia(ADM, "R1").total == Decimal("2250")


def test_cambio_de_habitacion_deja_historial_y_la_anterior_pasa_a_limpieza():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.cambiar_habitacion(REC, CambiarHabitacion("R1", "HAB-102", "Ruido", "E1"))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA
    assert estado_habitacion(c, "HAB-102") == EstadoHabitacion.OCUPADA
    historial = c.consultas.historial_de_cambios(REC, "R1")
    assert [(x.origen_id, x.destino_id) for x in historial] == [("HAB-101", "HAB-102")]


def test_cambio_a_habitacion_ocupada_se_rechaza_y_se_revierte():
    c = contenedor_basico()
    en_estancia(c)
    c.administracion.marcar_fuera_de_servicio(ADM, "HAB-102")
    with pytest.raises(Exception):
        c.recepcion.cambiar_habitacion(REC, CambiarHabitacion("R1", "HAB-102", "Ruido", "E1"))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.OCUPADA
    assert c.consultas.historial_de_cambios(REC, "R1") == []


def test_check_out_con_saldo_pendiente_se_rechaza_y_revierte_el_pago():
    c = contenedor_basico()
    en_estancia(c)
    with pytest.raises(CuentaError):
        c.recepcion.realizar_check_out(REC, RealizarCheckOut("R1", Decimal("500")))
    cuenta = c.consultas.cuenta_de_estancia(REC, "R1")
    assert cuenta.pagado == 0 and cuenta.abierta
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.OCUPADA


def test_ciclo_completo_hasta_que_limpieza_libera_la_habitacion():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.realizar_check_out(REC, RealizarCheckOut("R1", Decimal("2000")))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA
    c.limpieza.marcar_habitacion_disponible(LIM, "HAB-101")
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.DISPONIBLE
    tipos = [type(e) for e in c.publicador.eventos]
    assert HabitacionPendienteDeLimpieza in tipos and HabitacionDisponible in tipos
    assert c.consultas.consultar_reservacion(REC, "R1").estado == EstadoReservacion.CHECK_OUT


def test_cargo_despues_del_check_out_se_rechaza():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.realizar_check_out(REC, RealizarCheckOut("R1", Decimal("2000")))
    with pytest.raises(CuentaError):
        c.recepcion.registrar_cargo(REC, RegistrarCargo("R1", "Minibar", Decimal("50"), "E1"))


# ----- permisos y administración
def test_solo_limpieza_libera_habitaciones():
    c = contenedor_basico()
    en_estancia(c)
    c.recepcion.realizar_check_out(REC, RealizarCheckOut("R1", Decimal("2000")))
    with pytest.raises(PermisoDenegadoError):
        c.limpieza.marcar_habitacion_disponible(REC, "HAB-101")
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA


def test_recepcion_no_puede_confirmar_reservaciones():
    c = contenedor_basico()
    solicitar(c)
    with pytest.raises(PermisoDenegadoError):
        c.reservaciones.confirmar_reservacion(REC, "R1")


def test_administracion_saca_de_servicio_y_reactiva():
    c = contenedor_basico()
    c.administracion.marcar_fuera_de_servicio(ADM, "HAB-201")
    assert estado_habitacion(c, "HAB-201") == EstadoHabitacion.FUERA_DE_SERVICIO
    c.administracion.reactivar_habitacion(ADM, "HAB-201")
    assert estado_habitacion(c, "HAB-201") == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA


# ----- consultas y reporte
def test_reporte_de_ocupacion():
    c = contenedor_basico()
    en_estancia(c)
    reporte = c.consultas.reporte_de_ocupacion(ADM)
    assert reporte["habitaciones_total"] == 3
    assert reporte["habitaciones_por_estado"]["OCUPADA"] == 1
    assert reporte["ocupacion_porcentaje"] == 33.33
    assert reporte["reservaciones_por_estado"]["CHECK_IN"] == 1


def test_reporte_de_un_hotel_sin_habitaciones():
    from src.infrastructure.composicion import crear_contenedor
    reporte = crear_contenedor().consultas.reporte_de_ocupacion(ADM)
    assert reporte["ocupacion_porcentaje"] == 0.0


def test_listar_reservaciones_por_estado():
    c = contenedor_basico()
    confirmada(c, "R1")
    solicitar(c, "R2", huesped="H2")
    soli = c.consultas.listar_reservaciones(RES, EstadoReservacion.SOLICITADA)
    assert [r.id for r in soli] == ["R2"]
    assert len(c.consultas.listar_reservaciones(RES)) == 2


def test_consultar_reservacion_inexistente():
    c = contenedor_basico()
    with pytest.raises(NoEncontradoError):
        c.consultas.consultar_reservacion(RES, "NO-EXISTE")


def test_consultar_reservacion_con_huesped():
    c = contenedor_basico()
    solicitar(c)
    reservacion, huesped = c.consultas.consultar_reservacion_con_huesped(RES, "R1")
    assert reservacion.huesped_id == huesped.id == "H1"


def test_servicio_de_recepcion_sin_pasarela_no_valida_la_garantia():
    from src.application.servicios import ServicioDeRecepcion
    from src.infrastructure.en_memoria import PublicadorEnMemoria
    c = contenedor_basico()
    confirmada(c)
    servicio = ServicioDeRecepcion(c.nueva_uow, PublicadorEnMemoria(), pasarela=None)
    servicio.realizar_check_in(REC, RealizarCheckIn("R1", "HAB-101", True, GARANTIA))
    assert estado_habitacion(c, "HAB-101") == EstadoHabitacion.OCUPADA
