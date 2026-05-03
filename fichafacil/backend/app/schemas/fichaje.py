"""
FichaFacil MVP - Fichaje Schemas
Validation and serialization for clock records.
"""
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict, Field
from app.models.fichaje import TipoFichaje


class FichajeCreate(BaseModel):
    """Schema for creating a clock record (employee)."""
    negocio_id: int
    pin: str | None = Field(None, min_length=4, max_length=4, pattern=r"^\d{4}$")
    tipo: TipoFichaje
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)


class EmpleadoPinRequest(BaseModel):
    """Schema for employee session-authenticated reads."""
    negocio_id: int


class HistorialEmpleadoRequest(EmpleadoPinRequest):
    """Schema for employee history lookup."""
    dias: int = Field(7, ge=1, le=366)


class FichajeResponse(BaseModel):
    """Schema for clock record response."""
    id: int
    tipo: TipoFichaje
    timestamp: datetime
    lat: float | None
    lon: float | None
    distancia_metros: float | None
    empleado_id: int
    negocio_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FichajeConEmpleado(FichajeResponse):
    """Fichaje with employee name (for dashboard)."""
    empleado_nombre: str
    empleado_dni: str | None = None


class FichajeDia(BaseModel):
    """Single day summary for an employee."""
    fecha: date
    entrada: datetime | None
    salida: datetime | None
    horas_trabajadas: str | None  # Format: "8h 30m"
    distancia_entrada: float | None
    distancia_salida: float | None
    tiene_correccion: bool = False


class DashboardFichaje(BaseModel):
    """Dashboard row for realtime view."""
    empleado_id: int
    empleado_nombre: str
    entrada: datetime | None
    salida: datetime | None
    horas_trabajadas: str | None
    distancia_metros: float | None
    estado: str  # "completo", "pendiente_salida", "no_fichado"
    alerta: str | None  # "lejos", "sin_salida_ayer", etc.


class FichajeConfirmacion(BaseModel):
    """Response after successful clock."""
    mensaje: str
    tipo: TipoFichaje
    timestamp: datetime
    distancia_metros: float | None
    alerta_distancia: bool = False


class PDFRequest(BaseModel):
    """Request to generate PDF report."""
    empleado_id: int | None = None  # None = all employees
    fecha_inicio: date
    fecha_fin: date


class EstadisticasSemana(BaseModel):
    """Weekly statistics for dashboard."""
    total_horas: str  # "46h 45m"
    horas_extra: str | None  # "6h 45m" if > 40h
    dias_trabajados: int
    incidencias: int
