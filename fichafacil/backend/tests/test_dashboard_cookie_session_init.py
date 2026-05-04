import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2]


class DashboardCookieSessionInitTests(unittest.TestCase):
    def test_dashboard_initial_cookie_probe_does_not_show_error_to_unauthenticated_users(self):
        dashboard_html = (APP_ROOT / "frontend" / "dashboard.html").read_text()

        self.assertIn("async function loadDashboard({ showError = true } = {})", dashboard_html)
        self.assertIn("if (showError)", dashboard_html)
        self.assertIn("loadDashboard({ showError: false });", dashboard_html)
        self.assertNotIn("if (auth.isLoggedIn()) {\n            loadDashboard();\n        }", dashboard_html)


if __name__ == "__main__":
    unittest.main()
