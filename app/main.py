"""
Dashboard Musica Clasica - Backend protegido con JWT (Keycloak + LDAP).
Valida el Bearer Token (firma RS256, issuer, audience) antes de
permitir GET /api/items y POST /api/items.

Flujo:
  Browser -> Next.js /api/auth/login -> Keycloak token endpoint
    (grant_type=password, LDAP federado) -> JWT
  Browser -> Next.js proxy (inyecta Authorization: Bearer <JWT>)
    -> este backend -> valida JWT -> responde listado/alta.
"""
import json
import os
from pathlib import Path
from typing import Annotated

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

KC_INTERNAL = os.getenv("KEYCLOAK_INTERNAL", "http://localhost:8081")
KC_PUBLIC = os.getenv("KEYCLOAK_PUBLIC", "http://localhost:8081")
REALM = os.getenv("KEYCLOAK_REALM", "cybersecurity")
CLIENT_ID = os.getenv("KEYCLOAK_CLIENT_ID", "fastapi-api")

# El `iss` del token es siempre la URL PUBLICA de Keycloak.
ISSUER = f"{KC_PUBLIC}/realms/{REALM}"
# JWKS se puede obtener por URL interna (docker) o publica (dev local).
JWKS_URLS = [
    f"{KC_INTERNAL}/realms/{REALM}/protocol/openid-connect/certs",
    f"{KC_PUBLIC}/realms/{REALM}/protocol/openid-connect/certs",
]

DATA_FILE = Path(__file__).parent / "data_items.json"

app = FastAPI(title="Dashboard Musica Clasica API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bearer_scheme = HTTPBearer(auto_error=True)


def _load_items() -> list[dict]:
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    seed = [
        {"id": 1, "obra": "Sinfonia No. 5", "compositor": "Beethoven", "epoca": "Clasicismo", "anio": 1808, "duracion_min": 33},
        {"id": 2, "obra": "Las Cuatro Estaciones", "compositor": "Vivaldi", "epoca": "Barroco", "anio": 1725, "duracion_min": 42},
        {"id": 3, "obra": "Requiem en Re menor", "compositor": "Mozart", "epoca": "Clasicismo", "anio": 1791, "duracion_min": 54},
    ]
    DATA_FILE.write_text(json.dumps(seed, ensure_ascii=False, indent=2), encoding="utf-8")
    return seed


def _save_items(items: list[dict]) -> None:
    DATA_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


async def _fetch_jwks() -> dict:
    last_err: Exception | None = None
    async with httpx.AsyncClient() as c:
        for url in JWKS_URLS:
            try:
                r = await c.get(url, timeout=5)
                r.raise_for_status()
                return r.json()
            except httpx.HTTPError as e:
                last_err = e
    raise HTTPException(500, f"No se pudo obtener JWKS de Keycloak: {last_err}")


async def current_user(
    request: Request,
    creds: Annotated[HTTPAuthorizationCredentials, Depends(bearer_scheme)],
) -> dict:
    # EVIDENCIA PARA EL VIDEO: muestra que el JWT llega en cada request.
    auth_header = request.headers.get("authorization", "")
    print(f"[backend] {request.method} {request.url.path} -> Authorization: {auth_header[:60]}...")
    token = creds.credentials
    print(f"[backend] JWT (primeros 40 chars): {token[:40]}... largo={len(token)}")
    try:
        jwks = await _fetch_jwks()
        header = jwt.get_unverified_header(token)
        key = next((k for k in jwks["keys"] if k.get("kid") == header.get("kid")), None)
        if not key:
            raise HTTPException(401, "Signing key not found")
        return jwt.decode(token, key, algorithms=["RS256"], audience=CLIENT_ID, issuer=ISSUER)
    except (JWTError, StopIteration) as e:
        print(f"[backend] JWT INVALIDO: {e}")
        raise HTTPException(401, f"Invalid access token: {e}", headers={"WWW-Authenticate": "Bearer"})


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/profile")
async def profile(user: Annotated[dict, Depends(current_user)]):
    return {
        "message": "Bearer token valido",
        "subject": user.get("sub"),
        "username": user.get("preferred_username"),
        "email": user.get("email"),
        "issuer": user.get("iss"),
    }


@app.get("/api/items")
async def list_items(user: Annotated[dict, Depends(current_user)]):
    items = _load_items()
    print(f"[backend] GET /api/items por {user.get('preferred_username')} -> {len(items)} items")
    return {"items": items, "total": len(items)}


@app.post("/api/items", status_code=201)
async def create_item(payload: dict, user: Annotated[dict, Depends(current_user)]):
    items = _load_items()
    for field in ("obra", "compositor"):
        if not payload.get(field):
            raise HTTPException(422, f"Campo requerido: {field}")
    new_id = max([i["id"] for i in items], default=0) + 1
    item = {
        "id": new_id,
        "obra": payload.get("obra"),
        "compositor": payload.get("compositor"),
        "epoca": payload.get("epoca", "—"),
        "anio": payload.get("anio"),
        "duracion_min": payload.get("duracion_min"),
    }
    items.append(item)
    _save_items(items)
    print(f"[backend] POST /api/items por {user.get('preferred_username')} -> creado id={new_id}")
    return item
