from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List

from app.database import get_session
from app.models.cita import Cita, CitaCreate, CitaRead, CitaUpdate
from app.models.usuario import Usuario
from app.core.security import get_current_user, require_admin

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


@router.get("/", response_model=List[CitaRead])
async def obtener_todas_citas(
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    """
    Obtiene todas las citas del sistema (solo administradores)
    """
    try:
        result = await session.exec(select(Cita))
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
            procedimiento=cita_data.procedimiento,
            estado=cita_data.estado,
            #notas=cita_data.notas,
            odontologo=cita_data.odontologo,
            usuario_id=cita_data.usuario_id
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

@router.patch("/{cita_id}", response_model=CitaRead)
async def actualizar_cita(
    cita_id: int,
    cita_update: CitaUpdate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin) # Solo admin puede cambiar estados
):
    """
    Actualiza el estado de una cita existente
    """
    db_cita = await session.get(Cita, cita_id)
    if not db_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Actualizar solo los campos enviados
    cita_data = cita_update.dict(exclude_unset=True)
    for key, value in cita_data.items():
        setattr(db_cita, key, value)
    
    session.add(db_cita)
    await session.commit()
    await session.refresh(db_cita)
    return db_cita

@router.delete("/{cita_id}")
async def eliminar_cita(
    cita_id: int,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin) # Solo admin puede eliminar
):
    """
    Elimina una cita del sistema
    """
    db_cita = await session.get(Cita, cita_id)
    if not db_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    await session.delete(db_cita)
    await session.commit()
    return {"ok": True}

@router.put("/{cita_id}", response_model=CitaRead)
async def editar_cita_completa(
    cita_id: int,
    cita_data: CitaCreate, # Usamos CitaCreate para validar todos los campos
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    db_cita = await session.get(Cita, cita_id)
    if not db_cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Actualizamos todos los campos
    cita_dict = cita_data.dict()
    for key, value in cita_dict.items():
        setattr(db_cita, key, value)
        
    session.add(db_cita)
    await session.commit()
    await session.refresh(db_cita)
    return db_cita