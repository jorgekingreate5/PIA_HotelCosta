"""Los 120 casos y las 20 transiciones del PIA, con un oráculo calculado directo de los CSV."""
import csv
from collections import Counter
from decimal import Decimal
from pathlib import Path

from src.infrastructure.composicion import crear_contenedor
from src.infrastructure.configuracion import Configuracion
from src.infrastructure.datos_pia import DatosPIA, cargar_datos, ejecutar_casos_de_prueba
from src.infrastructure.ejecucion_pia import ejecutar_transiciones

CARPETA = Path(__file__).resolve().parent.parent.parent / "datos"


def filas(nombre):
    with open(CARPETA / nombre, encoding="utf-8-sig", newline="") as archivo:
        return list(csv.DictReader(archivo))


def operaciones_esperadas():
    """Oráculo: aplica las reglas del PIA sobre las filas crudas, sin usar el dominio."""
    actores = {f["actor_id"]: f for f in filas("actores.csv")}
    catalogo = {f["recurso_id"]: f for f in filas("catalogo.csv")}
    detalle = {}
    for f in filas("detalle_operaciones.csv"):
        detalle.setdefault(f["operacion_id"], []).append(f)
    esperado = {}
    for op in filas("operaciones.csv"):
        lineas = detalle.get(op["operacion_id"], [])
        actor = actores[op["actor_id"]]
        total = sum(Decimal(catalogo[x["recurso_id"]]["precio_mxn"]) * int(x["cantidad"])
                    for x in lineas)
        por_categoria = Counter()
        for x in lineas:
            por_categoria[x["recurso_id"]] += int(x["cantidad"])
        confirmable = (
            actor["activo"] == "1" and len(lineas) > 0 and op["autorizado"] == "1"
            and all(catalogo[c]["habilitado"] == "1" and n <= int(catalogo[c]["capacidad_o_stock"])
                    for c, n in por_categoria.items()))
        esperado[op["operacion_id"]] = {
            "procesable": actor["activo"] == "1" and len(lineas) > 0 and op["autorizado"] == "1",
            "beneficio": actor["es_preferente"] == "1" and total >= 1500
            and op["promocion_activa"] == "0",
            "confirmable": confirmable,
        }
    return esperado


def test_el_paquete_trae_las_cantidades_esperadas():
    datos = DatosPIA(CARPETA)
    assert len(datos.huespedes()) == 40
    assert len(datos.categorias()) == 20
    assert len(datos.reservaciones()) == 60
    assert len(datos.casos) == 120
    assert len(datos.transiciones) == 20


def test_el_hotel_demo_tiene_120_habitaciones_distintas():
    habitaciones = DatosPIA(CARPETA).habitaciones(6)
    assert len(habitaciones) == 120
    assert len({h.numero for h in habitaciones}) == 120


def test_total_de_las_reservaciones_es_la_suma_de_precio_por_cantidad():
    reservaciones = {r.id: r for r in DatosPIA(CARPETA).reservaciones()}
    assert reservaciones["HOT-O001"].total == sum(
        (x.tarifa * x.cantidad for x in reservaciones["HOT-O001"].lineas), Decimal("0"))
    sin_detalle = [r.id for r in reservaciones.values() if not r.lineas]
    assert len(sin_detalle) == 2


def test_los_120_casos_coinciden_con_el_oraculo():
    esperado = operaciones_esperadas()
    resultados = ejecutar_casos_de_prueba(DatosPIA(CARPETA))
    assert len(resultados) == 120
    for r in resultados:
        op = esperado[r["operacion_id"]]
        if r["tipo_prueba"] == "validar_operacion":
            assert (r["resultado"] == "CUMPLE") == op["procesable"], r["caso_id"]
        else:
            assert (r["resultado"] == "APLICA") == op["beneficio"], r["caso_id"]


def test_los_casos_no_cumplen_explican_el_motivo():
    resultados = ejecutar_casos_de_prueba(DatosPIA(CARPETA))
    no_cumplen = [r for r in resultados if r["resultado"] == "NO CUMPLE"]
    assert no_cumplen and all(r["detalle"] for r in no_cumplen)


def test_hay_casos_de_cada_resultado_posible():
    resultados = Counter(r["resultado"] for r in ejecutar_casos_de_prueba(DatosPIA(CARPETA)))
    assert set(resultados) == {"CUMPLE", "NO CUMPLE", "APLICA", "NO APLICA"}


def test_las_20_transiciones_coinciden_con_el_oraculo():
    esperado = operaciones_esperadas()
    resultados = ejecutar_transiciones(CARPETA)
    assert len(resultados) == 20
    for r in resultados:
        op, accion = esperado[r["operacion_id"]], r["accion"]
        if accion in ("aprobar", "completar"):
            assert (r["resultado"] == "OK") == op["confirmable"], r["caso_id"]
            assert r["estado_final"] == ("CHECK_OUT" if accion == "completar" and r["resultado"] == "OK"
                                         else "CONFIRMADA" if r["resultado"] == "OK" else "SOLICITADA")
        elif accion == "cancelar":
            assert r["resultado"] == "OK" and r["estado_final"] == "CANCELADA"
        else:  # repetir_aprobacion y saltar_estado siempre terminan rechazadas
            assert r["resultado"] == "RECHAZADA", r["caso_id"]
            assert "TransicionInvalidaError" in r["detalle"] or not op["confirmable"]


def test_saltar_estado_es_siempre_una_transicion_invalida():
    for r in ejecutar_transiciones(CARPETA):
        if r["accion"] == "saltar_estado":
            assert "TransicionInvalidaError" in r["detalle"]
            assert r["estado_final"] == "SOLICITADA"


def test_cargar_datos_en_el_contenedor_y_consultar():
    c = crear_contenedor(Configuracion())
    cargar_datos(c.nueva_uow, DatosPIA(CARPETA))
    assert len(c.consultas.consultar_categorias("RECEPCION")) == 20
    assert len(c.consultas.estatus_de_habitaciones("RECEPCION")) == 120
    assert len(c.consultas.listar_reservaciones("RESERVACIONES")) == 60


def test_el_contenedor_puede_cargar_los_datos_demo_al_arrancar():
    c = crear_contenedor(Configuracion(cargar_datos_demo=True, ruta_datos=str(CARPETA)))
    assert len(c.consultas.estatus_de_habitaciones("RECEPCION")) == 120
