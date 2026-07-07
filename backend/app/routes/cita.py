from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List

from app.database import get_session
from app.models.cita import Cita, CitaCreate, CitaRead
from app.models.usuario import Usuario
from app.core.security import get_current_user

router = APIRouter(prefix="/citas", tags=["Citas"])


@router.get("/mis-citas", response_model=List[CitaRead])
async def obtener_mis_citas(
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(get_current_user)
):
    """
    Obtiene todas las citas del usuario autenticado
    """
    try:
        # Buscar el usuario por supabase_uid
        result = await session.exec(
            select(Usuario).where(Usuario.supabase_uid == token_data.get("sub"))
        )
        usuario = result.first()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Obtener citas del usuario
        result = await session.exec(
            select(Cita).where(Cita.usuario_id == usuario.id)
        )
        citas = result.all()

        return citas

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")


@router.post("/", response_model=CitaRead)
async def crear_cita(
    cita_data: CitaCreate,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(get_current_user)
):
    """
    Crea una nueva cita para el usuario autenticado
    """
    try:
        # Buscar el usuario por supabase_uid
        result = await session.exec(
            select(Usuario).where(Usuario.supabase_uid == token_data.get("sub"))
        )
        usuario = result.first()

        if not usuario:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")

        # Crear la cita
        nueva_cita = Cita(
            fecha=cita_data.fecha,
            hora=cita_data.hora,
            tratamiento=cita_data.tratamiento,
            estado=cita_data.estado,
            notas=cita_data.notas,
            usuario_id=usuario.id
        )

        session.add(nueva_cita)
        await session.commit()
        await session.refresh(nueva_cita)

        return nueva_cita

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
