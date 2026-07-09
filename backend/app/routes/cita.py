from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import List
from datetime import datetime
from io import BytesIO

from app.database import get_session
from app.models.cita import Cita, CitaCreate, CitaRead, CitaUpdate
from app.models.usuario import Usuario
from app.core.security import get_current_user, require_admin
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

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


@router.get("/historial-pdf")
async def generar_historial_pdf(
    session: AsyncSession = Depends(get_session),
    token_data: dict = Depends(get_current_user)
):
    """
    Genera un PDF con el historial médico de citas del paciente
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

        # Crear el PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        styles = getSampleStyleSheet()
        elements = []

        # Título
        title = Paragraph("Historial Médico - Consultora Odontológica", styles['Title'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Información del paciente
        patient_info = Paragraph(
            f"<b>Paciente:</b> {usuario.nombre} {usuario.apellido}<br/>"
            f"<b>Email:</b> {usuario.correo}<br/>"
            f"<b>Teléfono:</b> {usuario.telefono}<br/>"
            f"<b>Fecha de generación:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            styles['Normal']
        )
        elements.append(patient_info)
        elements.append(Spacer(1, 24))

        # Tabla de citas
        if citas:
            data = [['Fecha', 'Hora', 'Odontólogo', 'Procedimiento', 'Estado']]
            
            for cita in citas:
                fecha_str = cita.fecha.strftime('%d/%m/%Y') if cita.fecha else 'N/A'
                hora_str = str(cita.hora) if cita.hora else 'N/A'
                odontologo_str = cita.odontologo or 'No asignado'
                procedimiento_str = cita.procedimiento or 'General'
                estado_str = cita.estado or 'Pendiente'
                
                data.append([fecha_str, hora_str, odontologo_str, procedimiento_str, estado_str])

            table = Table(data, colWidths=[1.2*inch, 1*inch, 1.5*inch, 1.5*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ]))
            
            elements.append(table)
        else:
            no_citas = Paragraph("No hay citas registradas en el historial.", styles['Normal'])
            elements.append(no_citas)

        # Generar el PDF
        doc.build(elements)
        buffer.seek(0)

        # Retornar el PDF como respuesta
        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=historial_{usuario.correo}_{datetime.now().strftime('%Y%m%d')}.pdf"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar PDF: {str(e)}")