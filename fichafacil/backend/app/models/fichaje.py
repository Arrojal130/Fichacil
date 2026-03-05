"""
FichaFacil MVP - Fichaje (Clock Record) Model
Core entity for legal compliance. IMMUTABLE - never delete, only correct.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Float, DateTime, Integer, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class TipoFichaje(str, Enum):
    """Type of clock record."""
    ENTRADA = "ENTRADA"
    SALIDA = "SALIDA"


class Fichaje(Base):
    """
    Clock record (entry or exit).
    LEGAL REQUIREMENT: Immutable. Timestamp from server.
    Corrections are stored in separate table with audit trail.
    """
    __tablename__ = "fichajes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Type
    tipo: Mapped[TipoFichaje] = mapped_column(SQLEnum(TipoFichaje), nullable=False)
    
    # SERVER timestamp (never trust client)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    
    # Geolocation (optional but recommended)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    distancia_metros: Mapped[float | None] = mapped_column(Float, nullable=True)  # Distance from business
    
    # Client metadata (for audit)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # Relationships
    empleado_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    negocio_id: Mapped[int] = mapped_column(Integer, ForeignKey("negocios.id"), nullable=False, index=True)
    
    # Audit (immutable - created_at only)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Relationships
    empleado: Mapped["User"] = relationship("User", back_populates="fichajes")
    negocio: Mapped["Negocio"] = relationship("Negocio", back_populates="fichajes")
    correcciones: Mapped[list["Correccion"]] = relationship("Correccion", back_populates="fichaje")
    
    def __repr__(self) -> str:
        return f"<Fichaje {self.tipo.value} {self.timestamp}>"


# Import at end to avoid circular import
from app.models.user import User
from app.models.negocio import Negocio
from app.models.correccion import Correccion
