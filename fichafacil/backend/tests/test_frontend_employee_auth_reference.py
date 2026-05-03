import unittest
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[2]


class EmployeeFrontendAuthReferenceTests(unittest.TestCase):
    def test_employee_page_defines_auth_api_alias_before_using_it(self):
        empleado_html = (APP_ROOT / "frontend" / "empleado.html").read_text()

        first_auth_use = empleado_html.index("auth.loginEmpleado")
        auth_alias = "const auth = window.FichaFacilAPI.auth;"

        self.assertIn(auth_alias, empleado_html)
        self.assertLess(empleado_html.index(auth_alias), first_auth_use)


if __name__ == "__main__":
    unittest.main()
