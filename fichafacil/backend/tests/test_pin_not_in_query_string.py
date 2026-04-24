import ast
from pathlib import Path
import unittest


class PinNotInQueryStringTests(unittest.TestCase):
    ROUTES = {
        "get_ultimo_fichaje",
        "get_historial_empleado",
        "get_correcciones_pendientes_empleado",
    }

    def test_employee_pin_endpoints_do_not_accept_pin_as_function_parameter(self):
        backend = Path(__file__).resolve().parents[1]
        files = [
            backend / "app" / "routers" / "fichajes.py",
            backend / "app" / "routers" / "correcciones.py",
        ]
        offenders = []
        for file_path in files:
            tree = ast.parse(file_path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.AsyncFunctionDef) and node.name in self.ROUTES:
                    arg_names = [arg.arg for arg in node.args.args]
                    if "pin" in arg_names:
                        offenders.append(f"{file_path.name}:{node.name}")

        self.assertEqual(offenders, [], "PINs must be accepted in request bodies, not query parameters")


if __name__ == "__main__":
    unittest.main()
