from fastapi import FastAPI, Depends
from sqlmodel import select, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from app.database import get_session, engine
from app.models.usuario import Usuario
from app.core.security import get_current_user_with_role, require_admin
from app.routes.usuario import router as usuarios_router

app = FastAPI(title="Backend Odontología")

# EVENTO DE INICIO PARA CREAR TABLAS
@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        # Esto crea las tablas automáticamente si no existen en la base de datos
        # Al haber cambiado el modelo a usar 'String', se creará como VARCHAR limpio
        await conn.run_sync(SQLModel.metadata.create_all)

# INCLUSIÓN DE RUTAS
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