"""Carga y ejecución de los datos ficticios del PIA (CSV UTF-8 con BOM)."""
import csv
from datetime import date
from decimal import Decimal
from pathlib import Path

from ..domain.categoria import CategoriaHabitacion
from ..domain.especificaciones import (ContextoDeReservacion, beneficio_preferente,
                                       explicar_incumplimiento, puede_procesarse)
from ..domain.habitacion import Habitacion
from ..domain.huesped import Huesped
from ..domain.reservacion import Reservacion
from ..domain.valor import LineaReservacion


def leer_csv(ruta):
    with open(ruta, encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


class DatosPIA:
    """Datos del paquete convertidos a objetos de dominio."""

    def __init__(self, carpeta="datos"):
        carpeta = Path(carpeta)
        self.filas_actores = leer_csv(carpeta / "actores.csv")
        self.filas_catalogo = leer_csv(carpeta / "catalogo.csv")
        self.filas_operaciones = leer_csv(carpeta / "operaciones.csv")
        self.filas_detalle = leer_csv(carpeta / "detalle_operaciones.csv")
        self.casos = leer_csv(carpeta / "casos_prueba.csv")
        self.transiciones = leer_csv(carpeta / "transiciones_prueba.csv")

    def huespedes(self):
        return [Huesped(f["actor_id"], f["nombre"], f["es_preferente"] == "1",
                        f["activo"] == "1", f["ciudad"]) for f in self.filas_actores]

    def categorias(self):
        return [CategoriaHabitacion(f["recurso_id"], f["descripcion"], Decimal(f["precio_mxn"]),
                                    int(f["capacidad_o_stock"]), f["habilitado"] == "1")
                for f in self.filas_catalogo]

    def habitaciones(self, por_categoria=6):
        habitaciones, numero = [], 100
        for fila in self.filas_catalogo:
            for _ in range(por_categoria):
                numero += 1
                habitaciones.append(Habitacion(f"HAB-{numero}", str(numero), fila["recurso_id"]))
        return habitaciones

    def reservaciones(self):
        tarifas = {f["recurso_id"]: Decimal(f["precio_mxn"]) for f in self.filas_catalogo}
        lineas = {}
        for f in self.filas_detalle:
            lineas.setdefault(f["operacion_id"], []).append(
                LineaReservacion(f["recurso_id"], int(f["cantidad"]), tarifas[f["recurso_id"]]))
        return [Reservacion(f["operacion_id"], f["actor_id"], lineas.get(f["operacion_id"], []),
                            referencia=f["referencia"],
                            fecha_solicitud=date.fromisoformat(f["fecha_solicitud"]),
                            autorizada=f["autorizado"] == "1",
                            promocion_activa=f["promocion_activa"] == "1")
                for f in self.filas_operaciones]


def cargar_datos(nueva_uow, datos, habitaciones_por_categoria=6):
    """Guarda huéspedes, categorías, habitaciones y reservaciones usando la unidad de trabajo."""
    with nueva_uow() as uow:
        for entidad in datos.huespedes():
            uow.huespedes.guardar(entidad)
        for entidad in datos.categorias():
            uow.categorias.guardar(entidad)
        for entidad in datos.habitaciones(habitaciones_por_categoria):
            uow.habitaciones.guardar(entidad)
        for entidad in datos.reservaciones():
            uow.reservaciones.guardar(entidad)
        uow.guardar_cambios()


def ejecutar_casos_de_prueba(datos, umbral=Decimal("1500")):
    """Evalúa los 120 casos (validar_operacion y evaluar_beneficio) con las Specifications."""
    huespedes = {h.id: h for h in datos.huespedes()}
    reservaciones = {r.id: r for r in datos.reservaciones()}
    resultados = []
    for caso in datos.casos:
        reservacion = reservaciones[caso["operacion_id"]]
        contexto = ContextoDeReservacion(reservacion, huespedes[reservacion.huesped_id], {})
        if caso["tipo_prueba"] == "validar_operacion":
            cumple = puede_procesarse().es_satisfecha_por(contexto)
            detalle = "" if cumple else explicar_incumplimiento(contexto)
            resultado = "CUMPLE" if cumple else "NO CUMPLE"
        else:
            aplica = beneficio_preferente(umbral).es_satisfecha_por(contexto)
            resultado = "APLICA" if aplica else "NO APLICA"
            detalle = f"total={reservacion.total}"
        resultados.append({"caso_id": caso["caso_id"], "operacion_id": caso["operacion_id"],
                           "tipo_prueba": caso["tipo_prueba"], "resultado": resultado,
                           "detalle": detalle})
    return resultados
