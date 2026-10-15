# Análisis Nuclei — dashboard-musica-backend

- **Fecha:** 2026-10-14
- **Herramienta:** Nuclei v3.11.1, templates v10.5.0 (11,144 templates), contenedor `projectdiscovery/nuclei:latest`
- **Método:** el backend corrió en un contenedor (imagen construida con el `Dockerfile` del repo) dentro de la red Docker del lab (`ldap-keycloak-oauth2-lab_auth-network`), y el contenedor de Nuclei se conectó a esa misma red.
- **Conectividad:** `http://dashboard-backend:8001` respondió HTTP 404 en `/`, lo cual es normal porque no hay ruta raíz. El escaneo terminó en 2 minutos sin errores de conexión; los "Errors: 232" del log son timeouts y respuestas 4xx de templates que no aplican.
- **Scripts usados:** `run-nuclei.ps1` y `run-nuclei-resto.ps1` (están en el repo `ldap-keycloak-oauth2-lab/nuclei-results`).

## Resultados del escaneo del servicio (14 hallazgos)

| # | Severidad | Template | Ruta | Comentario |
|---|---|---|---|---|
| 1 | info | `swagger-api` | `/docs` | Swagger UI público. |
| 2 | info | `openapi` | `/openapi.json` | Esquema de la API público (expone endpoints y modelos). |
| 3 | info | `redoc-api-docs` | `/redoc` | ReDoc público. |
| 4 | info | `http-missing-security-headers` ×10 | `/` | Faltan CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, COEP, CORP y X-Permitted-Cross-Domain-Policies. |
| 5 | info | `tech-detect:uvicorn` | `/` | El header `server: uvicorn` revela la tecnología. |

## Resultados del escaneo de código (`-file`, 8 coincidencias)

| Archivo | Template | Severidad | ¿Real? |
|---|---|---|---|
| `app/main.py` | `dom-invader-xss:sink` (`fetch`) | high | Falso positivo: es Python y no hay DOM. El patrón coincide con el nombre de la función `_fetch_jwks`. |
| `app/main.py` | `credentials-disclosure-file` | unknown | Parcial: son nombres de variables, pero el código **imprime en consola el header `Authorization` y parte del JWT** (`print(...)` en `current_user`), lo que filtra tokens a los logs. |
| `README.md` | `credentials-disclosure-file` | unknown | **Sí.** Credenciales de ejemplo (`alice` / `alice123`) en los comandos curl. |
| `.git/hooks/fsmonitor-watchman.sample` | `credentials-disclosure-file` | unknown | Falso positivo: archivo de ejemplo de Git. |
| `nuclei-results/*` | varios | — | Ruido: Nuclei escaneó sus propios reportes. |

Detalle completo en `nuclei-report.txt` / `.jsonl`, `nuclei-file-report.txt` / `.jsonl` y `markdown/`.
