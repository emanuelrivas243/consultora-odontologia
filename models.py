from typing import Optional
from sqlmodel import SQLModel, Field

class Usuario(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: Optional[int] = Field(default=None, primary_key=True)
    correo: str = Field(unique=True, nullable=False, max_length=100)
    telefono: str = Field(unique=True, nullable=False, max_length=20)
    nombre: str = Field(nullable=False, max_length=50)
    apellido: str = Field(nullable=False, max_length=50)
    rol: str = Field(default="paciente", max_length=20)

    supabase_uid: Optional[str] = Field(default=None, unique=True, nullable=True)