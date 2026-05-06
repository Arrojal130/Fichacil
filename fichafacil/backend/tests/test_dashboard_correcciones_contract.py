import ast
from pathlib import Path
import unittest


class DashboardCorreccionesContractTests(unittest.TestCase):
    def test_dashboard_fichaje_exposes_latest_fichaje_id_for_corrections(self):
        """The dashboard correction button needs a concrete fichaje id, never null."""
        schema_path = Path(__file__).resolve().parents[1] / "app" / "schemas" / "fichaje.py"
        tree = ast.parse(schema_path.read_text())

        dashboard = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef) and node.name == "DashboardFichaje"
        )
        annotated_fields = {
            stmt.target.id
            for stmt in dashboard.body
            if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name)
        }

        self.assertIn("ultimo_fichaje_id", annotated_fields)

    def test_get_fichajes_hoy_populates_latest_fichaje_id(self):
        router_path = Path(__file__).resolve().parents[1] / "app" / "routers" / "fichajes.py"
        source = router_path.read_text()

        self.assertIn("ultimo_fichaje_id=ultimo_fichaje_id", source)
        self.assertIn("ultimo_fichaje_id =", source)


if __name__ == "__main__":
    unittest.main()
