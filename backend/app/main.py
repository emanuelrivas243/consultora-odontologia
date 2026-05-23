# main.py
from fastapi import FastAPI, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session
from app.models.usuario import Usuario
from app.core.security import get_current_user_with_role, require_admin
from app.routes.usuario import router as usuarios_router

app = FastAPI(title="Backend Odontología")
app.include_router(usuarios_router)
# ENDPOINT: Para probar el token y ver tu información + rol
@app.get("/usuario/me")
async def obtener_mi_perfil(current_user: dict = Depends(get_current_user_with_role)):
    """
    Retorna el payload del token decodificado de Supabase y el rol mapeado.
    """
    return current_user

# ENDPOINT: Solo los Administradores deberían listar todos los pacientes
@app.get("/pacientes")
async def listar_pacientes(session: AsyncSession = Depends(get_session), admin_user: dict = Depends(require_admin)):
    statement = select(Usuario)
    result = await session.exec(statement)
    pacientes = result.all()
    
    return pacientes