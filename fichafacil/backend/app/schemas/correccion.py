"""
FichaFacil MVP - Correccion Schemas
Validation and serialization for correction records.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from app.models.correccion import EstadoCorreccion, MotivoCorreccion


class CorreccionCreate(BaseModel):
    """Schema for creating a correction."""
    fichaje_id: int
    timestamp_corregido: datetime
    motivo: MotivoCorreccion
    detalle: str | None = Field(None, max_length=500)


class CorreccionApprove(BaseModel):
    """Schema for approving/rejecting a correction."""
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    aprobar: bool  # True = approve, False = reject


class CorreccionApproveEmpleado(BaseModel):
    """Schema for employee approving correction with PIN (no JWT)."""
    negocio_id: int
    pin: str = Field(..., min_length=4, max_length=4, pattern=r"^\d{4}$")
    aprobar: bool  # True = approve, False = reject


class CorreccionResponse(BaseModel):
    """Schema for correction response."""
    id: int
    fichaje_id: int
    timestamp_original: datetime
    timestamp_corregido: datetime
    motivo: MotivoCorreccion
    detalle: str | None
    estado: EstadoCorreccion
    creador_id: int
    creador_nombre: str
    aprobador_id: int | None
    aprobador_nombre: str | None
    created_at: datetime
    resolved_at: datetime | None
    
    class Config:
        from_attributes = True


class CorreccionPendiente(BaseModel):
    """Pending correction for notifications."""
    id: int
    fichaje_id: int
    empleado_nombre: str
    timestamp_original: datetime
    timestamp_corregido: datetime
    motivo: MotivoCorreccion
    detalle: str | None
    creador_nombre: str
    created_at: datetime
