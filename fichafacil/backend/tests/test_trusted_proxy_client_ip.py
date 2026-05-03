import importlib
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("SECRET_KEY", "0123456789abcdef0123456789abcdef")

from app.config import Settings

security = importlib.import_module("app.utils.security")


class TrustedProxyClientIpTests(unittest.TestCase):
    def tearDown(self):
        security.settings = security.get_settings()

    def _request(self, *, client_host, headers=None):
        return SimpleNamespace(
            headers=headers or {},
            client=SimpleNamespace(host=client_host) if client_host is not None else None,
        )

    def _use_settings(self, trusted_proxy_ips=""):
        security.settings = Settings(
            secret_key="0123456789abcdef0123456789abcdef",
            trusted_proxy_ips=trusted_proxy_ips,
            _env_file=None,
        )

    def test_ignores_forwarded_headers_from_untrusted_direct_clients(self):
        self._use_settings(trusted_proxy_ips="10.0.0.10")
        request = self._request(
            client_host="198.51.100.23",
            headers={"X-Forwarded-For": "203.0.113.99"},
        )

        self.assertEqual(security.get_client_ip(request), "198.51.100.23")

    def test_uses_forwarded_for_when_direct_client_is_trusted_proxy(self):
        self._use_settings(trusted_proxy_ips="10.0.0.10")
        request = self._request(
            client_host="10.0.0.10",
            headers={"X-Forwarded-For": "203.0.113.99"},
        )

        self.assertEqual(security.get_client_ip(request), "203.0.113.99")

    def test_skips_trusted_proxy_hops_in_forwarded_for_chain(self):
        self._use_settings(trusted_proxy_ips="10.0.0.0/24")
        request = self._request(
            client_host="10.0.0.20",
            headers={"X-Forwarded-For": "203.0.113.99, 10.0.0.10"},
        )

        self.assertEqual(security.get_client_ip(request), "203.0.113.99")

    def test_uses_x_real_ip_only_from_trusted_proxy(self):
        self._use_settings(trusted_proxy_ips="10.0.0.10")

        untrusted_request = self._request(
            client_host="198.51.100.23",
            headers={"X-Real-IP": "203.0.113.99"},
        )
        trusted_request = self._request(
            client_host="10.0.0.10",
            headers={"X-Real-IP": "203.0.113.99"},
        )

        self.assertEqual(security.get_client_ip(untrusted_request), "198.51.100.23")
        self.assertEqual(security.get_client_ip(trusted_request), "203.0.113.99")


if __name__ == "__main__":
    unittest.main()
