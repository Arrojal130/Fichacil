import asyncio
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

# The app imports settings at module import time, so tests need explicit
# production-like env values instead of inheriting the local LAN-demo .env.
os.environ["DEBUG"] = "false"
os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from fastapi import HTTPException
from app.config import Settings
from app.main import authorize_sse_access
from app.models.user import UserRole
from app.routers.negocios import get_my_negocio, list_empleados


class FakeResult:
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
    def __init__(self, results):
        self._results = list(results)

    async def execute(self, _query):
        if not self._results:
            raise AssertionError("Unexpected DB query in test")
        return self._results.pop(0)


class MultiTenantAndDeploymentSmokeTests(unittest.TestCase):
    def test_admin_only_sees_their_own_business(self):
        current_user = SimpleNamespace(id=1, negocio_id=10, rol=UserRole.ADMIN)
        negocio = SimpleNamespace(
            id=10,
            nombre="Negocio A",
            direccion="Calle Mayor 1",
            nif="A12345678",
            lat=None,
            lon=None,
            slug="negocio-a",
            created_at="2026-04-26T10:00:00Z",
        )
        db = FakeSession([FakeResult(one=negocio)])

        response = asyncio.run(get_my_negocio(current_user=current_user, db=db))

        self.assertEqual(response.id, 10)
        self.assertEqual(response.nombre, "Negocio A")
        self.assertEqual(response.slug, "negocio-a")

    def test_admin_employee_list_is_scoped_to_their_business(self):
        current_user = SimpleNamespace(id=1, negocio_id=10, rol=UserRole.ADMIN)
        empleado = SimpleNamespace(
            id=2,
            nombre="Ana",
            dni="11111111A",
            pin_hash="hash",
            rol=UserRole.EMPLEADO,
            negocio_id=10,
            active=True,
        )
        db = FakeSession([FakeResult(many=[empleado])])

        response = asyncio.run(list_empleados(current_user=current_user, db=db))

        self.assertEqual(len(response), 1)
        self.assertEqual(response[0].id, 2)
        self.assertEqual(response[0].nombre, "Ana")
        self.assertFalse(hasattr(response[0], "negocio_id"))

    def test_sse_rejects_cross_business_access(self):
        current_user = SimpleNamespace(id=7, negocio_id=10, rol=UserRole.EMPLEADO)

        with self.assertRaises(HTTPException) as ctx:
            authorize_sse_access(current_user=current_user, negocio_id=99)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("No autorizado", ctx.exception.detail)

    def test_production_app_does_not_expose_interactive_docs(self):
        for module_name in ["app.main", "app.config"]:
            sys.modules.pop(module_name, None)
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = "0123456789abcdef0123456789abcdef"

        config_module = __import__("app.config", fromlist=["Settings", "get_settings"])
        config_module.get_settings.cache_clear()
        main_module = __import__("app.main", fromlist=["app"])
        settings = config_module.Settings(
            secret_key="0123456789abcdef0123456789abcdef",
            _env_file=None,
        )

        self.assertFalse(settings.debug)
        self.assertIsNone(main_module.app.docs_url)
        self.assertIsNone(main_module.app.redoc_url)
        self.assertIsNone(main_module.app.openapi_url)


if __name__ == "__main__":
    unittest.main()
