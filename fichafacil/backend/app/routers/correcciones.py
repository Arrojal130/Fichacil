"""
FichaFacil MVP - Correcciones (Corrections) Router
Audit trail for clock record modifications with mutual approval.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.database import get_db
from app.models import User, Fichaje, Correccion
from app.models.correccion import EstadoCorreccion
from app.models.user import UserRole
from app.schemas.correccion import (
    CorreccionCreate,
    CorreccionApprove,
    CorreccionApproveEmpleado,
    CorreccionesPendientesEmpleadoRequest,
    CorreccionResponse,
    CorreccionPendiente,
)
from app.utils.security import (
    get_current_admin,
    get_current_user,
    get_optional_user,
    resolve_employee_user,
    verify_password,
)

router = APIRouter(prefix="/correcciones", tags=["Correcciones"])


@router.post("/", response_model=CorreccionResponse, status_code=status.HTTP_201_CREATED)
async def crear_correccion(
    data: CorreccionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a correction proposal.
    
    LEGAL: Requires mutual approval.
    - If admin proposes -> employee must approve
    - If employee proposes -> admin must approve
    """
    # Get the fichaje
    result = await db.execute(
        select(Fichaje).where(Fichaje.id == data.fichaje_id)
    )
    fichaje = result.scalar_one_or_none()
    
    if not fichaje:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fichaje no encontrado"
        )
    
    # Verify user can modify this fichaje
    if current_user.rol == UserRole.ADMIN:
        # Admin can only correct fichajes from their business
        if fichaje.negocio_id != current_user.negocio_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes corregir fichajes de otro negocio"
            )
    else:
        # Employee can only correct their own fichajes
        if fichaje.empleado_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No puedes corregir fichajes de otros empleados"
            )
    
    # Check for existing pending correction
    result = await db.execute(
        select(Correccion).where(
            Correccion.fichaje_id == data.fichaje_id,
            Correccion.estado == EstadoCorreccion.PENDIENTE
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una corrección pendiente para este fichaje"
        )
    
    # Create correction
    correccion = Correccion(
        fichaje_id=fichaje.id,
        timestamp_original=fichaje.timestamp,
        timestamp_corregido=data.timestamp_corregido,
        motivo=data.motivo,
        detalle=data.detalle,
        estado=EstadoCorreccion.PENDIENTE,
        creador_id=current_user.id
    )
    db.add(correccion)
    await db.flush()
    await db.refresh(correccion)
    
    # Get creator name
    return CorreccionResponse(
        id=correccion.id,
        fichaje_id=correccion.fichaje_id,
        timestamp_original=correccion.timestamp_original,
        timestamp_corregido=correccion.timestamp_corregido,
        motivo=correccion.motivo,
        detalle=correccion.detalle,
        estado=correccion.estado,
        creador_id=correccion.creador_id,
        creador_nombre=current_user.nombre,
        aprobador_id=None,
        aprobador_nombre=None,
        created_at=correccion.created_at,
        resolved_at=None
    )


@router.get("/pendientes", response_model=list[CorreccionPendiente])
async def get_correcciones_pendientes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending corrections that need this user's approval.
    
    - Admin sees corrections from employees
    - Employee sees corrections from admins
    """
    # Get fichajes this user can approve
    if current_user.rol == UserRole.ADMIN:
        # Admin approves employee corrections
        # Get all employee fichajes from this business
        fichaje_query = select(Fichaje.id).where(
            Fichaje.negocio_id == current_user.negocio_id
        )
    else:
        # Employee approves admin corrections on their fichajes
        fichaje_query = select(Fichaje.id).where(
            Fichaje.empleado_id == current_user.id
        )
    
    fichaje_ids = (await db.execute(fichaje_query)).scalars().all()
    
    if not fichaje_ids:
        return []
    
    # Get pending corrections NOT created by this user
    result = await db.execute(
        select(Correccion).where(
            Correccion.fichaje_id.in_(fichaje_ids),
            Correccion.estado == EstadoCorreccion.PENDIENTE,
            Correccion.creador_id != current_user.id
        ).order_by(Correccion.created_at.desc())
    )
    correcciones = result.scalars().all()
    
    # Get related data
    pendientes = []
    for c in correcciones:
        # Get fichaje
        fichaje_result = await db.execute(
            select(Fichaje).where(Fichaje.id == c.fichaje_id)
        )
        fichaje = fichaje_result.scalar_one()
        
        # Get employee
        emp_result = await db.execute(
            select(User).where(User.id == fichaje.empleado_id)
        )
        empleado = emp_result.scalar_one()
        
        # Get creator
        creator_result = await db.execute(
            select(User).where(User.id == c.creador_id)
        )
        creator = creator_result.scalar_one()
        
        pendientes.append(CorreccionPendiente(
            id=c.id,
            fichaje_id=c.fichaje_id,
            empleado_nombre=empleado.nombre,
            timestamp_original=c.timestamp_original,
            timestamp_corregido=c.timestamp_corregido,
            motivo=c.motivo,
            detalle=c.detalle,
            creador_nombre=creator.nombre,
            created_at=c.created_at
        ))
    
    return pendientes


@router.post("/{correccion_id}/aprobar", response_model=CorreccionResponse)
async def aprobar_correccion(
    correccion_id: int,
    data: CorreccionApprove,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Approve or reject a correction.
    
    LEGAL: Requires real admin password re-authentication for the approval.
    Updates the fichaje timestamp if approved.
    """
    # Get correction
    result = await db.execute(
        select(Correccion).where(Correccion.id == correccion_id)
    )
    correccion = result.scalar_one_or_none()
    
    if not correccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corrección no encontrada"
        )
    
    if correccion.estado != EstadoCorreccion.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta corrección ya fue procesada"
        )
    
    # Verify user can approve
    if correccion.creador_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes aprobar tu propia corrección"
        )
    
    # Get fichaje to verify ownership
    fichaje_result = await db.execute(
        select(Fichaje).where(Fichaje.id == correccion.fichaje_id)
    )
    fichaje = fichaje_result.scalar_one()
    
    # Verify re-authentication
    if current_user.rol == UserRole.ADMIN:
        if not current_user.password_hash or not verify_password(data.admin_password, current_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Contraseña de administrador incorrecta"
            )
    
    # Check permission
    if current_user.rol == UserRole.ADMIN:
        if fichaje.negocio_id != current_user.negocio_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta corrección"
            )
    else:
        if fichaje.empleado_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permiso para esta corrección"
            )
    
    # Process approval/rejection
    now = datetime.now(timezone.utc)
    
    if data.aprobar:
        correccion.estado = EstadoCorreccion.APROBADO
        # Keep the original fichaje immutable. Reports/read models must resolve
        # Correccion.timestamp_corregido as the effective timestamp.
    else:
        correccion.estado = EstadoCorreccion.RECHAZADO
    
    correccion.aprobador_id = current_user.id
    correccion.resolved_at = now
    
    await db.flush()
    await db.refresh(correccion)
    
    # Get names for response
    creator_result = await db.execute(
        select(User).where(User.id == correccion.creador_id)
    )
    creator = creator_result.scalar_one()
    
    return CorreccionResponse(
        id=correccion.id,
        fichaje_id=correccion.fichaje_id,
        timestamp_original=correccion.timestamp_original,
        timestamp_corregido=correccion.timestamp_corregido,
        motivo=correccion.motivo,
        detalle=correccion.detalle,
        estado=correccion.estado,
        creador_id=correccion.creador_id,
        creador_nombre=creator.nombre,
        aprobador_id=correccion.aprobador_id,
        aprobador_nombre=current_user.nombre,
        created_at=correccion.created_at,
        resolved_at=correccion.resolved_at
    )


@router.get("/historial", response_model=list[CorreccionResponse])
async def get_historial_correcciones(
    empleado_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get correction history for audit purposes.
    
    LEGAL: Full audit trail of all corrections.
    """
    # Build query based on user role
    if current_user.rol == UserRole.ADMIN:
        # Admin sees all corrections for their business
        fichaje_subquery = select(Fichaje.id).where(
            Fichaje.negocio_id == current_user.negocio_id
        )
        if empleado_id:
            fichaje_subquery = fichaje_subquery.where(
                Fichaje.empleado_id == empleado_id
            )
    else:
        # Employee sees only their corrections
        fichaje_subquery = select(Fichaje.id).where(
            Fichaje.empleado_id == current_user.id
        )
    
    fichaje_ids = (await db.execute(fichaje_subquery)).scalars().all()
    
    if not fichaje_ids:
        return []
    
    result = await db.execute(
        select(Correccion).where(
            Correccion.fichaje_id.in_(fichaje_ids)
        ).order_by(Correccion.created_at.desc()).limit(50)
    )
    correcciones = result.scalars().all()
    
    # Enrich with names
    response = []
    for c in correcciones:
        creator_result = await db.execute(
            select(User).where(User.id == c.creador_id)
        )
        creator = creator_result.scalar_one()
        
        aprobador_nombre = None
        if c.aprobador_id:
            apr_result = await db.execute(
                select(User).where(User.id == c.aprobador_id)
            )
            aprobador = apr_result.scalar_one_or_none()
            if aprobador:
                aprobador_nombre = aprobador.nombre
        
        response.append(CorreccionResponse(
            id=c.id,
            fichaje_id=c.fichaje_id,
            timestamp_original=c.timestamp_original,
            timestamp_corregido=c.timestamp_corregido,
            motivo=c.motivo,
            detalle=c.detalle,
            estado=c.estado,
            creador_id=c.creador_id,
            creador_nombre=creator.nombre,
            aprobador_id=c.aprobador_id,
            aprobador_nombre=aprobador_nombre,
            created_at=c.created_at,
            resolved_at=c.resolved_at
        ))
    
    return response


# ============================================
# ENDPOINTS PARA EMPLEADOS (autenticación por PIN)
# ============================================

@router.post("/pendientes-empleado", response_model=list[CorreccionPendiente])
async def get_correcciones_pendientes_empleado(
    data: CorreccionesPendientesEmpleadoRequest,
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get pending corrections for an employee.
    Returns corrections proposed by admin that need employee approval.
    Session-authenticated employees only.
    """
    empleado = await resolve_employee_user(
        current_user=current_user,
        negocio_id=data.negocio_id,
    )
    
    # Get fichajes for this employee
    fichaje_result = await db.execute(
        select(Fichaje.id).where(Fichaje.empleado_id == empleado.id)
    )
    fichaje_ids = fichaje_result.scalars().all()
    
    if not fichaje_ids:
        return []
    
    # Get pending corrections NOT created by this employee (i.e., from admin)
    result = await db.execute(
        select(Correccion).where(
            Correccion.fichaje_id.in_(fichaje_ids),
            Correccion.estado == EstadoCorreccion.PENDIENTE,
            Correccion.creador_id != empleado.id
        ).order_by(Correccion.created_at.desc())
    )
    correcciones = result.scalars().all()
    
    pendientes = []
    for c in correcciones:
        # Get creator name
        creator_result = await db.execute(
            select(User).where(User.id == c.creador_id)
        )
        creator = creator_result.scalar_one()
        
        pendientes.append(CorreccionPendiente(
            id=c.id,
            fichaje_id=c.fichaje_id,
            empleado_nombre=empleado.nombre,
            timestamp_original=c.timestamp_original,
            timestamp_corregido=c.timestamp_corregido,
            motivo=c.motivo,
            detalle=c.detalle,
            creador_nombre=creator.nombre,
            created_at=c.created_at
        ))
    
    return pendientes


@router.post("/{correccion_id}/aprobar-empleado", response_model=CorreccionResponse)
async def aprobar_correccion_empleado(
    correccion_id: int,
    data: CorreccionApproveEmpleado,
    request: Request,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Employee approves/rejects a correction.

    Employees use their authenticated session; no PIN re-entry is required.
    Updates the fichaje timestamp if approved.
    """
    empleado = await resolve_employee_user(
        current_user=current_user,
        negocio_id=data.negocio_id,
    )
    
    # Get correction
    result = await db.execute(
        select(Correccion).where(Correccion.id == correccion_id)
    )
    correccion = result.scalar_one_or_none()
    
    if not correccion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Corrección no encontrada"
        )
    
    if correccion.estado != EstadoCorreccion.PENDIENTE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta corrección ya fue procesada"
        )
    
    # Get fichaje to verify ownership
    fichaje_result = await db.execute(
        select(Fichaje).where(Fichaje.id == correccion.fichaje_id)
    )
    fichaje = fichaje_result.scalar_one()
    
    # Verify this employee owns the fichaje
    if fichaje.empleado_id != empleado.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes aprobar correcciones de otros empleados"
        )
    
    # Verify employee is not the creator
    if correccion.creador_id == empleado.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No puedes aprobar tu propia corrección"
        )
    
    # Process approval/rejection
    now = datetime.now(timezone.utc)
    
    if data.aprobar:
        correccion.estado = EstadoCorreccion.APROBADO
        # Keep the original fichaje immutable. Reports/read models must resolve
        # Correccion.timestamp_corregido as the effective timestamp.
    else:
        correccion.estado = EstadoCorreccion.RECHAZADO
    
    correccion.aprobador_id = empleado.id
    correccion.resolved_at = now
    
    await db.flush()
    await db.refresh(correccion)
    
    # Get creator name for response
    creator_result = await db.execute(
        select(User).where(User.id == correccion.creador_id)
    )
    creator = creator_result.scalar_one()
    
    return CorreccionResponse(
        id=correccion.id,
        fichaje_id=correccion.fichaje_id,
        timestamp_original=correccion.timestamp_original,
        timestamp_corregido=correccion.timestamp_corregido,
        motivo=correccion.motivo,
        detalle=correccion.detalle,
        estado=correccion.estado,
        creador_id=correccion.creador_id,
        creador_nombre=creator.nombre,
        aprobador_id=correccion.aprobador_id,
        aprobador_nombre=empleado.nombre,
        created_at=correccion.created_at,
        resolved_at=correccion.resolved_at
    )

