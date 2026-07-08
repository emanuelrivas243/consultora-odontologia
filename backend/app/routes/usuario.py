from fastapi import APIRouter, Depends, HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.database import get_session
from app.models.usuario import Usuario, UsuarioCreate, UsuarioRead, UsuarioUpdate
from app.core.security import get_current_user, require_admin, get_current_user_with_role

# Definimos el router. IMPORTANTE: El prefijo aquí es "/usuarios"
router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# 1. Endpoint /me - DEBE ir primero para que no sea interceptado por /{usuario_id}
@router.get("/me", response_model=dict)
async def get_usuario_me(
    user_data: dict = Depends(get_current_user_with_role)
):
    if not user_data or "usuario_db" not in user_data:
        raise HTTPException(status_code=404, detail="Usuario no encontrado en base de datos")
    
    usuario_db = user_data["usuario_db"]
    
    return {
        "id": usuario_db.id,
        "nombre": usuario_db.nombre,
        "apellido": usuario_db.apellido,
        "correo": usuario_db.correo,
        "rol": usuario_db.rol.value if hasattr(usuario_db.rol, 'value') else usuario_db.rol
    }

# 2. Otros endpoints
@router.post("/", response_model=UsuarioRead)
async def crear_usuario(
    usuario: UsuarioCreate,
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(get_current_user)
): 
    nuevo_usuario = Usuario(**usuario.model_dump())
    nuevo_usuario.supabase_uid = token_data.get("sub")
    session.add(nuevo_usuario)
    await session.commit()
    await session.refresh(nuevo_usuario)
    return nuevo_usuario

@router.get("/", response_model=list[UsuarioRead])
async def listar_usuarios(
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    result = await session.exec(select(Usuario))
    return result.all()

@router.get("/{usuario_id}", response_model=UsuarioRead)
async def obtener_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_session),
    user: dict = Depends(get_current_user)
):
    result = await session.exec(select(Usuario).where(Usuario.supabase_uid == usuario_id))
    usuario = result.first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.delete("/{usuario_id}")
async def eliminar_usuario(
    usuario_id: str,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    result = await session.exec(select(Usuario).where(Usuario.supabase_uid == usuario_id))
    usuario = result.first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await session.delete(usuario)
    await session.commit()
    return {"mensaje": "Usuario eliminado correctamente"}

@router.patch("/{usuario_id}", response_model=UsuarioRead)
async def actualizar_usuario(
    usuario_id: str,
    usuario_data: UsuarioUpdate,
    session: AsyncSession = Depends(get_session),
    admin: dict = Depends(require_admin)
):
    result = await session.exec(select(Usuario).where(Usuario.supabase_uid == usuario_id))
    usuario = result.first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    data = usuario_data.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(usuario, key, value)
    
    session.add(usuario)
    await session.commit()
    await session.refresh(usuario)
    return usuario