# ---- base: dependencias de ejecución
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# ---- test: agrega herramientas de prueba y el código de pruebas
FROM base AS test
RUN pip install --no-cache-dir -r requirements-dev.txt
COPY pyproject.toml ./
COPY src ./src
COPY datos ./datos
COPY tests ./tests
COPY docs/matriz_trazabilidad.csv ./docs/matriz_trazabilidad.csv
COPY docs/historias_usuario.md ./docs/historias_usuario.md
CMD ["python", "-m", "pytest", "-v"]

# ---- runtime: imagen final de la API (sin herramientas de prueba)
FROM base AS runtime
COPY src ./src
COPY datos ./datos
RUN useradd --create-home appuser
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "uvicorn src.api.app:obtener_app --factory --host 0.0.0.0 --port ${PORT:-8000}"]
