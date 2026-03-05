"""
FichaFacil MVP - Negocio (Business) Model
Multi-tenant: each business is independent.
"""
from datetime import datetime
from sqlalchemy import String, Float, DateTime, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Negocio(Base):
    """
    Business entity (bar, salon, workshop, etc.)
    Each business has one owner (admin) and multiple employees.
    """
    __tablename__ = "negocios"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    direccion: Mapped[str | None] = mapped_column(String(255), nullable=True)
    nif: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Geolocation center point
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Audit
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    users: Mapped[list["User"]] = relationship("User", back_populates="negocio")
    fichajes: Mapped[list["Fichaje"]] = relationship("Fichaje", back_populates="negocio")
    
    def __repr__(self) -> str:
        return f"<Negocio {self.nombre} ({self.slug})>"


# Import at end to avoid circular import
from app.models.user import User
from app.models.fichaje import Fichaje
