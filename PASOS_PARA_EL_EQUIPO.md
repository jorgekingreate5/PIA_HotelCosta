# Pasos para el equipo antes de entregar

Este proyecto se preparó en un entorno sin FastAPI, SQLAlchemy, Ruff ni Docker (ver `docs/CAMBIOS_RESPECTO_A_ENTREGA_ANTERIOR.md`). Lo verificado allí: 186 pruebas unitarias en verde. Lo siguiente hay que hacerlo en su equipo (PowerShell, un comando a la vez).

1. **Entorno** (desde la carpeta del proyecto):
   ```
   py -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
   ```
   Si algún paquete no instala con su versión de Python, usen Python 3.12 o 3.13.
2. **Pruebas y cobertura:**
   ```
   .\.venv\Scripts\python.exe -m pytest -v --cov=src --cov-report=term-missing --cov-fail-under=80
   .\.venv\Scripts\python.exe -m ruff check src tests scripts
   ```
   Se esperan unas 209 pruebas. Capturen la salida (evidencias P1 y P2 del informe). Si falla una de `tests/integration`, revisen primero las versiones de FastAPI (con Pydantic 2) y SQLAlchemy 2.
3. **Docker:** `copy .env.example .env`, cambien `POSTGRES_PASSWORD` y ejecuten `docker compose up --build`. Abran http://localhost:8000/docs y capturen (P4, P6). Después `docker compose --profile pruebas run --rm pruebas` (P5).
4. **GitHub:** creen el repositorio `hotel-costa-azul-cln` (vacío, sin README) y suban el proyecto. Para que el historial muestre a los tres integrantes, cada uno debe hacer al menos un commit con su propio usuario (por ejemplo, cada quien agrega su conclusión individual o corrige un documento). Comando base:
   ```
   git init
   git add .
   git commit -m "PIA: Hotel Costa Azul"
   git branch -M main
   git remote add origin https://github.com/jorgekingreate5/hotel-costa-azul-cln.git
   git push -u origin main
   ```
5. **GitHub Actions:** revisen que los trabajos `calidad-y-pruebas`, `integracion-postgres` e `imagen-docker` queden en verde y capturen (P3).
6. **Render:** New → Blueprint → su repositorio (usa `render.yaml`). Verifiquen `/health` y `/docs`, copien la URL pública al informe (sección 10 y "Link de GitHub"), a la presentación y al README (P7). Opcional: guardar el Deploy Hook como secreto `RENDER_DEPLOY_HOOK_URL`.
7. **Informe y presentación** (`entregables/`): peguen las capturas P1–P8 donde dicen "CAPTURA PENDIENTE", pongan la URL pública y agreguen sus propios prompts en el apartado de uso de IA.
8. **Entender el código** antes de defenderlo: cada integrante debe poder explicar un caso de uso completo (servicio → dominio → repositorio → prueba) y las dos reglas nuevas (tope de crédito y penalidad de cancelación).
9. **Validar con el negocio** las preguntas abiertas del BRD (sección 12).
