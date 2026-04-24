"""
FichaFacil MVP - Negocio Schemas
Validation and serialization for business entities.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class NegocioBase(BaseModel):
    """Base schema for business data."""
    nombre: str = Field(..., min_length=2, max_length=100)
    direccion: str | None = None
    nif: str | None = None
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)


class NegocioCreate(NegocioBase):
    """Schema for creating a new business."""
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")


class NegocioUpdate(BaseModel):
    """Schema for updating a business."""
    nombre: str | None = Field(None, min_length=2, max_length=100)
    direccion: str | None = None
    nif: str | None = None
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)


class NegocioResponse(NegocioBase):
    """Schema for business response."""
    id: int
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NegocioListItem(BaseModel):
    """Minimal schema for business list (employee search)."""
    id: int
    nombre: str
    slug: str
    model_config = ConfigDict(from_attributes=True)
