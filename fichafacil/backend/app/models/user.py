"""
FichaFacil MVP - User Model
Two roles: admin (owner) and empleado (employee).
"""
from datetime import datetime
from enum import Enum
from sqlalchemy import String, Boolean, DateTime, Integer, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class UserRole(str, Enum):
    """User role in the system."""
    ADMIN = "admin"
    EMPLEADO = "empleado"


class User(Base):
    """
    User entity (owner or employee).
    Employees authenticate with PIN, admins with email+password.
    """
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    dni: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # Authentication
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # For admins
    pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # For employees (4 digits)
    
    # Role and status
    rol: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.EMPLEADO, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Business relationship
    negocio_id: Mapped[int] = mapped_column(Integer, ForeignKey("negocios.id"), nullable=False, index=True)
    
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
    negocio: Mapped["Negocio"] = relationship("Negocio", back_populates="users")
    fichajes: Mapped[list["Fichaje"]] = relationship("Fichaje", back_populates="empleado")
    correcciones_creadas: Mapped[list["Correccion"]] = relationship(
        "Correccion",
        foreign_keys="Correccion.creador_id",
        back_populates="creador"
    )
    correcciones_aprobadas: Mapped[list["Correccion"]] = relationship(
        "Correccion",
        foreign_keys="Correccion.aprobador_id",
        back_populates="aprobador"
    )
    
    def __repr__(self) -> str:
        return f"<User {self.nombre} ({self.rol.value})>"


# Import at end to avoid circular import
from app.models.negocio import Negocio
from app.models.fichaje import Fichaje
from app.models.correccion import Correccion
