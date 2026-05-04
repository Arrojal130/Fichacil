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
from app.main import authorize_sse_access, sse_endpoint


class DummyRequest:
    async def is_disconnected(self):
        return True


class SseAuthorizationTests(unittest.TestCase):
    def test_authorize_sse_access_rejects_cross_tenant_subscription(self):
        current_user = SimpleNamespace(negocio_id=7)

        with self.assertRaises(HTTPException) as ctx:
            authorize_sse_access(current_user=current_user, negocio_id=8)

        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn("No autorizado", ctx.exception.detail)

    def test_sse_endpoint_allows_same_business_subscription(self):
        current_user = SimpleNamespace(negocio_id=7)

        response = asyncio.run(
            sse_endpoint(
                request=DummyRequest(),
                negocio_id=7,
                current_user=current_user,
            )
        )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
