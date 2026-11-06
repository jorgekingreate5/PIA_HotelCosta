# Despliegue y operación

## 1. Local con Docker Compose
```bash
cp .env.example .env          # cambia POSTGRES_PASSWORD
docker compose up --build     # levanta PostgreSQL y la API en http://localhost:8000
docker compose --profile pruebas run --rm pruebas   # ejecuta las pruebas contra PostgreSQL
docker compose down           # detener (agrega -v para borrar los datos)
```
- API: http://localhost:8000 · documentación interactiva: http://localhost:8000/docs · salud: http://localhost:8000/health
- Con `CARGAR_DATOS_DEMO=1` se cargan 40 huéspedes, 20 categorías, 120 habitaciones y 60 reservaciones.

## 2. Local sin Docker
```bash
python -m venv .venv && source .venv/bin/activate     # en Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
CARGAR_DATOS_DEMO=1 uvicorn src.api.app:obtener_app --factory --reload
```
Sin `DATABASE_URL` usa memoria; con `DATABASE_URL=sqlite+pysqlite:///hotel.sqlite3` persiste en un archivo.

## 3. Despliegue en Render
1. Sube el repositorio a GitHub.
2. En Render: **New → Blueprint** y elige el repositorio. Render lee `render.yaml`, crea la base PostgreSQL y la API con Docker.
3. Verifica `https://<tu-servicio>.onrender.com/health` y `/docs`.
4. Para despliegue automático desde GitHub Actions: en Render copia el *Deploy Hook* del servicio y guárdalo en GitHub como secreto `RENDER_DEPLOY_HOOK_URL` (Settings → Secrets and variables → Actions). El workflow lo usa solo en la rama main.

El plan gratuito de Render duerme el servicio tras un rato sin tráfico; la primera petición puede tardar.

## 4. CI/CD (GitHub Actions)
| Trabajo | Qué hace |
|---|---|
| calidad-y-pruebas | Ruff, pytest con cobertura mínima de 80% y reporte HTML como artefacto. |
| integracion-postgres | Pruebas de persistencia contra PostgreSQL real. |
| imagen-docker | Construye la imagen de producción. |
| despliegue | En main, dispara el despliegue en Render si existe el secreto. |

## 5. Seguridad básica
- Ningún secreto está en el código: contraseñas y URLs vienen del entorno; `.env` está en `.gitignore`.
- La imagen de producción corre con un usuario sin privilegios y no incluye herramientas de prueba.
- La autenticación real (JWT) está pendiente (ADR-008).
