# Dashboard Música Clásica — Backend (repo 2 de 3)

API FastAPI que guarda el listado de obras y **exige JWT como Bearer Token**
emitido por Keycloak (federado con LDAP del lab).

## Endpoints
| Método | Ruta | Auth | Descripción |
|---|---|---|---|
| GET | `/health` | no | healthcheck |
| GET | `/api/profile` | Bearer JWT | devuelve usuario del token |
| GET | `/api/items` | Bearer JWT | listado de obras |
| POST | `/api/items` | Bearer JWT | alta `{obra, compositor, epoca, anio, duracion_min}` |

Sin `Authorization: Bearer <JWT>` responde `401/403`. Con token válido
imprime en consola el header recibido (evidencia para el video).

## Correr local (requiere lab levantado en :8081)
```bash
pip install -r requirements.txt
uvicorn app.main:app --port 8001
# probar:
curl http://localhost:8001/health
```

## Probar con token LDAP (alice/alice123)
```bash
$TOKEN=$(curl -s -X POST http://localhost:8081/realms/cybersecurity/protocol/openid-connect/token -H "Content-Type: application/x-www-form-urlencoded" -d "grant_type=password" -d "client_id=fastapi-api" -d "username=alice" -d "password=alice123" -d "scope=openid" | python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl http://localhost:8001/api/items -H "Authorization: Bearer $TOKEN"
curl -X POST http://localhost:8001/api/items -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d "{\"obra\":\"Claro de Luna\",\"compositor\":\"Beethoven\",\"epoca\":\"Clasicismo\",\"anio\":1801,\"duracion_min\":15}"
```

## Subir a GitHub (repo separado del frontend)
```bash
cd backend-dashboard
git init -b main
git add .
git commit -m "Backend dashboard musica clasica con validacion JWT"
gh repo create <TU-USUARIO>/dashboard-musica-backend --public --source=. --push
```

## Análisis de seguridad con Nuclei
Escaneo realizado el 2026-10-14 con **Nuclei v3.11.1** (templates v10.5.0, 11,144 templates).
El backend corrió en un contenedor dentro de la red Docker del lab LDAP/Keycloak, y Nuclei se ejecutó
en otro contenedor conectado a esa misma red (`http://dashboard-backend:8001`). También se escaneó el
código fuente con los templates `file/`.

Resultados completos: [`nuclei-results/`](nuclei-results/) · Triage: [`nuclei-results/RESUMEN.md`](nuclei-results/RESUMEN.md)

| Severidad | Hallazgo |
|---|---|
| Info | Swagger `/docs`, ReDoc `/redoc` y `/openapi.json` públicos |
| Info | Faltan 10 headers de seguridad (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, COOP, COEP, CORP, X-Permitted-Cross-Domain-Policies) |
| Info | Se revela la tecnología del servidor (`server: uvicorn`) |
| Código | Se imprime el header `Authorization` y parte del JWT en los logs (`app/main.py`) |
| Código | Credenciales de ejemplo en el README |

Hay falsos positivos documentados en el resumen, por ejemplo `dom-invader-xss` sobre código Python.

---

## Seguridad: Fail2Ban contra HTTP-flood (actividad DDoS)

La imagen ahora corre **Nginx como reverse proxy + Fail2Ban** al frente del
uvicorn (que queda en `127.0.0.1:9001`). Nginx escribe `access.log` y el jail
`http-flood` banea con `iptables-allports` a la IP que supere el umbral.

- Config: carpeta [`security/`](security/) (`nginx.conf`, `jail.local`,
  `filter-http-flood.conf`, `entrypoint.sh`).
- Umbral: `maxretry=60` en `findtime=10s` (~6 req/s sostenidas → ban).

```bash
docker compose up --build        # levanta el backend protegido en :8001
# estado del jail / baneos:
docker compose exec backend fail2ban-client status http-flood
docker compose exec backend iptables -S | grep f2b
```

La prueba de carga vive en el repo aparte **dashboard-musica-ddos**:
```bash
python flood.py 127.0.0.1 8001 --rate 120 --duration 15
python sweep.py 127.0.0.1 8001 --out resultados-backend.txt   # halla el máximo sostenible
```
> **Nota:** `cap_add: [NET_ADMIN, NET_RAW]` es obligatorio (ya está en el compose)
> para que Fail2Ban pueda crear las reglas iptables dentro del contenedor.
