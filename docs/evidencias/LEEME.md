# Evidencias

| Archivo | Qué es |
|---|---|
| `resultados_casos_prueba.csv` | Resultado de los 120 casos (validar_operacion y evaluar_beneficio) ejecutados sobre el sistema. |
| `resultados_transiciones.csv` | Resultado de las 20 transiciones (aprobar, completar, cancelar, repetir_aprobacion, saltar_estado). |

Se generan con `python scripts/ejecutar_casos_pia.py`. La prueba `tests/unit/test_datos_pia.py` compara ambos resultados contra un cálculo independiente hecho directamente sobre los CSV.

Capturas que debe agregar el equipo (no se pueden generar desde el repositorio): pytest en verde con cobertura, GitHub Actions en verde, Docker Compose levantado, `/docs` de la API, despliegue en Render y llamadas de ejemplo.
