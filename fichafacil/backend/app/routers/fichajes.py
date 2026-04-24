"""
FichaFacil MVP - Fichajes (Clock Records) Router
Core functionality: clock in/out with geolocation.
"""
from datetime import datetime, date, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.database import get_db
from app.models import Negocio, User, Fichaje
from app.models.fichaje import TipoFichaje
from app.models.user import UserRole
from app.schemas.fichaje import (
    FichajeCreate,
    EmpleadoPinRequest,
    HistorialEmpleadoRequest,
    FichajeResponse,
    FichajeConfirmacion,
    DashboardFichaje
)
from app.utils.security import (
    verify_pin, 
    get_current_user, 
    get_current_admin,
    check_pin_rate_limit,
    record_pin_attempt,
    get_client_ip
)
from app.utils.geolocation import calculate_distance_to_business, check_distance_alert
from app.utils.formatting import format_hours

router = APIRouter(prefix="/fichajes", tags=["Fichajes"])


@router.post("/", response_model=FichajeConfirmacion, status_code=status.HTTP_201_CREATED)
async def crear_fichaje(
    data: FichajeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a clock record (ENTRADA or SALIDA).
    
    CRITICAL: Timestamp is ALWAYS server-side (never trust client).
    Geolocation is validated but does NOT block clock-in.
    Rate limited: 5 attempts per IP per hour.
    """
    client_ip = get_client_ip(request)
    
    # Check rate limit before processing
    check_pin_rate_limit(data.negocio_id, client_ip)
    
    # Validate business exists
    result = await db.execute(
        select(Negocio).where(Negocio.id == data.negocio_id)
    )
    negocio = result.scalar_one_or_none()
    
    if not negocio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado"
        )
    
    # Find employee by PIN in this business
    result = await db.execute(
        select(User).where(
            User.negocio_id == data.negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        )
    )
    employees = result.scalars().all()
    
    empleado = None
    for emp in employees:
        if emp.pin_hash and verify_pin(data.pin, emp.pin_hash):
            empleado = emp
            break
    
    if not empleado:
        # Record failed attempt
        record_pin_attempt(data.negocio_id, client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto"
        )
    
    # Success - clear rate limit
    record_pin_attempt(data.negocio_id, client_ip, success=True)
    
    # Check if this clock type makes sense
    # Get last fichaje for this employee today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    result = await db.execute(
        select(Fichaje).where(
            Fichaje.empleado_id == empleado.id,
            Fichaje.timestamp >= today_start
        ).order_by(Fichaje.timestamp.desc())
    )
    today_fichajes = result.scalars().all()
    
    # Logic: ENTRADA should follow SALIDA (or be first)
    # SALIDA should follow ENTRADA
    if today_fichajes:
        last_tipo = today_fichajes[0].tipo
        if data.tipo == last_tipo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Ya has fichado {last_tipo.value} hoy. Debes fichar {'SALIDA' if last_tipo == TipoFichaje.ENTRADA else 'ENTRADA'}"
            )
    else:
        # First clock of the day should be ENTRADA
        if data.tipo == TipoFichaje.SALIDA:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No puedes fichar SALIDA sin haber fichado ENTRADA hoy"
            )
    
    # Calculate distance to business
    distancia = calculate_distance_to_business(
        data.lat,
        data.lon,
        negocio.lat,
        negocio.lon
    )
    
    is_alert, alert_msg = check_distance_alert(distancia)
    
    # Create fichaje with SERVER timestamp
    fichaje = Fichaje(
        tipo=data.tipo,
        timestamp=datetime.now(timezone.utc),  # ALWAYS server time
        lat=data.lat,
        lon=data.lon,
        distancia_metros=distancia,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
        empleado_id=empleado.id,
        negocio_id=negocio.id
    )
    db.add(fichaje)
    await db.flush()
    await db.refresh(fichaje)
    
    return FichajeConfirmacion(
        mensaje=f"Fichaje {data.tipo.value} registrado correctamente",
        tipo=data.tipo,
        timestamp=fichaje.timestamp,
        distancia_metros=distancia,
        alerta_distancia=is_alert
    )


@router.post("/ultimo", response_model=FichajeResponse | None)
async def get_ultimo_fichaje(
    data: EmpleadoPinRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """Get the last clock record for an employee (for display). Rate limited."""
    negocio_id = data.negocio_id
    pin = data.pin
    client_ip = get_client_ip(request)
    
    # Check rate limit before processing
    check_pin_rate_limit(negocio_id, client_ip)
    
    # Find employee by PIN
    result = await db.execute(
        select(User).where(
            User.negocio_id == negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        )
    )
    employees = result.scalars().all()
    
    empleado = None
    for emp in employees:
        if emp.pin_hash and verify_pin(pin, emp.pin_hash):
            empleado = emp
            break
    
    if not empleado:
        record_pin_attempt(negocio_id, client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto"
        )
    
    # Success - clear rate limit
    record_pin_attempt(negocio_id, client_ip, success=True)
    
    # Get last fichaje
    result = await db.execute(
        select(Fichaje).where(
            Fichaje.empleado_id == empleado.id
        ).order_by(Fichaje.timestamp.desc()).limit(1)
    )
    fichaje = result.scalar_one_or_none()
    
    if not fichaje:
        return None
    
    return FichajeResponse.model_validate(fichaje)


@router.post("/historial-empleado", response_model=list[FichajeResponse])
async def get_historial_empleado(
    data: HistorialEmpleadoRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Get fichaje history for employee (PIN auth, no JWT).
    Returns last N days of fichajes for the authenticated employee.
    Rate limited.
    """
    negocio_id = data.negocio_id
    pin = data.pin
    dias = data.dias
    client_ip = get_client_ip(request)
    check_pin_rate_limit(negocio_id, client_ip)
    
    # Find employee by PIN
    result = await db.execute(
        select(User).where(
            User.negocio_id == negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        )
    )
    employees = result.scalars().all()
    
    empleado = None
    for emp in employees:
        if emp.pin_hash and verify_pin(pin, emp.pin_hash):
            empleado = emp
            break
    
    if not empleado:
        record_pin_attempt(negocio_id, client_ip, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorrecto"
        )
    
    record_pin_attempt(negocio_id, client_ip, success=True)
    
    # Get fichajes for last N days
    from datetime import timedelta
    fecha_inicio = datetime.now(timezone.utc) - timedelta(days=dias)
    
    result = await db.execute(
        select(Fichaje).where(
            Fichaje.empleado_id == empleado.id,
            Fichaje.timestamp >= fecha_inicio
        ).order_by(Fichaje.timestamp.desc())
    )
    fichajes = result.scalars().all()
    
    return [FichajeResponse.model_validate(f) for f in fichajes]


@router.get("/hoy", response_model=list[DashboardFichaje])
async def get_fichajes_hoy(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get today's clock records for dashboard (admin only).
    Returns one row per employee with entry/exit/status.
    """
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Get all employees for this business
    result = await db.execute(
        select(User).where(
            User.negocio_id == current_user.negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        ).order_by(User.nombre)
    )
    employees = result.scalars().all()
    
    dashboard_data = []
    
    for emp in employees:
        # Get today's fichajes for this employee
        result = await db.execute(
            select(Fichaje).where(
                Fichaje.empleado_id == emp.id,
                Fichaje.timestamp >= today_start
            ).order_by(Fichaje.timestamp)
        )
        fichajes = result.scalars().all()
        
        entrada = None
        salida = None
        distancia = None
        
        for f in fichajes:
            if f.tipo == TipoFichaje.ENTRADA:
                entrada = f.timestamp
                distancia = f.distancia_metros
            elif f.tipo == TipoFichaje.SALIDA:
                salida = f.timestamp
        
        # Calculate hours worked
        horas = None
        if entrada and salida:
            delta = salida - entrada
            horas = format_hours(int(delta.total_seconds() / 60))
        
        # Determine status
        if entrada and salida:
            estado = "completo"
        elif entrada:
            estado = "pendiente_salida"
        else:
            estado = "no_fichado"
        
        # Check for alerts
        alerta = None
        if distancia and distancia > 500:
            alerta = f"Lejos: {distancia:.0f}m"
        
        # Check yesterday's incomplete
        if estado == "no_fichado":
            yesterday = today_start - timedelta(days=1)
            result = await db.execute(
                select(Fichaje).where(
                    Fichaje.empleado_id == emp.id,
                    Fichaje.timestamp >= yesterday,
                    Fichaje.timestamp < today_start,
                    Fichaje.tipo == TipoFichaje.ENTRADA
                )
            )
            yesterday_entrada = result.scalar_one_or_none()
            
            if yesterday_entrada:
                result = await db.execute(
                    select(Fichaje).where(
                        Fichaje.empleado_id == emp.id,
                        Fichaje.timestamp >= yesterday,
                        Fichaje.timestamp < today_start,
                        Fichaje.tipo == TipoFichaje.SALIDA
                    )
                )
                yesterday_salida = result.scalar_one_or_none()
                
                if not yesterday_salida:
                    alerta = "Sin salida ayer"
        
        dashboard_data.append(DashboardFichaje(
            empleado_id=emp.id,
            empleado_nombre=emp.nombre,
            entrada=entrada,
            salida=salida,
            horas_trabajadas=horas,
            distancia_metros=distancia,
            estado=estado,
            alerta=alerta
        ))
    
    return dashboard_data


@router.get("/rango")
async def get_fichajes_rango(
    fecha_inicio: date,
    fecha_fin: date,
    empleado_id: Optional[int] = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get clock records for a date range (for PDF generation).
    Returns grouped by employee and day.
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
    
    # Build query
    start_dt = datetime.combine(fecha_inicio, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_dt = datetime.combine(fecha_fin, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    query = select(Fichaje).where(
        Fichaje.negocio_id == current_user.negocio_id,
        Fichaje.timestamp >= start_dt,
        Fichaje.timestamp <= end_dt
    )
    
    if empleado_id:
        query = query.where(Fichaje.empleado_id == empleado_id)
    
    query = query.order_by(Fichaje.empleado_id, Fichaje.timestamp)
    
    result = await db.execute(query)
    fichajes = result.scalars().all()
    
    # Group by employee and day
    from collections import defaultdict
    grouped = defaultdict(lambda: defaultdict(list))
    
    for f in fichajes:
        day = f.timestamp.date()
        grouped[f.empleado_id][day].append(f)
    
    # Get employee names
    emp_ids = list(grouped.keys())
    if emp_ids:
        result = await db.execute(
            select(User).where(User.id.in_(emp_ids))
        )
        employees = {e.id: e for e in result.scalars().all()}
    else:
        employees = {}
    
    # Format response
    response = []
    for emp_id, days in grouped.items():
        emp = employees.get(emp_id)
        emp_data = {
            "empleado_id": emp_id,
            "empleado_nombre": emp.nombre if emp else "Desconocido",
            "empleado_dni": emp.dni if emp else None,
            "dias": []
        }
        
        total_minutes = 0
        
        for day, day_fichajes in sorted(days.items()):
            entrada = None
            salida = None
            
            for f in day_fichajes:
                if f.tipo == TipoFichaje.ENTRADA:
                    entrada = f
                elif f.tipo == TipoFichaje.SALIDA:
                    salida = f
            
            minutes = 0
            if entrada and salida:
                minutes = int((salida.timestamp - entrada.timestamp).total_seconds() / 60)
                total_minutes += minutes
            
            emp_data["dias"].append({
                "fecha": day.isoformat(),
                "entrada": entrada.timestamp.isoformat() if entrada else None,
                "salida": salida.timestamp.isoformat() if salida else None,
                "horas": format_hours(minutes) if minutes else None,
                "lat_entrada": entrada.lat if entrada else None,
                "lon_entrada": entrada.lon if entrada else None,
                "lat_salida": salida.lat if salida else None,
                "lon_salida": salida.lon if salida else None
            })
        
        emp_data["total_horas"] = format_hours(total_minutes)
        emp_data["horas_extra"] = format_hours(total_minutes - 2400) if total_minutes > 2400 else None  # 40h = 2400min
        
        response.append(emp_data)
    
    return response
