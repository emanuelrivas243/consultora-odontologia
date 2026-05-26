import os
from pathlib import Path
import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
AUTH_TOKEN = os.getenv("TEST_TOKEN", "").strip()


def print_result(path: str, status_code: int, content: str) -> None:
    print(f"{path} -> {status_code}")
    print(content)
    print("-" * 60)


def request(path: str, method: str = "GET", json=None, use_auth: bool = False):
    url = f"{BASE_URL}{path}"
    headers = {}
    if use_auth:
        if not AUTH_TOKEN:
            print(f"SKIP {method} {path}: no TEST_TOKEN definido en .env")
            print("-" * 60)
            return
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"

    response = requests.request(method, url, headers=headers, json=json, timeout=15)
    try:
        content = response.json()
    except ValueError:
        content = response.text

    print_result(f"{method} {path}", response.status_code, str(content))


if __name__ == "__main__":
    print("Base URL:", BASE_URL)
    print("Auth token:", "yes" if AUTH_TOKEN else "no")
    print("=" * 60)

    request("/openapi.json")
    request("/docs")
    request("/usuario/me")
    request("/pacientes")
    request("/usuarios/")
    request("/usuarios/", use_auth=True)
    request("/usuario/me", use_auth=True)
    request("/pacientes", use_auth=True)
    request("/usuarios/", use_auth=True, json={
        "correo": "prueba@example.com",
        "telefono": "1234567890",
        "nombre": "Prueba",
        "apellido": "Usuario",
        "rol": "paciente",
        "supabase_uid": "uid-prueba-123"
    })
