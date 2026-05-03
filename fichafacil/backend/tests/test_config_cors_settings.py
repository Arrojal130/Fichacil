import importlib
import os
import re
import sys
import unittest
import warnings
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from starlette.datastructures import Headers
from starlette.middleware.cors import CORSMiddleware

from app.config import Settings


class SettingsCorsTests(unittest.TestCase):
    def setUp(self):
        for module_name in ["app.main", "app.config"]:
            sys.modules.pop(module_name, None)

    def tearDown(self):
        for key in ["DEBUG", "ALLOWED_ORIGINS", "CORS_ORIGINS", "SECRET_KEY"]:
            os.environ.pop(key, None)
        for module_name in ["app.main", "app.config"]:
            sys.modules.pop(module_name, None)

    def test_debug_is_disabled_by_default_for_safer_deployments(self):
        settings = Settings(secret_key="0123456789abcdef0123456789abcdef", _env_file=None)

        self.assertFalse(settings.debug)

    def test_default_sqlite_database_lives_inside_backend_data_directory(self):
        settings = Settings(secret_key="0123456789abcdef0123456789abcdef", _env_file=None)

        self.assertEqual(settings.database_url, "sqlite+aiosqlite:///./data/fichafacil.db")

    def test_importing_main_does_not_emit_pydantic_class_based_config_warning(self):
        for module_name in ["app.main", "app.config"]:
            sys.modules.pop(module_name, None)
        os.environ["SECRET_KEY"] = "0123456789abcdef0123456789abcdef"

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            importlib.import_module("app.main")

        pydantic_warnings = [
            warning for warning in caught
            if "class-based `config` is deprecated" in str(warning.message)
        ]

        self.assertEqual(pydantic_warnings, [])

    def test_default_allowed_origins_do_not_include_hardcoded_private_lan_hosts(self):
        settings = Settings(secret_key="0123456789abcdef0123456789abcdef")

        self.assertNotIn("http://192.168.1.42:3000", settings.effective_allowed_origins)

    def test_uses_cors_origins_alias_when_present(self):
        settings = Settings(
            secret_key="0123456789abcdef0123456789abcdef",
            allowed_origins="http://legacy.example.com",
            cors_origins=" https://app.example.com , https://admin.example.com ",
        )

        self.assertEqual(
            settings.effective_allowed_origins,
            ["https://app.example.com", "https://admin.example.com"],
        )

    def test_explicit_empty_cors_origins_disables_fallback_to_default_origins(self):
        settings = Settings(
            secret_key="0123456789abcdef0123456789abcdef",
            allowed_origins="http://legacy.example.com",
            cors_origins="",
        )

        self.assertEqual(settings.effective_allowed_origins, [])

    def test_builds_debug_lan_regex_only_in_debug_mode(self):
        settings = Settings(debug=True, _env_file=None)

        self.assertEqual(
            settings.cors_origin_regex,
            r"http://(?:192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(?:1[6-9]|2\d|3[0-1])\.\d+\.\d+):3000",
        )

    def test_debug_lan_regex_matches_10_range_origins(self):
        settings = Settings(debug=True, _env_file=None)

        self.assertIsNotNone(re.fullmatch(settings.cors_origin_regex, "http://10.20.30.40:3000"))

    def test_uses_local_dev_secret_key_fallback_only_in_debug_mode(self):
        settings = Settings(debug=True, _env_file=None)

        self.assertEqual(settings.secret_key, Settings.LOCAL_DEV_SECRET_KEY)

    def test_requires_secret_key_when_debug_is_disabled(self):
        with self.assertRaisesRegex(ValueError, "SECRET_KEY es obligatorio"):
            Settings(_env_file=None)

    def test_rejects_short_or_placeholder_secret_keys_in_production(self):
        with self.assertRaisesRegex(ValueError, "SECRET_KEY inseguro"):
            Settings(secret_key="your-secret-key-change-in-production", _env_file=None)

        with self.assertRaisesRegex(ValueError, "SECRET_KEY inseguro"):
            Settings(secret_key="short-secret", _env_file=None)

    def test_accepts_secure_secret_key_in_production(self):
        settings = Settings(secret_key="0123456789abcdef0123456789abcdef")

        self.assertEqual(settings.secret_key, "0123456789abcdef0123456789abcdef")

    def test_trusted_proxy_ips_defaults_to_empty_for_safe_proxy_header_handling(self):
        settings = Settings(secret_key="0123456789abcdef0123456789abcdef", _env_file=None)

        self.assertEqual(settings.trusted_proxy_ips, "")

    def test_trusted_proxy_ips_can_be_configured_from_environment(self):
        settings = Settings(
            secret_key="0123456789abcdef0123456789abcdef",
            trusted_proxy_ips="10.0.0.0/24, 127.0.0.1",
            _env_file=None,
        )

        self.assertEqual(settings.trusted_proxy_ips, "10.0.0.0/24, 127.0.0.1")

    def test_disables_debug_lan_regex_in_production_mode(self):
        settings = Settings(debug=False, secret_key="0123456789abcdef0123456789abcdef")

        self.assertIsNone(settings.cors_origin_regex)

    def test_main_disables_interactive_api_docs_outside_debug_mode(self):
        os.environ["DEBUG"] = "false"
        os.environ["SECRET_KEY"] = "0123456789abcdef0123456789abcdef"
        config_module = importlib.import_module("app.config")
        config_module.get_settings.cache_clear()
        main_module = importlib.import_module("app.main")

        self.assertIsNone(main_module.app.docs_url)
        self.assertIsNone(main_module.app.redoc_url)
        self.assertIsNone(main_module.app.openapi_url)

    def test_main_wires_normalized_origins_and_regex_into_cors_middleware(self):
        os.environ["DEBUG"] = "true"
        os.environ["ALLOWED_ORIGINS"] = "http://legacy.example.com"
        os.environ["CORS_ORIGINS"] = "https://app.example.com, https://admin.example.com"

        config_module = importlib.import_module("app.config")
        config_module.get_settings.cache_clear()
        main_module = importlib.import_module("app.main")

        cors_middleware = next(
            middleware
            for middleware in main_module.app.user_middleware
            if middleware.cls.__name__ == "CORSMiddleware"
        )

        self.assertEqual(
            cors_middleware.kwargs["allow_origins"],
            ["https://app.example.com", "https://admin.example.com"],
        )
        self.assertEqual(
            cors_middleware.kwargs["allow_origin_regex"],
            Settings.DEBUG_LAN_ORIGIN_REGEX,
        )

    def test_preflight_allows_private_10_range_origin_in_debug_mode(self):
        middleware = CORSMiddleware(
            app=lambda scope, receive, send: None,
            allow_origins=["https://app.example.com"],
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
            allow_credentials=True,
            allow_origin_regex=Settings.DEBUG_LAN_ORIGIN_REGEX,
        )

        response = middleware.preflight_response(
            Headers(
                {
                    "origin": "http://10.20.30.40:3000",
                    "access-control-request-method": "GET",
                }
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers.get("access-control-allow-origin"),
            "http://10.20.30.40:3000",
        )

    def test_preflight_rejects_private_10_range_origin_in_production_mode(self):
        settings = Settings(
            debug=False,
            secret_key="0123456789abcdef0123456789abcdef",
            cors_origins="",
        )
        middleware = CORSMiddleware(
            app=lambda scope, receive, send: None,
            allow_origins=settings.effective_allowed_origins,
            allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            allow_headers=["Content-Type", "Authorization"],
            allow_credentials=True,
            allow_origin_regex=settings.cors_origin_regex,
        )

        response = middleware.preflight_response(
            Headers(
                {
                    "origin": "http://10.20.30.40:3000",
                    "access-control-request-method": "GET",
                }
            )
        )

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(response.headers.get("access-control-allow-origin"))


if __name__ == "__main__":
    unittest.main()
