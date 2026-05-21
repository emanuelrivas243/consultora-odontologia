import os
from typing import AsyncGenerator
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv


load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("Falta la variable de entorno DATABASE_URL")

engine = create_async_engine(
    DATABASE_URL, 
    connect_args={"statement_cache_size": 0},
    echo=True, 
    pool_size=5, 
    max_overflow=10
)

# 2. Generador de sesiones asíncronas
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async_session = sessionmaker(
        engine, 
        class_=AsyncSession, 
        expire_on_commit=False
    )
    async with async_session() as session:
        yield session  # Retorna la sesión activa para la petición y la cierra al terminar