"""
FichaFacil MVP - Authentication Router
Handles admin and employee authentication.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import Negocio, User
from app.models.user import UserRole
from app.schemas.auth import (
    AdminLogin,
    AdminRegister,
    EmpleadoLogin,
    Token,
    CurrentUser
)
from app.utils.security import (
    hash_password,
    verify_password,
    hash_pin,
    verify_pin,
    create_access_token,
    get_current_user,
    check_pin_rate_limit,
    record_pin_attempt,
    get_client_ip
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register_business(
    data: AdminRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new business with its admin user.
    This is the onboarding flow.
    """
    # Check if slug already exists
    existing = await db.execute(
        select(Negocio).where(Negocio.slug == data.negocio_slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un negocio con ese identificador"
        )
    
    # Check if email already exists
    existing_email = await db.execute(
        select(User).where(User.email == data.admin_email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un usuario con ese email"
        )
    
    # Create business
    negocio = Negocio(
        nombre=data.negocio_nombre,
        slug=data.negocio_slug,
        direccion=data.negocio_direccion,
        nif=data.negocio_nif,
        lat=data.negocio_lat,
        lon=data.negocio_lon
    )
    db.add(negocio)
    await db.flush()  # Get the ID
    
    # Create admin user
    admin = User(
        nombre=data.admin_nombre,
        email=data.admin_email,
        password_hash=hash_password(data.admin_password),
        rol=UserRole.ADMIN,
        negocio_id=negocio.id
    )
    db.add(admin)
    await db.flush()
    
    # Generate token
    token = create_access_token(
        user_id=admin.id,
        negocio_id=negocio.id,
        rol=UserRole.ADMIN
    )
    
    return Token(access_token=token)


@router.post("/login/admin", response_model=Token)
async def login_admin(
    data: AdminLogin,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login as admin (email + password)."""
    result = await db.execute(
        select(User).where(
            User.email == data.email,
            User.rol == UserRole.ADMIN
        )
    )
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos"
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    token = create_access_token(
        user_id=user.id,
        negocio_id=user.negocio_id,
        rol=user.rol
    )
    
    # Set cookie for convenience
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,  # HTTPS only
        samesite="lax",
        max_age=3600  # 1 hour
    )
    
    return Token(access_token=token)


@router.post("/login/empleado", response_model=Token)
async def login_empleado(
    data: EmpleadoLogin,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """
    Login as employee (negocio + PIN).
    PIN validates against specific business.
    Rate limited: 5 attempts per IP per hour.
    """
    client_ip = get_client_ip(request)
    
    # Check rate limit before processing
    check_pin_rate_limit(data.negocio_id, client_ip)
    
    # Get all employees for this business
    result = await db.execute(
        select(User).where(
            User.negocio_id == data.negocio_id,
            User.rol == UserRole.EMPLEADO,
            User.active == True
        )
    )
    employees = result.scalars().all()
    
    # Check PIN against all employees (PIN is unique per business)
    for emp in employees:
        if emp.pin_hash and verify_pin(data.pin, emp.pin_hash):
            # Success - clear rate limit
            record_pin_attempt(data.negocio_id, client_ip, success=True)
            
            token = create_access_token(
                user_id=emp.id,
                negocio_id=emp.negocio_id,
                rol=emp.rol
            )
            
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                secure=True,
                samesite="lax",
                max_age=3600
            )
            
            return Token(access_token=token)
    
    # Failed - record attempt
    record_pin_attempt(data.negocio_id, client_ip, success=False)
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="PIN incorrecto"
    )


@router.get("/me", response_model=CurrentUser)
async def get_me(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current authenticated user info."""
    # Load business name
    result = await db.execute(
        select(Negocio).where(Negocio.id == current_user.negocio_id)
    )
    negocio = result.scalar_one()
    
    return CurrentUser(
        id=current_user.id,
        nombre=current_user.nombre,
        email=current_user.email,
        rol=current_user.rol,
        negocio_id=current_user.negocio_id,
        negocio_nombre=negocio.nombre
    )


@router.post("/logout")
async def logout(response: Response):
    """Logout by clearing the cookie."""
    response.delete_cookie("access_token")
    return {"message": "Sesión cerrada"}
