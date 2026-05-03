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
from app.models.correccion import EstadoCorreccion, MotivoCorreccion
from app.models.user import UserRole
from app.routers.correcciones import aprobar_correccion
from app.schemas.correccion import CorreccionApprove
from app.utils.security import hash_password


class FakeResult:
    def __init__(self, *, one=None, one_or_none=None):
        self._one = one
        self._one_or_none = one_or_none

    def scalar_one_or_none(self):
        return self._one_or_none

    def scalar_one(self):
        return self._one


class FakeSession:
    def __init__(self, results):
        self._results = list(results)

    async def execute(self, _query):
        if not self._results:
            raise AssertionError("Unexpected DB query in test")
        return self._results.pop(0)

    async def flush(self):
        return None

    async def refresh(self, _obj):
        return None


class AdminCorreccionReauthTests(unittest.TestCase):
    def _make_correccion(self):
        return SimpleNamespace(
            id=1,
            fichaje_id=10,
            timestamp_original=datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc),
            timestamp_corregido=datetime(2026, 1, 1, 8, 15, tzinfo=timezone.utc),
            motivo=MotivoCorreccion.ERROR,
            detalle="Ajuste puntual",
            estado=EstadoCorreccion.PENDIENTE,
            creador_id=99,
            aprobador_id=None,
            resolved_at=None,
            created_at=datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc),
        )

    def test_admin_approval_requires_password_and_preserves_original_fichaje(self):
        correccion = self._make_correccion()
        fichaje = SimpleNamespace(id=10, negocio_id=7, timestamp=correccion.timestamp_original)
        creator = SimpleNamespace(id=99, nombre="Empleada")
        current_user = SimpleNamespace(
            id=5,
            nombre="Admin",
            rol=UserRole.ADMIN,
            negocio_id=7,
            password_hash=hash_password("Secret123"),
        )
        db = FakeSession([
            FakeResult(one_or_none=correccion),
            FakeResult(one=fichaje),
            FakeResult(one=creator),
        ])

        response = asyncio.run(
            aprobar_correccion(
                correccion_id=1,
                data=CorreccionApprove(admin_password="Secret123", aprobar=True),
                current_user=current_user,
                db=db,
            )
        )

        self.assertEqual(correccion.estado, EstadoCorreccion.APROBADO)
        self.assertEqual(correccion.aprobador_id, 5)
        self.assertIsNotNone(correccion.resolved_at)
        self.assertEqual(fichaje.timestamp, correccion.timestamp_original)
        self.assertEqual(response.estado, EstadoCorreccion.APROBADO)
        self.assertEqual(response.aprobador_nombre, "Admin")

    def test_admin_approval_rejects_wrong_password(self):
        correccion = self._make_correccion()
        fichaje = SimpleNamespace(id=10, negocio_id=7, timestamp=correccion.timestamp_original)
        current_user = SimpleNamespace(
            id=5,
            nombre="Admin",
            rol=UserRole.ADMIN,
            negocio_id=7,
            password_hash=hash_password("Secret123"),
        )
        db = FakeSession([
            FakeResult(one_or_none=correccion),
            FakeResult(one=fichaje),
        ])

        with self.assertRaises(HTTPException) as ctx:
            asyncio.run(
                aprobar_correccion(
                    correccion_id=1,
                    data=CorreccionApprove(admin_password="BadPass1", aprobar=False),
                    current_user=current_user,
                    db=db,
                )
            )

        self.assertEqual(ctx.exception.status_code, 401)
        self.assertIn("Contraseña de administrador", ctx.exception.detail)
        self.assertEqual(correccion.estado, EstadoCorreccion.PENDIENTE)
        self.assertIsNone(correccion.aprobador_id)
        self.assertIsNone(correccion.resolved_at)


if __name__ == "__main__":
    unittest.main()
