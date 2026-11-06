"""Quién puede hacer qué (supuesto de diseño por validar con el negocio)."""
from ..domain.errores import PermisoDenegadoError
from ..domain.valor import Rol

R = Rol
TODOS = frozenset(Rol)

PERMISOS = {
    "consultar_catalogo": TODOS,
    "consultar_reservacion": TODOS,
    "solicitar_reservacion": frozenset({R.RESERVACIONES}),
    "autorizar_reservacion": frozenset({R.RESERVACIONES}),
    "confirmar_reservacion": frozenset({R.RESERVACIONES}),
    "cancelar_reservacion": frozenset({R.RESERVACIONES}),
    "registrar_no_show": frozenset({R.RESERVACIONES, R.RECEPCION}),
    "realizar_check_in": frozenset({R.RECEPCION}),
    "registrar_cargo": frozenset({R.RECEPCION}),
    "cambiar_habitacion": frozenset({R.RECEPCION}),
    "realizar_check_out": frozenset({R.RECEPCION}),
    "consultar_cuenta": frozenset({R.RECEPCION, R.ADMINISTRACION}),
    "ver_estatus_habitaciones": TODOS,
    "marcar_habitacion_disponible": frozenset({R.LIMPIEZA}),
    "marcar_fuera_de_servicio": frozenset({R.ADMINISTRACION}),
    "reactivar_habitacion": frozenset({R.ADMINISTRACION}),
    "ver_reporte_ocupacion": frozenset({R.ADMINISTRACION}),
    "ver_eventos": frozenset({R.ADMINISTRACION}),
}


def convertir_rol(rol):
    try:
        return Rol(str(rol).upper())
    except ValueError:
        raise PermisoDenegadoError(f"Rol desconocido: {rol!r}") from None


def exigir_permiso(rol, accion):
    rol = convertir_rol(rol)
    if rol not in PERMISOS[accion]:
        raise PermisoDenegadoError(f"El rol {rol.value} no puede ejecutar '{accion}'")
    return rol
