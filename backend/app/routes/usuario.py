from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.usuario import Usuario, UsuarioCreate, UsuarioRead, UsuarioUpdate
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
    usuario_id: str,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    result = await session.exec(
        select(Usuario).where(Usuario.supabase_uid == usuario_id)
    )
    usuario = result.first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario


# Eliminar usuario (solo admin)
@router.delete("/{usuario_id}")
async def eliminar_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    result = await session.exec(
        select(Usuario).where(Usuario.supabase_uid == usuario_id)
    )
    usuario = result.first()

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    #eliminamos
    await session.delete(usuario)
    
    await session.commit()

    return {"mensaje": "Usuario eliminado correctamente"}

# Actualizar usuario (solo admin)
@router.patch("/{usuario_id}", response_model=UsuarioRead)
async def actualizar_usuario(
    usuario_id: str,
    usuario_data: UsuarioUpdate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    # 1. Buscar el usuario
    result = await session.exec(select(Usuario).where(Usuario.supabase_uid == usuario_id))
    usuario = result.first()
    
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    # 2. Actualizar solo los campos que vienen en el JSON
    # 'exclude_unset=True' es vital: solo toma los campos que el usuario envió
    data = usuario_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(usuario, key, value)
    
    # 3. Guardar cambios
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    
    return usuario