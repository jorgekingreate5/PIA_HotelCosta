from datetime import datetime
from decimal import Decimal

import pytest

from src.domain.categoria import CategoriaHabitacion
from src.domain.cuenta_estancia import CuentaEstancia
from src.domain.errores import (CuentaError, DatoInvalidoError, HabitacionNoDisponibleError,
                                SinCupoError, TransicionInvalidaError)
from src.domain.eventos import HabitacionDisponible, HabitacionPendienteDeLimpieza
from src.domain.habitacion import Habitacion
from src.domain.valor import EstadoHabitacion, Garantia, LineaReservacion

AHORA = datetime(2026, 10, 20, 12, 0)


# ----- habitación
def test_entregar_habitacion_disponible():
    h = Habitacion("A", "101", "C1")
    h.entregar()
    assert h.estado == EstadoHabitacion.OCUPADA


@pytest.mark.parametrize("estado", [EstadoHabitacion.OCUPADA, EstadoHabitacion.PENDIENTE_DE_LIMPIEZA,
                                    EstadoHabitacion.FUERA_DE_SERVICIO])
def test_no_se_entrega_una_habitacion_que_no_esta_disponible(estado):
    h = Habitacion("A", "101", "C1", estado)
    with pytest.raises(HabitacionNoDisponibleError):
        h.entregar()
    assert h.estado == estado


def test_ciclo_completo_genera_eventos_de_limpieza():
    h = Habitacion("A", "101", "C1")
    h.entregar()
    h.enviar_a_limpieza()
    h.marcar_disponible()
    tipos = [type(e) for e in h.sacar_eventos()]
    assert tipos == [HabitacionPendienteDeLimpieza, HabitacionDisponible]
    assert h.sacar_eventos() == []


def test_solo_limpieza_pendiente_puede_marcarse_disponible():
    with pytest.raises(TransicionInvalidaError):
        Habitacion("A", "101", "C1", EstadoHabitacion.OCUPADA).marcar_disponible()


def test_fuera_de_servicio_y_reactivar_pasa_por_limpieza():
    h = Habitacion("A", "101", "C1")
    h.marcar_fuera_de_servicio()
    assert h.estado == EstadoHabitacion.FUERA_DE_SERVICIO
    h.reactivar()
    assert h.estado == EstadoHabitacion.PENDIENTE_DE_LIMPIEZA


def test_no_se_saca_de_servicio_una_habitacion_ocupada():
    with pytest.raises(TransicionInvalidaError):
        Habitacion("A", "101", "C1", EstadoHabitacion.OCUPADA).marcar_fuera_de_servicio()


# ----- categoría (cupo)
def test_reservar_y_liberar_cupo():
    c = CategoriaHabitacion("C1", "Estándar", Decimal("1000"), 5)
    c.reservar_cupo(5)
    assert c.cupo_disponible == 0
    c.liberar_cupo(2)
    assert c.cupo_disponible == 2


def test_no_se_reserva_mas_cupo_del_disponible():
    c = CategoriaHabitacion("C1", "Estándar", Decimal("1000"), 2)
    with pytest.raises(SinCupoError):
        c.reservar_cupo(3)
    assert c.cupo_disponible == 2


@pytest.mark.parametrize("cantidad", [0, -1])
def test_cantidades_de_cupo_invalidas(cantidad):
    c = CategoriaHabitacion("C1", "Estándar", Decimal("1000"), 2)
    with pytest.raises(DatoInvalidoError):
        c.reservar_cupo(cantidad)
    with pytest.raises(DatoInvalidoError):
        c.liberar_cupo(cantidad)


# ----- value objects
def test_linea_reservacion_valida_cantidad_y_calcula_subtotal():
    assert LineaReservacion("C1", 3, Decimal("428.00")).subtotal == Decimal("1284.00")
    with pytest.raises(DatoInvalidoError):
        LineaReservacion("C1", 0, Decimal("1"))
    with pytest.raises(DatoInvalidoError):
        LineaReservacion("C1", 1, Decimal("-1"))


def test_garantia_exige_tipo_y_referencia():
    assert Garantia("tarjeta", "TC-1").tipo == "tarjeta"
    with pytest.raises(DatoInvalidoError):
        Garantia("", "TC-1")
    with pytest.raises(DatoInvalidoError):
        Garantia("tarjeta", "  ")


# ----- cuenta de estancia
def cuenta_con_hospedaje(monto="3000"):
    return CuentaEstancia.abrir("CTA-1", "R1", Decimal(monto), AHORA)


def test_abrir_cuenta_registra_el_hospedaje_como_primer_cargo():
    c = cuenta_con_hospedaje()
    assert c.total == Decimal("3000") and c.saldo == Decimal("3000") and c.abierta


def test_cerrar_cuenta_liquidada():
    c = cuenta_con_hospedaje()
    c.registrar_pago(Decimal("3000"))
    c.cerrar()
    assert not c.abierta


def test_no_se_cierra_con_saldo_pendiente():
    c = cuenta_con_hospedaje()
    c.registrar_pago(Decimal("1000"))
    with pytest.raises(CuentaError, match="saldo pendiente"):
        c.cerrar()
    assert c.abierta


def test_cargo_en_cuenta_cerrada_se_rechaza():
    c = cuenta_con_hospedaje("0.01")
    c.registrar_pago(Decimal("0.01"))
    c.cerrar()
    with pytest.raises(CuentaError):
        c.registrar_cargo("Minibar", Decimal("50"), "E1", AHORA)
    with pytest.raises(CuentaError):
        c.registrar_pago(Decimal("1"))
    with pytest.raises(CuentaError):
        c.cerrar()


@pytest.mark.parametrize("monto", ["0", "-5"])
def test_cargo_debe_ser_mayor_a_cero(monto):
    with pytest.raises(DatoInvalidoError):
        cuenta_con_hospedaje().registrar_cargo("Minibar", Decimal(monto), "E1", AHORA)


def test_pago_negativo_se_rechaza():
    with pytest.raises(DatoInvalidoError):
        cuenta_con_hospedaje().registrar_pago(Decimal("-1"))


def test_total_suma_todos_los_cargos():
    c = cuenta_con_hospedaje()
    c.registrar_cargo("Restaurante", Decimal("250.50"), "E1", AHORA)
    assert c.total == Decimal("3250.50")
