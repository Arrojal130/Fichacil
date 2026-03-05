"""
FichaFacil MVP - Security Utilities
JWT tokens, password hashing, PIN hashing.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import get_settings
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import TokenData

settings = get_settings()

# Password context for bcrypt hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def hash_pin(pin: str) -> str:
    """Hash a 4-digit PIN using bcrypt."""
    return pwd_context.hash(pin)


def verify_pin(plain_pin: str, hashed_pin: str) -> bool:
    """Verify a PIN against a hash."""
    return pwd_context.verify(plain_pin, hashed_pin)


def create_access_token(
    user_id: int,
    negocio_id: int,
    rol: UserRole,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.access_token_expire_minutes
        )
    
    to_encode = {
        "user_id": user_id,
        "negocio_id": negocio_id,
        "rol": rol.value,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.secret_key,
        algorithm=settings.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return TokenData(
            user_id=payload["user_id"],
            negocio_id=payload["negocio_id"],
            rol=UserRole(payload["rol"]),
            exp=payload["exp"]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get the current authenticated user from JWT token."""
    # Check for token in Authorization header
    token = None
    if credentials:
        token = credentials.credentials
    
    # Fallback to cookie
    if not token:
        token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )
    
    token_data = decode_token(token)
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.id == token_data.user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )
    
    if not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado"
        )
    
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user and verify they are an admin."""
    if current_user.rol != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requieren permisos de administrador"
        )
    return current_user


async def get_optional_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    try:
        return await get_current_user(request, credentials, db)
    except HTTPException:
        return None


# ============================================
# PIN RATE LIMITING
# Simple in-memory rate limiter (MVP solution)
# For production: use Redis or database-backed rate limiting
# ============================================

from collections import defaultdict
from threading import Lock

# Configuration
PIN_MAX_ATTEMPTS = 5
PIN_WINDOW_MINUTES = 60

# In-memory storage: {(negocio_id, pin_hash): [(timestamp, success), ...]}
_pin_attempts: dict[str, list[datetime]] = defaultdict(list)
_pin_lock = Lock()


def _get_rate_limit_key(negocio_id: int, identifier: str) -> str:
    """Generate rate limit key from negocio and identifier (IP or PIN)."""
    return f"{negocio_id}:{identifier}"


def check_pin_rate_limit(negocio_id: int, client_ip: str) -> None:
    """
    Check if PIN attempts are rate limited for this negocio/IP combo.
    Raises HTTPException if too many attempts.
    
    Args:
        negocio_id: Business ID
        client_ip: Client IP address
    """
    key = _get_rate_limit_key(negocio_id, client_ip)
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(minutes=PIN_WINDOW_MINUTES)
    
    with _pin_lock:
        # Clean old attempts
        _pin_attempts[key] = [
            ts for ts in _pin_attempts[key]
            if ts > window_start
        ]
        
        # Check count
        if len(_pin_attempts[key]) >= PIN_MAX_ATTEMPTS:
            minutes_left = PIN_WINDOW_MINUTES - int((now - _pin_attempts[key][0]).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Demasiados intentos fallidos. Espera {minutes_left} minutos."
            )


def record_pin_attempt(negocio_id: int, client_ip: str, success: bool) -> None:
    """
    Record a PIN attempt (only failures count towards rate limit).
    
    Args:
        negocio_id: Business ID
        client_ip: Client IP address
        success: Whether the attempt was successful
    """
    if success:
        # Clear attempts on success
        key = _get_rate_limit_key(negocio_id, client_ip)
        with _pin_lock:
            _pin_attempts.pop(key, None)
    else:
        # Record failed attempt
        key = _get_rate_limit_key(negocio_id, client_ip)
        with _pin_lock:
            _pin_attempts[key].append(datetime.now(timezone.utc))


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    # Check for proxy headers
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fallback to direct client
    return request.client.host if request.client else "unknown"
