"""Implementación en memoria de los contratos (pruebas, demostración y desarrollo local)."""
import copy

from ..application.puertos import PublicadorDeEventos, UnidadDeTrabajo
from ..domain.errores import NoEncontradoError
from ..domain.repositorios import (RepositorioDeCategorias, RepositorioDeCuentas,
                                   RepositorioDeHabitaciones, RepositorioDeHuespedes,
                                   RepositorioDeReservaciones)


class Almacen:
    def __init__(self):
        self.huespedes = {}
        self.categorias = {}
        self.habitaciones = {}
        self.reservaciones = {}
        self.cuentas = {}

    def _colecciones(self):
        return (self.huespedes, self.categorias, self.habitaciones, self.reservaciones,
                self.cuentas)

    def respaldar(self):
        return copy.deepcopy(self._colecciones())

    def restaurar(self, respaldo):
        for actual, guardado in zip(self._colecciones(), respaldo):
            actual.clear()
            actual.update(guardado)


def _obtener(coleccion, clave, nombre):
    if clave not in coleccion:
        raise NoEncontradoError(f"No existe {nombre} '{clave}'")
    return coleccion[clave]


class _RepoBase:
    nombre = "el elemento"
    campo = ""

    def __init__(self, almacen):
        self._coleccion = getattr(almacen, self.campo)

    def obtener(self, clave):
        return _obtener(self._coleccion, clave, self.nombre)

    def guardar(self, entidad):
        self._coleccion[entidad.id] = entidad

    def listar(self):
        return list(self._coleccion.values())


class RepositorioDeHuespedesEnMemoria(_RepoBase, RepositorioDeHuespedes):
    nombre, campo = "el huésped", "huespedes"


class RepositorioDeCategoriasEnMemoria(_RepoBase, RepositorioDeCategorias):
    nombre, campo = "la categoría", "categorias"


class RepositorioDeHabitacionesEnMemoria(_RepoBase, RepositorioDeHabitaciones):
    nombre, campo = "la habitación", "habitaciones"


class RepositorioDeReservacionesEnMemoria(_RepoBase, RepositorioDeReservaciones):
    nombre, campo = "la reservación", "reservaciones"


class RepositorioDeCuentasEnMemoria(RepositorioDeCuentas):
    def __init__(self, almacen):
        self._coleccion = almacen.cuentas

    def obtener_por_reservacion(self, reservacion_id):
        for cuenta in self._coleccion.values():
            if cuenta.reservacion_id == reservacion_id:
                return cuenta
        raise NoEncontradoError(f"No hay cuenta de estancia para la reservación '{reservacion_id}'")

    def guardar(self, cuenta):
        self._coleccion[cuenta.id] = cuenta


class UnidadDeTrabajoEnMemoria(UnidadDeTrabajo):
    def __init__(self, almacen):
        self._almacen = almacen
        self._confirmado = False
        self._respaldo = None

    def __enter__(self):
        self._respaldo = self._almacen.respaldar()
        self._confirmado = False
        self.huespedes = RepositorioDeHuespedesEnMemoria(self._almacen)
        self.categorias = RepositorioDeCategoriasEnMemoria(self._almacen)
        self.habitaciones = RepositorioDeHabitacionesEnMemoria(self._almacen)
        self.reservaciones = RepositorioDeReservacionesEnMemoria(self._almacen)
        self.cuentas = RepositorioDeCuentasEnMemoria(self._almacen)
        return self

    def guardar_cambios(self):
        self._confirmado = True

    def __exit__(self, tipo, valor, traza):
        if not self._confirmado:  # rechazo o error: se deshace todo
            self._almacen.restaurar(self._respaldo)
        return False


class PublicadorEnMemoria(PublicadorDeEventos):
    def __init__(self):
        self.eventos = []

    def publicar(self, evento):
        self.eventos.append(evento)
