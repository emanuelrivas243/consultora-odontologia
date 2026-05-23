import os
from typing import AsyncGenerator
from pathlib import Path
from dotenv import load_dotenv
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker

#SEGURO DE RUTAS: 
# Path(__file__).resolve() es 'backend/app/database.py'
# .parent es 'backend/app'
# .parent.parent es 'backend' (donde vive tu .env)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Falta la variable de entorno DATABASE_URL en el archivo .env")

engine = create_async_engine(
    DATABASE_URL, 
    connect_args={"statement_cache_size": 0},
    echo=True, 
    pool_size=5, 
    max_overflow=10
)

# Generador de sesiones asíncronas fuera para evitar recrearla en cada petición
async_session_factory = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)
# generador de sesiones asíncronas para los endpoints
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session # Entrega la sesión a la ruta y la cierra automáticamente al terminar la petición