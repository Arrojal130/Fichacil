import asyncio
import os
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

# The app imports its settings at module import time, so test modules need a
# valid runtime secret before importing any app code.
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import HTTPException
from app.models.fichaje import TipoFichaje
from app.models.user import UserRole
from app.models.correccion import MotivoCorreccion
from app.routers.correcciones import get_correcciones_pendientes_empleado
from app.routers.fichajes import crear_fichaje, get_historial_empleado, get_ultimo_fichaje


class FakeResult:
    def __init__(self, *, one=None, many=None):
        self._one = one
        self._many = many or []

    def scalar_one_or_none(self):
        return self._one

    def scalar_one(self):
        return self._one

    def scalars(self):
        return self

    def all(self):
        return self._many


class FakeSession:
    def __init__(self, results):
        self._results = list(results)
        self.added = []

    async def execute(self, _query):
        if not self._results:
            raise AssertionError("Unexpected DB query in test")
        return self._results.pop(0)

    def add(self, obj):
        self.added.append(obj)

    async def flush(self):
        return None

    async def refresh(self, _obj):
        return None


class DummyRequest:
    def __init__(self, *, client_host="127.0.0.1"):
        self.client = SimpleNamespace(host=client_host)
        self.headers = {"user-agent": "pytest"}

    async def is_disconnected(self):
        return True


class EmployeeTokenSessionTests(unittest.TestCase):
    def test_employee_can_get_last_fichaje_with_session_cookie(self):
        current_user = SimpleNamespace(id=7, nombre="Empleado", rol=UserRole.EMPLEADO, negocio_id=42)
        fichaje = SimpleNamespace(
            id=1,
            tipo=TipoFichaje.ENTRADA,
            timestamp=datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc),
            lat=None,
            lon=None,
            distancia_metros=None,
            empleado_id=7,
            negocio_id=42,
            created_at=datetime(2026, 4, 26, 10, 0, tzinfo=timezone.utc),
        )
        db = FakeSession([FakeResult(one=fichaje)])

        response = asyncio.run(
            get_ultimo_fichaje(
                data=SimpleNamespace(negocio_id=42),
                request=DummyRequest(),
                current_user=current_user,
                db=db,
            )
        )

        self.assertIsNotNone(response)
        self.assertEqual(response.id, 1)
        self.assertEqual(response.empleado_id, 7)

    def test_employee_can_load_history_with_session_cookie(self):
        current_user = SimpleNamespace(id=7, nombre="Empleado", rol=UserRole.EMPLEADO, negocio_id=42)
        fichaje = SimpleNamespace(
            id=1,
            tipo=TipoFichaje.ENTRADA,
            timestamp=datetime(2026, 4, 25, 8, 0, tzinfo=timezone.utc),
            lat=None,
            lon=None,
            distancia_metros=None,
            empleado_id=7,
            negocio_id=42,
            created_at=datetime(2026, 4, 25, 8, 0, tzinfo=timezone.utc),
        )
        db = FakeSession([FakeResult(many=[fichaje])])

        response = asyncio.run(
            get_historial_empleado(
                data=SimpleNamespace(negocio_id=42, dias=7),
                request=DummyRequest(),
                current_user=current_user,
                db=db,
            )
        )

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].id, 1)

    def test_employee_can_clock_in_without_sending_pin_after_login(self):
        current_user = SimpleNamespace(id=7, nombre="Empleado", rol=UserRole.EMPLEADO, negocio_id=42)
        negocio = SimpleNamespace(id=42, lat=None, lon=None)
        db = FakeSession([FakeResult(one=negocio), FakeResult(many=[])])

        response = asyncio.run(
            crear_fichaje(
                data=SimpleNamespace(
                    negocio_id=42,
                    tipo=TipoFichaje.ENTRADA,
                    lat=None,
                    lon=None,
                ),
                request=DummyRequest(),
                current_user=current_user,
                db=db,
            )
        )

        self.assertEqual(response.tipo, TipoFichaje.ENTRADA)
        self.assertEqual(len(db.added), 1)
        self.assertEqual(db.added[0].empleado_id, 7)

    def test_employee_pending_corrections_use_session_auth_only(self):
        current_user = SimpleNamespace(id=7, nombre="Empleado", rol=UserRole.EMPLEADO, negocio_id=42)
        creator = SimpleNamespace(id=99, nombre="Admin")
        correccion = SimpleNamespace(
            id=3,
            fichaje_id=11,
            timestamp_original=datetime(2026, 4, 25, 8, 0, tzinfo=timezone.utc),
            timestamp_corregido=datetime(2026, 4, 25, 8, 15, tzinfo=timezone.utc),
            motivo=MotivoCorreccion.ERROR,
            detalle="Ajuste",
            estado="PENDIENTE",
            creador_id=99,
            created_at=datetime(2026, 4, 25, 9, 0, tzinfo=timezone.utc),
        )
        db = FakeSession([
            FakeResult(many=[11]),
            FakeResult(many=[correccion]),
            FakeResult(one=creator),
        ])

        response = asyncio.run(
            get_correcciones_pendientes_empleado(
                data=SimpleNamespace(negocio_id=42),
                request=DummyRequest(),
                current_user=current_user,
                db=db,
            )
        )

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].id, 3)
        self.assertEqual(response[0].empleado_nombre, "Empleado")

    def test_employee_endpoints_reject_pin_only_access_without_session(self):
        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                get_ultimo_fichaje(
                    data=SimpleNamespace(negocio_id=42, pin="1234"),
                    request=DummyRequest(),
                    current_user=None,
                    db=FakeSession([]),
                )
            )

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("No autenticado", ctx.exception.detail)


if __name__ == "__main__":
    unittest.main()
