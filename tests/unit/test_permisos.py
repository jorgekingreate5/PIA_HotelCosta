import pytest

from src.application.permisos import PERMISOS, convertir_rol, exigir_permiso
from src.domain.errores import PermisoDenegadoError
from src.domain.valor import Rol


@pytest.mark.parametrize("rol,accion", [
    ("RESERVACIONES", "confirmar_reservacion"), ("RECEPCION", "realizar_check_in"),
    ("LIMPIEZA", "marcar_habitacion_disponible"), ("ADMINISTRACION", "ver_reporte_ocupacion"),
    ("recepcion", "registrar_cargo")])
def test_roles_con_permiso(rol, accion):
    assert exigir_permiso(rol, accion) == Rol(rol.upper())


@pytest.mark.parametrize("rol,accion", [
    ("RECEPCION", "marcar_habitacion_disponible"), ("LIMPIEZA", "realizar_check_out"),
    ("RESERVACIONES", "realizar_check_in"), ("RECEPCION", "ver_reporte_ocupacion"),
    ("LIMPIEZA", "marcar_fuera_de_servicio")])
def test_roles_sin_permiso(rol, accion):
    with pytest.raises(PermisoDenegadoError):
        exigir_permiso(rol, accion)


@pytest.mark.parametrize("rol", [None, "", "HUESPED", "admin"])
def test_rol_desconocido_se_rechaza(rol):
    with pytest.raises(PermisoDenegadoError, match="Rol desconocido"):
        convertir_rol(rol)


def test_toda_accion_tiene_al_menos_un_rol():
    assert all(len(roles) >= 1 for roles in PERMISOS.values())
