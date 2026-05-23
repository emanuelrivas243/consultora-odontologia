from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.usuario import Usuario, UsuarioCreate, UsuarioRead
from app.core.security import get_current_user, require_admin

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])


# Crear usuario (solo admin)
@router.post("/", response_model=UsuarioRead)
async def crear_usuario(
    usuario: UsuarioCreate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):  
    nuevo_usuario = Usuario(**usuario.model_dump())

    session.add(nuevo_usuario)
    await session.commit()
    await session.refresh(nuevo_usuario)

    return nuevo_usuario


# Obtener todos los usuarios (protegido)
@router.get("/", response_model=list[UsuarioRead])
async def listar_usuarios(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    result = await session.exec(select(Usuario))
    usuarios = result.all()
    return usuarios


# Obtener usuario por ID
@router.get("/{usuario_id}", response_model=UsuarioRead)
async def obtener_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    result = await session.exec(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario


# Eliminar usuario (solo admin)
@router.delete("/{usuario_id}")
async def eliminar_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    result = await session.exec(
        select(Usuario).where(Usuario.id == usuario_id)
    )
    usuario = result.first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    session.delete(usuario)
    await session.commit()

    return {"mensaje": "Usuario eliminado"}