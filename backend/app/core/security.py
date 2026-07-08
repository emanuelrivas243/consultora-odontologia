import os
import requests
from jose import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.usuario import RolUsuario, Usuario
from app.database import get_session
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pathlib import Path
from dotenv import load_dotenv

# CARGAR .ENV
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

# SEGURIDAD
security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL")

if not SUPABASE_URL:
    raise ValueError("Falta SUPABASE_URL en el .env")

# OBTENER CLAVES PÚBLICAS (JWKS)
def get_jwks():
    url = f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json"
    response = requests.get(url)

    if response.status_code != 200:
        # Error genérico para el cliente si falla la conexión interna con Supabase
        raise HTTPException(
            status_code=500,
            detail="Error interno de autenticación"
        )

    return response.json()

# VALIDAR JWT (ES256)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        jwks = get_jwks()

        # Obtener header del token
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")

        # Buscar clave correcta
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)

        if not key:
            raise HTTPException(status_code=401, detail="Clave pública no encontrada")

        # Validar token con configuración adaptada a Supabase
        payload = jwt.decode(
            token,
            key,
            algorithms=["ES256"],
            options={
                "verify_aud": False,  # Evitamos conflictos con el audience estricto
                "verify_sub": True,
                "verify_exp": True
            }
        )

        return payload

    except Exception as e:
        # El print se queda para lograr monitorear en la terminal local
        print(f"❌ ERROR DECODIFICANDO JWT: {str(e)}")
        
        # El cliente en Swagger o Frontend solo recibe un mensaje limpio y seguro
        raise HTTPException(
            status_code=401, 
            detail="Token inválido o expirado"
        )


# EXTRAER USUARIO + ROL
async def get_current_user_with_role(
    payload: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    try:
        # Obtener supabase_uid del JWT
        supabase_uid = payload.get("sub")

        if not supabase_uid:
            raise HTTPException(status_code=403, detail="Usuario no identificado")

        # Consultar el rol real en la base de datos
        result = await session.exec(
            select(Usuario).where(Usuario.supabase_uid == supabase_uid)
        )
        usuario = result.first()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado en base de datos")

        # Usar el rol de la base de datos
        return {
            "user": payload,
            "role": usuario.rol,
            "usuario_db": usuario
        }

    except ValueError:
        raise HTTPException(status_code=403, detail="Rol inválido")


# SOLO ADMIN
async def require_admin(
    user_data: dict = Depends(get_current_user_with_role)
):
    if user_data["role"] != RolUsuario.ADMIN:
        raise HTTPException(status_code=403, detail="No autorizado (Admin requerido)")

    return user_data


# SOLO PACIENTE
async def require_paciente(
    user_data: dict = Depends(get_current_user_with_role)
):
    if user_data["role"] != RolUsuario.PACIENTE:
        raise HTTPException(status_code=403, detail="Solo pacientes")

    return user_data