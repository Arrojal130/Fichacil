"""
FichaFacil MVP - Correccion (Correction) Model
Audit trail for all modifications. Requires mutual approval.
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, DateTime, Integer, ForeignKey, Text, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EstadoCorreccion(str, Enum):
    """Correction status."""
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class MotivoCorreccion(str, Enum):
    """Predefined correction reasons."""
    OLVIDO = "Olvido"
    ERROR = "Error"
    ACUERDO = "Acuerdo"
    OTRO = "Otro"


class Correccion(Base):
    """
    Correction record with full audit trail.
    LEGAL: Mutual approval required (owner<->employee).
    IMMUTABLE: Never delete corrections.
    """
    __tablename__ = "correcciones"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Original fichaje reference
    fichaje_id: Mapped[int] = mapped_column(Integer, ForeignKey("fichajes.id"), nullable=False, index=True)
    
    # Timestamps
    timestamp_original: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    timestamp_corregido: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    # Reason with detail
    motivo: Mapped[MotivoCorreccion] = mapped_column(SQLEnum(MotivoCorreccion), nullable=False)
    detalle: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Workflow
    estado: Mapped[EstadoCorreccion] = mapped_column(
        SQLEnum(EstadoCorreccion),
        default=EstadoCorreccion.PENDIENTE,
        nullable=False
    )
    
    # Who proposed the correction
    creador_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Who approved/rejected (null if pending)
    aprobador_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Audit timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    fichaje: Mapped["Fichaje"] = relationship("Fichaje", back_populates="correcciones")
    creador: Mapped["User"] = relationship(
        "User",
        foreign_keys=[creador_id],
        back_populates="correcciones_creadas"
    )
    aprobador: Mapped["User"] = relationship(
        "User",
        foreign_keys=[aprobador_id],
        back_populates="correcciones_aprobadas"
    )
    
    def __repr__(self) -> str:
        return f"<Correccion {self.id} [{self.estado.value}]>"


# Import at end to avoid circular import
from app.models.fichaje import Fichaje
from app.models.user import User
