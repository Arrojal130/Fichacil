"""
FichaFacil MVP - PDF Generation Router
PDF reports designed to help with labor inspection exports.
"""
from datetime import datetime, date, timezone
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from app.database import get_db
from app.models import Negocio, User, Fichaje
from app.models.fichaje import TipoFichaje
from app.models.user import UserRole
from app.models.correccion import Correccion, EstadoCorreccion
from app.utils.security import get_current_admin
from app.utils.formatting import format_hours
from app.utils.corrections import get_effective_timestamp
import uuid

router = APIRouter(prefix="/pdf", tags=["PDF"])


@router.get("/registro")
async def generar_pdf(
    fecha_inicio: date,
    fecha_fin: date,
    empleado_id: int = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate legal PDF report for time records.
    
    Export contents intended to support time-register review:
    - Company info (name, NIF, address)
    - Employee info (name, DNI)
    - Daily records: date, entry, exit, total hours
    - Geolocation coordinates
    - Total hours per period
    - Overtime calculation
    - Generation timestamp (UTC)
    - Unique document ID
    """
    # Validate date range
    if fecha_fin < fecha_inicio:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Fecha fin debe ser posterior a fecha inicio"
        )
    
    if (fecha_fin - fecha_inicio).days > 365:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rango máximo: 1 año"
        )
    
    # Get business info
    result = await db.execute(
        select(Negocio).where(Negocio.id == current_user.negocio_id)
    )
    negocio = result.scalar_one()
    
    # Get employees
    emp_query = select(User).where(
        User.negocio_id == current_user.negocio_id,
        User.rol == UserRole.EMPLEADO
    )
    if empleado_id:
        emp_query = emp_query.where(User.id == empleado_id)
    
    result = await db.execute(emp_query.order_by(User.nombre))
    employees = result.scalars().all()
    
    if not employees:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontraron empleados"
        )
    
    # Get fichajes
    start_dt = datetime.combine(fecha_inicio, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(fecha_fin, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    fichajes_query = select(Fichaje).where(
        Fichaje.negocio_id == current_user.negocio_id,
        Fichaje.timestamp >= start_dt,
        Fichaje.timestamp <= end_dt
    )
    if empleado_id:
        fichajes_query = fichajes_query.where(Fichaje.empleado_id == empleado_id)
    
    result = await db.execute(fichajes_query.order_by(Fichaje.timestamp))
    fichajes = result.scalars().all()
    
    # Get approved corrections for these fichajes
    fichaje_ids = [f.id for f in fichajes]
    correcciones_query = select(Correccion).where(
        Correccion.fichaje_id.in_(fichaje_ids),
        Correccion.estado == EstadoCorreccion.APROBADO
    )
    result = await db.execute(correcciones_query)
    correcciones_aprobadas = result.scalars().all()
    correcciones_por_fichaje = {
        c.fichaje_id: c.timestamp_corregido
        for c in correcciones_aprobadas
    }
    fichajes_corregidos = set(correcciones_por_fichaje)
    
    # Track if any corrections exist for footer note
    hay_correcciones = len(fichajes_corregidos) > 0
    
    # Group fichajes by employee and day
    from collections import defaultdict
    fichajes_by_emp = defaultdict(lambda: defaultdict(list))
    
    for f in fichajes:
        day = f.timestamp.date()
        fichajes_by_emp[f.empleado_id][day].append(f)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5*cm,
        leftMargin=1.5*cm,
        topMargin=1.5*cm,
        bottomMargin=1.5*cm
    )
    
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='Title2',
        parent=styles['Heading1'],
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='CompanyInfo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='Legal',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=colors.grey
    ))
    
    elements = []
    
    # Header
    elements.append(Paragraph("REGISTRO DE JORNADA LABORAL", styles['Title2']))
    elements.append(Paragraph(
        "Documento diseñado para ayudar al cumplimiento del registro horario",
        styles['Legal']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Company info
    elements.append(Paragraph(f"<b>EMPRESA:</b> {negocio.nombre}", styles['CompanyInfo']))
    if negocio.nif:
        elements.append(Paragraph(f"<b>NIF:</b> {negocio.nif}", styles['CompanyInfo']))
    if negocio.direccion:
        elements.append(Paragraph(f"<b>DIRECCIÓN:</b> {negocio.direccion}", styles['CompanyInfo']))
    elements.append(Paragraph(
        f"<b>PERÍODO:</b> {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}",
        styles['CompanyInfo']
    ))
    elements.append(Spacer(1, 0.5*cm))
    
    # Employee sections
    for emp in employees:
        emp_fichajes = fichajes_by_emp.get(emp.id, {})
        
        elements.append(Paragraph(
            f"<b>EMPLEADO:</b> {emp.nombre}" + (f" | DNI: {emp.dni}" if emp.dni else ""),
            styles['Heading2']
        ))
        elements.append(Spacer(1, 0.3*cm))
        
        # Build table data
        table_data = [["Fecha", "Entrada", "Salida", "Horas", "Ubicación"]]
        total_minutes = 0
        
        # Iterate through all days in range
        current_date = fecha_inicio
        while current_date <= fecha_fin:
            day_fichajes = emp_fichajes.get(current_date, [])
            
            entrada = None
            salida = None
            
            for f in day_fichajes:
                if f.tipo == TipoFichaje.ENTRADA:
                    entrada = f
                elif f.tipo == TipoFichaje.SALIDA:
                    salida = f
            
            if entrada or salida:
                # Check if this fichaje has approved correction
                entrada_corregido = entrada and entrada.id in fichajes_corregidos
                salida_corregido = salida and salida.id in fichajes_corregidos
                
                entrada_ts = get_effective_timestamp(entrada, correcciones_por_fichaje) if entrada else None
                salida_ts = get_effective_timestamp(salida, correcciones_por_fichaje) if salida else None

                entrada_str = entrada_ts.strftime("%H:%M") if entrada_ts else "-"
                if entrada_corregido:
                    entrada_str += " *"
                    
                salida_str = salida_ts.strftime("%H:%M") if salida_ts else "-"
                if salida_corregido:
                    salida_str += " *"
                
                minutes = 0
                if entrada_ts and salida_ts:
                    minutes = int((salida_ts - entrada_ts).total_seconds() / 60)
                    total_minutes += minutes
                
                horas_str = format_hours(minutes) if minutes else "-"
                
                # Geolocation
                loc_parts = []
                if entrada and entrada.lat and entrada.lon:
                    loc_parts.append(f"E:{entrada.lat:.4f}/{entrada.lon:.4f}")
                if salida and salida.lat and salida.lon:
                    loc_parts.append(f"S:{salida.lat:.4f}/{salida.lon:.4f}")
                loc_str = " ".join(loc_parts) if loc_parts else "-"
                
                table_data.append([
                    current_date.strftime("%d/%m/%Y"),
                    entrada_str,
                    salida_str,
                    horas_str,
                    loc_str
                ])
            
            current_date = date(
                current_date.year,
                current_date.month,
                current_date.day
            )
            # Increment by one day
            from datetime import timedelta
            current_date += timedelta(days=1)
        
        # Add totals
        if len(table_data) > 1:
            total_str = format_hours(total_minutes)
            extra_minutes = total_minutes - 2400  # 40h = 2400min (standard week)
            extra_str = format_hours(extra_minutes) if extra_minutes > 0 else "-"
            
            table_data.append(["", "", "TOTAL:", total_str, ""])
            if extra_minutes > 0:
                table_data.append(["", "", "EXTRAS:", extra_str, ""])
            
            # Create table
            table = Table(table_data, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 7*cm])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('FONTNAME', (2, -2), (3, -1), 'Helvetica-Bold'),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("Sin registros en este período", styles['Normal']))
        
        elements.append(Spacer(1, 0.5*cm))
    
    # Footer
    doc_id = str(uuid.uuid4())[:8].upper()
    gen_time = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M:%S UTC")
    
    elements.append(Spacer(1, 1*cm))
    
    # Add correction footnote if applicable
    if hay_correcciones:
        elements.append(Paragraph(
            "(*) Registro modificado mediante corrección aprobada por ambas partes.",
            styles['Legal']
        ))
        elements.append(Spacer(1, 0.3*cm))
    
    elements.append(Paragraph(
        f"Generado: {gen_time} | Pendiente de validación legal definitiva",
        styles['Legal']
    ))
    elements.append(Paragraph(
        f"Documento ID: {doc_id} | Sistema: FichaFácil v1.0",
        styles['Legal']
    ))
    
    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    
    # Generate filename
    filename = f"registro_{negocio.slug}_{fecha_inicio.strftime('%Y%m%d')}_{fecha_fin.strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )
