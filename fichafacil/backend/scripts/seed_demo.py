#!/usr/bin/env python3
"""Seed a minimal FichaFácil demo business.

Creates exactly:
- 1 negocio demo
- 1 admin user
- 2 employee users

Safe to run repeatedly: if the negocio slug already exists, it prints the
existing credentials and does not duplicate rows.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from sqlalchemy import select

from app.database import async_session, init_db
from app.models.negocio import Negocio
from app.models.user import User, UserRole
from app.utils.security import hash_password, hash_pin

DEMO_SLUG = "demo-fichafacil"
ADMIN_EMAIL = "gestion@test.local"
ADMIN_PASSWORD = "Test1234!"
EMPLOYEE_1_DNI = "00000001T"
EMPLOYEE_1_PIN = "1111"
EMPLOYEE_2_DNI = "00000002R"
EMPLOYEE_2_PIN = "2222"


async def seed_demo() -> None:
    await init_db()
    async with async_session() as session:
        existing = await session.scalar(select(Negocio).where(Negocio.slug == DEMO_SLUG))
        if existing:
            print(f"Demo already exists: negocio_id={existing.id}, slug={DEMO_SLUG}")
            print_credentials()
            return

        negocio = Negocio(
            nombre="Negocio Demo",
            slug=DEMO_SLUG,
            direccion="Calle Demo 1",
            nif="B12345678",
        )
        session.add(negocio)
        await session.flush()

        session.add_all(
            [
                User(
                    nombre="Gestión Demo",
                    email=ADMIN_EMAIL,
                    password_hash=hash_password(ADMIN_PASSWORD),
                    rol=UserRole.ADMIN,
                    active=True,
                    negocio_id=negocio.id,
                ),
                User(
                    nombre="Empleado Demo 1",
                    dni=EMPLOYEE_1_DNI,
                    pin_hash=hash_pin(EMPLOYEE_1_PIN),
                    rol=UserRole.EMPLEADO,
                    active=True,
                    negocio_id=negocio.id,
                ),
                User(
                    nombre="Empleado Demo 2",
                    dni=EMPLOYEE_2_DNI,
                    pin_hash=hash_pin(EMPLOYEE_2_PIN),
                    rol=UserRole.EMPLEADO,
                    active=True,
                    negocio_id=negocio.id,
                ),
            ]
        )
        await session.commit()
        print(f"Created demo: negocio_id={negocio.id}, slug={DEMO_SLUG}")
        print_credentials()


def print_credentials() -> None:
    print("Admin: gestion@test.local / Test1234!")
    print("Empleado 1: DNI 00000001T / PIN 1111")
    print("Empleado 2: DNI 00000002R / PIN 2222")


if __name__ == "__main__":
    asyncio.run(seed_demo())
