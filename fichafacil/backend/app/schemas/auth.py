"""
FichaFacil MVP - Auth Schemas
Authentication and authorization schemas.
"""
from pydantic import BaseModel, Field, EmailStr
from app.models.user import UserRole


class AdminLogin(BaseModel):
    """Schema for admin login."""
    email: EmailStr
    password: str


class EmpleadoLogin(BaseModel):
    """Schema for employee login (PIN)."""
    negocio_id: int
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data embedded in JWT token."""
    user_id: int
    negocio_id: int
    rol: UserRole
    exp: int


class AdminRegister(BaseModel):
    """Schema for registering new business with admin."""
    # Business data
    negocio_nombre: str = Field(..., min_length=2, max_length=100)
    negocio_slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    negocio_direccion: str | None = None
    negocio_nif: str | None = None
    negocio_lat: float | None = Field(None, ge=-90, le=90)
    negocio_lon: float | None = Field(None, ge=-180, le=180)
    
    # Admin data
    admin_nombre: str = Field(..., min_length=2, max_length=100)
    admin_email: EmailStr
    admin_password: str = Field(..., min_length=6)


class CurrentUser(BaseModel):
    """Current authenticated user info."""
    id: int
    nombre: str
    email: str | None
    rol: UserRole
    negocio_id: int
    negocio_nombre: str
