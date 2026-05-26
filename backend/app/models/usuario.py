from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import String
from pydantic import BaseModel


# editar datos de usuario (sin cambiar supabase_uid ni rol)
class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    # No incluimos 'supabase_uid' porque ese no debe cambiarse nunca
    
# DEFINICIÓN DE ROLES
class RolUsuario(str, Enum):
    PACIENTE = "paciente"    
    ADMIN = "admin"

# ESQUEMA BASE PARA USUARIOS (lo que comparten los 3 esquemas)
class UsuarioBase(SQLModel):
    correo: str = Field(unique=True, nullable=False, max_length=100)
    telefono: str = Field(unique=True, nullable=False, max_length=20)
    nombre: str = Field(nullable=False, max_length=50)
    apellido: str = Field(nullable=False, max_length=50)
    rol: RolUsuario = RolUsuario.PACIENTE

# ESQUEMA PARA CREAR (Lo que se envía en el JSON de Swagger)
class UsuarioCreate(UsuarioBase):
    pass  # <-- ¡Listo! Ya no pedirá el 'supabase_uid' en el cuerpo del JSON


# ESQUEMA PARA CREAR (Lo que envía el Frontend al registrarse)
# este sí se usa en producción, por ahora el de arriba queda para pruebas
#class UsuarioCreate(UsuarioBase):
#    supabase_uid: str = Field(nullable=False)  # Obligatorio al crearlo desde el registro de Supabase

# ESQUEMA PARA LEER (Lo que la API devuelve de forma segura)
class UsuarioRead(UsuarioBase):
    id: int
    supabase_uid: Optional[str] = None

# MODELO DE TABLA (Lo que se guarda en PostgreSQL realmente)
class Usuario(UsuarioBase, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Le decimos a SQLAlchemy que trate la columna como texto común (VARCHAR)
    rol: RolUsuario = Field(
        sa_column=Column(
            String, 
            nullable=False, 
            default=RolUsuario.PACIENTE.value
        )
    )

    supabase_uid: Optional[str] = Field(default=None, unique=True, nullable=True)