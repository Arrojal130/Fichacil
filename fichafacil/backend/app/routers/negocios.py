"""
FichaFacil MVP - Negocios (Business) Router
Business management and employee administration.
"""
import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Negocio, User
from app.models.user import UserRole
from app.schemas.negocio import (
    NegocioResponse,
    NegocioUpdate,
    NegocioListItem
)
from app.schemas.user import (
    EmpleadoCreate,
    EmpleadoResponse,
    UserResponse
)
from app.utils.security import (
    get_current_admin,
    get_current_user,
    hash_pin,
    verify_pin,
)

router = APIRouter(prefix="/negocios", tags=["Negocios"])


def validate_employee_pin(pin: str) -> None:
    """Validate employee PIN format before hashing or comparing it."""
    if not re.fullmatch(r"\d{4}", pin):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El PIN debe tener exactamente 4 dígitos"
        )


def ensure_unique_employee_pin(
    employees: list[User],
    pin: str,
    *,
    exclude_user_id: int | None = None,
) -> None:
    """Reject duplicate employee PINs within the same business."""
    for emp in employees:
        if exclude_user_id is not None and emp.id == exclude_user_id:
            continue

        if emp.pin_hash and verify_pin(pin, emp.pin_hash):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Este PIN ya está en uso por otro empleado"
            )


@router.get("/search", response_model=list[NegocioListItem])
async def search_negocios(
    q: str = "",
    db: AsyncSession = Depends(get_db)
):
    """
    Search businesses by name (for employee login).
    Public endpoint - returns minimal info.
    """
    query = select(Negocio).order_by(Negocio.nombre)
    
    if q:
        query = query.where(Negocio.nombre.ilike(f"%{q}%"))
    
    result = await db.execute(query.limit(10))
    negocios = result.scalars().all()
    
    return [NegocioListItem.model_validate(n) for n in negocios]


@router.get("/me", response_model=NegocioResponse)
async def get_my_negocio(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get the current user's business."""
    result = await db.execute(
        select(Negocio).where(Negocio.id == current_user.negocio_id)
    )
    negocio = result.scalar_one_or_none()
    
    if not negocio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado"
        )
    
    return NegocioResponse.model_validate(negocio)


@router.patch("/me", response_model=NegocioResponse)
async def update_my_negocio(
    data: NegocioUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update the current admin's business."""
    result = await db.execute(
        select(Negocio).where(Negocio.id == current_user.negocio_id)
    )
    negocio = result.scalar_one()
    
    # Update only provided fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(negocio, field, value)
    
    await db.flush()
    await db.refresh(negocio)
    
    return NegocioResponse.model_validate(negocio)


# === Employee Management ===

@router.get("/empleados", response_model=list[EmpleadoResponse])
async def list_empleados(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """List all employees for the admin's business."""
    result = await db.execute(
        select(User).where(
            User.negocio_id == current_user.negocio_id,
            User.rol == UserRole.EMPLEADO
        ).order_by(User.nombre)
    )
    empleados = result.scalars().all()
    
    return [EmpleadoResponse.model_validate(e) for e in empleados]


@router.post("/empleados", response_model=EmpleadoResponse, status_code=status.HTTP_201_CREATED)
async def create_empleado(
    data: EmpleadoCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Create a new employee for the admin's business."""
    # Check PIN uniqueness within business
    existing = await db.execute(
        select(User).where(
            User.negocio_id == current_user.negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        )
    )
    existing_employees = existing.scalars().all()
    validate_employee_pin(data.pin)
    ensure_unique_employee_pin(existing_employees, data.pin)

    empleado = User(
        nombre=data.nombre,
        dni=data.dni,
        pin_hash=hash_pin(data.pin),
        rol=UserRole.EMPLEADO,
        negocio_id=current_user.negocio_id
    )
    db.add(empleado)
    await db.flush()
    await db.refresh(empleado)
    
    return EmpleadoResponse.model_validate(empleado)


@router.get("/empleados/{empleado_id}", response_model=UserResponse)
async def get_empleado(
    empleado_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get employee details."""
    result = await db.execute(
        select(User).where(
            User.id == empleado_id,
            User.negocio_id == current_user.negocio_id
        )
    )
    empleado = result.scalar_one_or_none()
    
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    return UserResponse.model_validate(empleado)


@router.patch("/empleados/{empleado_id}", response_model=EmpleadoResponse)
async def update_empleado(
    empleado_id: int,
    nombre: str = None,
    dni: str = None,
    pin: str = None,
    active: bool = None,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Update an employee."""
    result = await db.execute(
        select(User).where(
            User.id == empleado_id,
            User.negocio_id == current_user.negocio_id,
            User.rol == UserRole.EMPLEADO
        )
    )
    empleado = result.scalar_one_or_none()
    
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    if nombre is not None:
        empleado.nombre = nombre
    if dni is not None:
        empleado.dni = dni
    if pin is not None:
        existing = await db.execute(
            select(User).where(
                User.negocio_id == current_user.negocio_id,
                User.rol == UserRole.EMPLEADO,
                User.active == True
            )
        )
        existing_employees = existing.scalars().all()
        validate_employee_pin(pin)
        ensure_unique_employee_pin(
            existing_employees,
            pin,
            exclude_user_id=empleado.id,
        )
        empleado.pin_hash = hash_pin(pin)
    if active is not None:
        empleado.active = active
    
    await db.flush()
    await db.refresh(empleado)
    
    return EmpleadoResponse.model_validate(empleado)


@router.delete("/empleados/{empleado_id}")
async def deactivate_empleado(
    empleado_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate an employee (soft delete)."""
    result = await db.execute(
        select(User).where(
            User.id == empleado_id,
            User.negocio_id == current_user.negocio_id,
            User.rol == UserRole.EMPLEADO
        )
    )
    empleado = result.scalar_one_or_none()
    
    if not empleado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empleado no encontrado"
        )
    
    # Soft delete - never hard delete for legal compliance
    empleado.active = False
    await db.flush()
    
    return {"message": "Empleado desactivado"}
