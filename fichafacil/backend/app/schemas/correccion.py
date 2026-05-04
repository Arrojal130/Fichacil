"""
FichaFacil MVP - Correccion Schemas
Validation and serialization for correction records.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.correccion import EstadoCorreccion, MotivoCorreccion


class CorreccionCreate(BaseModel):
    """Schema for creating a correction."""
    fichaje_id: int
    timestamp_corregido: datetime
    motivo: MotivoCorreccion
    detalle: str | None = Field(None, max_length=500)


class CorreccionApprove(BaseModel):
    """Schema for approving/rejecting a correction."""
    admin_password: str = Field(..., min_length=1)
    aprobar: bool  # True = approve, False = reject


class CorreccionApproveEmpleado(BaseModel):
    """Schema for employee approving correction with a session token."""
    negocio_id: int
    aprobar: bool  # True = approve, False = reject


class CorreccionesPendientesEmpleadoRequest(BaseModel):
    """Schema for employee pending corrections lookup with a session token."""
    negocio_id: int


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
    model_config = ConfigDict(from_attributes=True)


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
