from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.database import get_session
from app.models.usuario import Usuario
from app.core.security import SUPABASE_URL
import requests
import os

router = APIRouter(prefix="/auth", tags=["Autenticación"])

# Modelos para las solicitudes
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    nombre: str
    apellido: str
    telefono: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RegisterResponse(BaseModel):
    message: str
    user: dict

class LoginResponse(BaseModel):
    message: str
    access_token: str
    user: dict

SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

if not SUPABASE_KEY:
    raise ValueError("Falta SUPABASE_ANON_KEY en el .env")


@router.post("/register", response_model=RegisterResponse)
async def register_user(
    user_data: RegisterRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Registro de usuario público usando Supabase Auth
    """
    try:
        # 1. Verificar si el correo ya existe en nuestra base de datos
        existing_user = await session.exec(
            select(Usuario).where(Usuario.correo == user_data.email)
        )
        if existing_user.first():
            raise HTTPException(status_code=409, detail="El correo electrónico ya está registrado")

        # 2. Verificar si el teléfono ya existe
        existing_phone = await session.exec(
            select(Usuario).where(Usuario.telefono == user_data.telefono)
        )
        if existing_phone.first():
            raise HTTPException(status_code=409, detail="El número de teléfono ya está registrado")

        # 3. Registrar usuario en Supabase Auth
        supabase_url = f"{SUPABASE_URL}/auth/v1/signup"
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "nombre": user_data.nombre,
                    "apellido": user_data.apellido,
                    "telefono": user_data.telefono
                }
            }
        }

        response = requests.post(supabase_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            error_detail = response.json()
            raise HTTPException(
                status_code=400,
                detail=f"Error al registrar en Supabase: {error_detail.get('message', 'Error desconocido')}"
            )

        supabase_user = response.json()
        
        # 4. Crear el usuario en nuestra base de datos local
        nuevo_usuario = Usuario(
            correo=user_data.email,
            telefono=user_data.telefono,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            rol="paciente",
            supabase_uid=supabase_user.get("user", {}).get("id")
        )

        session.add(nuevo_usuario)
        await session.commit()
        await session.refresh(nuevo_usuario)

        return RegisterResponse(
            message="Registro exitoso",
            user={
                "id": nuevo_usuario.id,
                "correo": nuevo_usuario.correo,
                "nombre": nuevo_usuario.nombre,
                "apellido": nuevo_usuario.apellido,
                "rol": nuevo_usuario.rol
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.post("/login", response_model=LoginResponse)
async def login_user(credentials: LoginRequest):
    """
    Login de usuario usando Supabase Auth
    """
    try:
        # 1. Autenticar con Supabase
        supabase_url = f"{SUPABASE_URL}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": SUPABASE_KEY,
            "Content-Type": "application/json"
        }
        payload = {
            "email": credentials.email,
            "password": credentials.password
        }

        response = requests.post(supabase_url, json=payload, headers=headers)
        
        if response.status_code != 200:
            error_detail = response.json()
            raise HTTPException(
                status_code=401,
                detail=f"Credenciales inválidas: {error_detail.get('message', 'Error desconocido')}"
            )

        auth_data = response.json()
        
        return LoginResponse(
            message="Login exitoso",
            access_token=auth_data.get("access_token"),
            user={
                "id": auth_data.get("user", {}).get("id"),
                "email": auth_data.get("user", {}).get("email"),
                "role": auth_data.get("user", {}).get("app_metadata", {}).get("role", "paciente")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
