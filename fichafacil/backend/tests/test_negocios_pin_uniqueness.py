import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

# The app imports its settings at module import time, so test modules need a
# valid runtime secret before importing any app code.
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import HTTPException
from app.routers.negocios import (
    ensure_unique_employee_pin,
    update_empleado,
    validate_employee_pin,
)
from app.utils.security import hash_pin


class DummyEmployee:
    def __init__(self, employee_id: int, pin: str | None):
        self.id = employee_id
        self.pin_hash = hash_pin(pin) if pin is not None else None


class FakeScalarResult:
    def __init__(self, *, one=None, many=None):
        self._one = one
        self._many = many or []

    def scalar_one_or_none(self):
        return self._one

    def scalars(self):
        return self

    def all(self):
        return self._many


class FakeSession:
    def __init__(self, empleado, existing_employees):
        self._results = [
            FakeScalarResult(one=empleado),
            FakeScalarResult(many=existing_employees),
        ]

    async def execute(self, _query):
        return self._results.pop(0)

    async def flush(self):
        return None

    async def refresh(self, _obj):
        return None


class EnsureUniqueEmployeePinTests(unittest.TestCase):
    def test_rejects_duplicate_pin_from_other_employee(self):
        employees = [
            DummyEmployee(1, "1234"),
            DummyEmployee(2, "5678"),
        ]

        with self.assertRaises(HTTPException) as ctx:
            ensure_unique_employee_pin(employees, "1234", exclude_user_id=2)

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("PIN ya está en uso", ctx.exception.detail)

    def test_allows_reusing_same_pin_for_same_employee(self):
        employees = [
            DummyEmployee(1, "1234"),
            DummyEmployee(2, "5678"),
        ]

        ensure_unique_employee_pin(employees, "1234", exclude_user_id=1)

    def test_rejects_pin_with_invalid_format(self):
        with self.assertRaises(HTTPException) as ctx:
            validate_employee_pin("12ab")

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("4 dígitos", ctx.exception.detail)


class UpdateEmpleadoTests(unittest.TestCase):
    def test_update_empleado_rejects_duplicate_pin_from_other_active_employee(self):
        current_user = SimpleNamespace(negocio_id=10)
        empleado = SimpleNamespace(
            id=1,
            nombre="Ana",
            dni="11111111A",
            pin_hash=hash_pin("1234"),
            active=True,
        )
        other_employee = SimpleNamespace(id=2, pin_hash=hash_pin("5678"), active=True)
        db = FakeSession(empleado=empleado, existing_employees=[empleado, other_employee])

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                update_empleado(
                    empleado_id=1,
                    pin="5678",
                    current_user=current_user,
                    db=db,
                )
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("PIN ya está en uso", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
