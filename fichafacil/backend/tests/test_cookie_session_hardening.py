import os
import sys
import unittest
from pathlib import Path

os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

BACKEND_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = BACKEND_ROOT.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.config import Settings


class CookieSessionHardeningTests(unittest.TestCase):
    def test_frontend_api_does_not_store_or_read_sensitive_tokens_in_local_storage(self):
        api_js = (APP_ROOT / "frontend" / "js" / "api.js").read_text()

        forbidden_snippets = [
            "localStorage.setItem('token'",
            'localStorage.setItem("token"',
            "localStorage.getItem('token'",
            'localStorage.getItem("token"',
            "employeeSessionToken",
            "Authorization'] = `Bearer",
            "Authorization\"] = `Bearer",
        ]

        for snippet in forbidden_snippets:
            with self.subTest(snippet=snippet):
                self.assertNotIn(snippet, api_js)

    def test_register_and_login_routes_issue_httponly_cookie_sessions(self):
        auth_py = (BACKEND_ROOT / "app" / "routers" / "auth.py").read_text()

        self.assertIn("issue_auth_cookie(response, token)", auth_py)
        self.assertIn("httponly=True", auth_py)
        self.assertNotIn("secure=True,  # HTTPS only", auth_py)

    def test_cookie_secure_defaults_to_production_safe_and_debug_friendly(self):
        prod_settings = Settings(
            debug=False,
            secret_key="0123456789abcdef0123456789abcdef",
            _env_file=None,
        )
        debug_settings = Settings(debug=True, _env_file=None)

        self.assertTrue(prod_settings.cookie_secure)
        self.assertFalse(debug_settings.cookie_secure)


if __name__ == "__main__":
    unittest.main()
