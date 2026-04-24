import ast
from pathlib import Path
import unittest


class CorreccionesImmutabilityTests(unittest.TestCase):
    def test_correction_approval_does_not_overwrite_original_fichaje_timestamp(self):
        """Approved corrections must preserve the original append-only fichaje row."""
        router_path = Path(__file__).resolve().parents[1] / "app" / "routers" / "correcciones.py"
        tree = ast.parse(router_path.read_text())

        destructive_assignments = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                targets = []
                if isinstance(node, ast.Assign):
                    targets = list(node.targets)
                else:
                    targets = [node.target]

                for target in targets:
                    if (
                        isinstance(target, ast.Attribute)
                        and target.attr == "timestamp"
                        and isinstance(target.value, ast.Name)
                        and target.value.id == "fichaje"
                    ):
                        destructive_assignments.append(node.lineno)

        self.assertEqual(
            destructive_assignments,
            [],
            "Corrections must not assign fichaje.timestamp; keep original records immutable "
            "and resolve corrected/effective timestamps at read/report time.",
        )


if __name__ == "__main__":
    unittest.main()
