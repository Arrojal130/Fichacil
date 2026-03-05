"""
FichaFacil MVP - User Schemas
Validation and serialization for user entities.
"""
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from app.models.user import UserRole


class UserBase(BaseModel):
    """Base schema for user data."""
    nombre: str = Field(..., min_length=2, max_length=100)
    dni: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user."""
    email: EmailStr | None = None
    rol: UserRole = UserRole.EMPLEADO
    negocio_id: int
    password: str | None = Field(None, min_length=6)  # For admins
    pin: str | None = Field(None, min_length=4, max_length=4, pattern=r"^\d{4}$")  # For employees


class EmpleadoCreate(BaseModel):
    """Simplified schema for creating employee by admin."""
    nombre: str = Field(..., min_length=2, max_length=100)
    dni: str | None = None
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")


class UserUpdate(BaseModel):
    """Schema for updating user."""
    nombre: str | None = Field(None, min_length=2, max_length=100)
    dni: str | None = None
    email: EmailStr | None = None
    active: bool | None = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    email: str | None
    rol: UserRole
    negocio_id: int
    active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class EmpleadoResponse(BaseModel):
    """Minimal employee info for admin dashboard."""
    id: int
    nombre: str
    dni: str | None
    active: bool
    
    class Config:
        from_attributes = True


class EmpleadoPublic(BaseModel):
    """Public employee info (no sensitive data)."""
    id: int
    nombre: str
    
    class Config:
        from_attributes = True
