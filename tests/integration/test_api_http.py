"""Pruebas de la API con TestClient de FastAPI (contenedor en memoria con los datos del PIA)."""
import csv
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api.app import crear_app
from src.infrastructure.composicion import crear_contenedor
from src.infrastructure.configuracion import Configuracion

CARPETA = Path(__file__).resolve().parent.parent.parent / "datos"
RES = {"X-Rol": "RESERVACIONES"}
REC = {"X-Rol": "RECEPCION"}
LIM = {"X-Rol": "LIMPIEZA"}
ADM = {"X-Rol": "ADMINISTRACION"}


def huesped_activo():
    with open(CARPETA / "actores.csv", encoding="utf-8-sig", newline="") as archivo:
        return next(f["actor_id"] for f in csv.DictReader(archivo) if f["activo"] == "1")


@pytest.fixture()
def cliente():
    contenedor = crear_contenedor(Configuracion(cargar_datos_demo=True, ruta_datos=str(CARPETA)))
    return TestClient(crear_app(contenedor))


def crear_reservacion(cliente, cantidad=2, categoria="HOT-P001"):
    respuesta = cliente.post("/reservaciones", headers=RES, json={
        "huesped_id": huesped_activo(), "lineas": [{"categoria_id": categoria, "cantidad": cantidad}]})
    assert respuesta.status_code == 201
    return respuesta.json()["id"]


def llegar_a_estancia(cliente, referencia="TC-0001"):
    rid = crear_reservacion(cliente)
    assert cliente.post(f"/reservaciones/{rid}/autorizar", headers=RES).status_code == 200
    assert cliente.post(f"/reservaciones/{rid}/confirmar", headers=RES).status_code == 200
    return rid, {"habitacion_id": "HAB-101", "identidad_verificada": True,
                 "garantia": {"tipo": "tarjeta", "referencia": referencia}}


def test_salud_y_documentacion_openapi(cliente):
    assert cliente.get("/health").json() == {"estado": "ok"}
    assert cliente.get("/openapi.json").status_code == 200
    assert cliente.get("/docs").status_code == 200


def test_catalogo_requiere_un_rol_valido(cliente):
    assert cliente.get("/categorias").status_code == 403
    assert cliente.get("/categorias", headers={"X-Rol": "HUESPED"}).status_code == 403
    respuesta = cliente.get("/categorias", headers=RES)
    assert respuesta.status_code == 200 and len(respuesta.json()) == 20


def test_solicitud_invalida_responde_422(cliente):
    respuesta = cliente.post("/reservaciones", headers=RES, json={
        "huesped_id": "x", "lineas": [{"categoria_id": "HOT-P001", "cantidad": 0}]})
    assert respuesta.status_code == 422
    assert cliente.post("/reservaciones", headers=RES,
                        json={"huesped_id": "x", "lineas": []}).status_code == 422


def test_reservacion_inexistente_responde_404(cliente):
    assert cliente.get("/reservaciones/NO-EXISTE", headers=RES).status_code == 404


def test_recepcion_no_puede_solicitar_reservaciones(cliente):
    respuesta = cliente.post("/reservaciones", headers=REC, json={
        "huesped_id": huesped_activo(), "lineas": [{"categoria_id": "HOT-P001", "cantidad": 1}]})
    assert respuesta.status_code == 403


def test_confirmar_sin_autorizar_es_422_y_luego_funciona(cliente):
    rid = crear_reservacion(cliente)
    respuesta = cliente.post(f"/reservaciones/{rid}/confirmar", headers=RES)
    assert respuesta.status_code == 422 and "autorizada" in respuesta.json()["detalle"]
    consulta = cliente.get(f"/reservaciones/{rid}", headers=RES).json()
    assert consulta["requiere_revision"] is True
    cliente.post(f"/reservaciones/{rid}/autorizar", headers=RES)
    assert cliente.post(f"/reservaciones/{rid}/confirmar", headers=RES).json()["estado"] == "CONFIRMADA"


def test_confirmar_dos_veces_es_409(cliente):
    rid, _ = llegar_a_estancia(cliente)
    assert cliente.post(f"/reservaciones/{rid}/confirmar", headers=RES).status_code == 409


def test_sin_cupo_es_409(cliente):
    rid = crear_reservacion(cliente, cantidad=99)
    cliente.post(f"/reservaciones/{rid}/autorizar", headers=RES)
    assert cliente.post(f"/reservaciones/{rid}/confirmar", headers=RES).status_code == 409


def test_flujo_completo_por_http(cliente):
    rid, check_in = llegar_a_estancia(cliente)
    assert cliente.post(f"/reservaciones/{rid}/check-in", headers=REC, json=check_in).status_code == 200
    cargo = {"concepto": "Restaurante", "monto": "250.00", "empleado_id": "E1"}
    assert cliente.post(f"/reservaciones/{rid}/cargos", headers=REC, json=cargo).status_code == 201
    cuenta = cliente.get(f"/reservaciones/{rid}/cuenta", headers=REC).json()
    pendiente = cliente.post(f"/reservaciones/{rid}/check-out", headers=REC, json={"monto_pagado": "10"})
    assert pendiente.status_code == 409
    pago = {"monto_pagado": cuenta["total"]}
    assert cliente.post(f"/reservaciones/{rid}/check-out", headers=REC, json=pago).status_code == 200
    assert cliente.post("/habitaciones/HAB-101/limpieza-terminada", headers=REC).status_code == 403
    assert cliente.post("/habitaciones/HAB-101/limpieza-terminada", headers=LIM).status_code == 200
    estados = {h["id"]: h["estado"] for h in cliente.get("/habitaciones", headers=REC).json()}
    assert estados["HAB-101"] == "DISPONIBLE"
    reporte = cliente.get("/reportes/ocupacion", headers=ADM).json()
    assert reporte["habitaciones_total"] == 120
    assert cliente.get("/reportes/ocupacion", headers=REC).status_code == 403
    eventos = cliente.get("/eventos", headers=ADM).json()
    assert any(e["evento"] == "HabitacionDisponible" for e in eventos)


def test_cambio_de_habitacion_y_historial(cliente):
    rid, check_in = llegar_a_estancia(cliente)
    cliente.post(f"/reservaciones/{rid}/check-in", headers=REC, json=check_in)
    cambio = {"nueva_habitacion_id": "HAB-102", "motivo": "Ruido", "responsable": "E1"}
    assert cliente.post(f"/reservaciones/{rid}/cambio-habitacion", headers=REC, json=cambio).status_code == 200
    historial = cliente.get(f"/reservaciones/{rid}/historial-cambios", headers=REC).json()
    assert historial[0]["origen_id"] == "HAB-101" and historial[0]["destino_id"] == "HAB-102"


def test_garantia_rechazada_es_422_y_timeout_es_503(cliente):
    rid, check_in = llegar_a_estancia(cliente, referencia="TC-1-RECHAZADA")
    assert cliente.post(f"/reservaciones/{rid}/check-in", headers=REC, json=check_in).status_code == 422
    check_in["garantia"]["referencia"] = "TC-1-TIMEOUT"
    assert cliente.post(f"/reservaciones/{rid}/check-in", headers=REC, json=check_in).status_code == 503


def test_listar_cancelar_y_no_show(cliente):
    rid, _ = llegar_a_estancia(cliente)
    assert cliente.get("/reservaciones", headers=RES, params={"estado": "CONFIRMADA"}).json()
    assert cliente.post(f"/reservaciones/{rid}/no-show", headers=REC).json()["estado"] == "NO_SHOW"
    otro = crear_reservacion(cliente)
    assert cliente.post(f"/reservaciones/{otro}/cancelar", headers=RES).json()["estado"] == "CANCELADA"


def test_fuera_de_servicio_y_reactivar(cliente):
    assert cliente.post("/habitaciones/HAB-110/fuera-de-servicio", headers=ADM).status_code == 200
    assert cliente.post("/habitaciones/HAB-110/fuera-de-servicio", headers=REC).status_code == 403
    assert cliente.post("/habitaciones/HAB-110/reactivar", headers=ADM).json()["estado"] == "PENDIENTE_DE_LIMPIEZA"


# ----- CAMBIO PIA: reglas de la Actividad 5 (tope de crédito y cancelación a 48 h)
def test_cargo_sobre_el_tope_da_409_y_con_autorizacion_da_201(cliente):
    rid, check_in = llegar_a_estancia(cliente)
    assert cliente.post(f"/reservaciones/{rid}/check-in", headers=REC, json=check_in).status_code == 200
    cargo = {"concepto": "Spa", "monto": "3000.01", "empleado_id": "E1"}
    r = cliente.post(f"/reservaciones/{rid}/cargos", headers=REC, json=cargo)
    assert r.status_code == 409 and r.json()["error"] == "CreditoExcedidoError"
    cargo["autorizacion_administracion"] = True
    assert cliente.post(f"/reservaciones/{rid}/cargos", headers=REC, json=cargo).status_code == 201


def test_cancelacion_tardia_cobra_penalidad_y_la_excepcion_la_exenta(cliente):
    tardia = {"fecha_llegada": "2020-01-01T00:00:00"}
    rid, _ = llegar_a_estancia(cliente)
    r = cliente.post(f"/reservaciones/{rid}/cancelar", headers=RES, json=tardia)
    assert r.status_code == 200 and r.json()["penalidad_cancelacion"] != "0.00"
    otro, _ = llegar_a_estancia(cliente)
    r = cliente.post(f"/reservaciones/{otro}/cancelar", headers=RES,
                     json={**tardia, "autorizacion_jefe": True})
    assert r.json()["penalidad_cancelacion"] == "0.00"


def test_pantalla_sencilla_en_la_raiz(cliente):  # CAMBIO PIA
    r = cliente.get("/")
    assert r.status_code == 200
    assert "Hotel Costa Azul" in r.text
