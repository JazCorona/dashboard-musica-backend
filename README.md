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
