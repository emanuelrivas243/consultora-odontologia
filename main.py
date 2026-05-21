# main.py
from fastapi import FastAPI, Depends
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from database import get_session
from models import Usuario

app = FastAPI(title="Backend Odontología")

@app.get("/pacientes")
async def listar_pacientes(session: AsyncSession = Depends(get_session)):
    statement = select(Usuario)
    result = await session.exec(statement)
    pacientes = result.all()
    
    return pacientes