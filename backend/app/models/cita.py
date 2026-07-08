from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date, time


class CitaBase(SQLModel):
    fecha: date = Field(nullable=False)
    hora: time = Field(nullable=False)
    odontologo: Optional[str] = Field(default=None, max_length=100)
    procedimiento: Optional[str] = Field(default=None, max_length=100)
    estado: Optional[str] = Field(default="pendiente", max_length=20)


class CitaCreate(CitaBase):
    usuario_id: int = Field(nullable=False)


class CitaRead(CitaBase):
    id: int
    usuario_id: int


class Cita(CitaBase, table=True):
    __tablename__ = "citas"

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: Optional[int] = Field(default=None, nullable=True)
    
class CitaUpdate(SQLModel):
    estado: Optional[str] = None
