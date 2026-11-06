"""La pantalla sencilla para clientes existe y llama a los endpoints reales de la API."""
import re
from pathlib import Path

PANEL = Path(__file__).resolve().parents[2] / "src" / "api" / "static" / "panel.html"
APP = Path(__file__).resolve().parents[2] / "src" / "api" / "app.py"


def test_el_panel_existe_y_tiene_titulo():
    texto = PANEL.read_text(encoding="utf-8")
    assert "Hotel Costa Azul" in texto and "<script>" in texto


def test_el_panel_solo_usa_rutas_que_la_api_define():
    texto = PANEL.read_text(encoding="utf-8")
    definidas = set(re.findall(r'@app\.(?:get|post)\("([^"]+)"', APP.read_text(encoding="utf-8")))
    usadas = set(re.findall(r'api\("(?:GET|POST)","(/[a-z-]+)', texto))
    base = {m.group(0) for m in (re.match(r"/[a-z-]+", d) for d in definidas) if m}
    assert usadas and usadas <= base
