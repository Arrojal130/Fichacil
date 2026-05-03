"""
FichaFacil MVP - Security Utilities
JWT tokens, password hashing, PIN hashing.
"""
from datetime import datetime, timedelta, timezone
import ipaddress
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


async def resolve_employee_user(
    *,
    current_user: User | None = None,
    negocio_id: int,
) -> User:
    """
    Resolve an authenticated employee session.

    Employee-facing endpoints now require a real JWT/cookie session. PINs are
    only accepted at the dedicated login endpoint.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado"
        )

    if current_user.rol != UserRole.EMPLEADO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Se requiere autenticación de empleado"
        )
    if current_user.negocio_id != negocio_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado para este negocio"
        )
    return current_user


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


def _configured_trusted_proxy_networks() -> list[ipaddress._BaseNetwork]:
    """Return trusted proxy IP ranges configured through TRUSTED_PROXY_IPS."""
    networks: list[ipaddress._BaseNetwork] = []
    for raw_entry in settings.trusted_proxy_ips.split(","):
        entry = raw_entry.strip()
        if not entry:
            continue
        try:
            networks.append(ipaddress.ip_network(entry, strict=False))
        except ValueError:
            # Ignore malformed entries so a typo does not make all proxy headers trusted.
            continue
    return networks


def _is_trusted_proxy(host: str | None) -> bool:
    """Return whether the direct peer is an explicitly trusted proxy."""
    if not host:
        return False
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in network for network in _configured_trusted_proxy_networks())


def _first_untrusted_forwarded_for_ip(forwarded_for: str) -> str | None:
    """Resolve the original client from an X-Forwarded-For chain.

    X-Forwarded-For is ordered as: client, proxy1, proxy2. When the direct
    peer is trusted, walk the chain from right to left and skip trusted proxy
    hops, returning the first untrusted address.
    """
    candidates = [part.strip() for part in forwarded_for.split(",") if part.strip()]
    if not candidates:
        return None

    trusted_networks = _configured_trusted_proxy_networks()
    for candidate in reversed(candidates):
        try:
            ip = ipaddress.ip_address(candidate)
        except ValueError:
            continue
        if not any(ip in network for network in trusted_networks):
            return str(ip)

    return candidates[0]


def get_client_ip(request: Request) -> str:
    """Extract client IP without trusting spoofable proxy headers by default."""
    direct_client_ip = request.client.host if request.client else "unknown"
    if not _is_trusted_proxy(direct_client_ip):
        return direct_client_ip

    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        resolved_ip = _first_untrusted_forwarded_for_ip(forwarded)
        if resolved_ip:
            return resolved_ip

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    return direct_client_ip
