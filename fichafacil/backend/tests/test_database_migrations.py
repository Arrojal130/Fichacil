import asyncio
import importlib
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


class DatabaseMigrationTests(unittest.TestCase):
    def setUp(self):
        for module_name in ["app.config", "app.database", "app.migrations"]:
            sys.modules.pop(module_name, None)

    def tearDown(self):
        for key in ["SECRET_KEY", "DATABASE_URL", "DEBUG"]:
            os.environ.pop(key, None)
        for module_name in ["app.config", "app.database", "app.migrations"]:
            sys.modules.pop(module_name, None)

    def test_init_db_applies_versioned_schema_migrations(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "fichafacil.db"
            os.environ["SECRET_KEY"] = "0123456789abcdef0123456789abcdef"
            os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
            os.environ["DEBUG"] = "false"

            database = importlib.import_module("app.database")
            asyncio.run(database.init_db())
            asyncio.run(database.init_db())

            with sqlite3.connect(db_path) as conn:
                tables = {
                    row[0]
                    for row in conn.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    ).fetchall()
                }
                applied_versions = [
                    row[0]
                    for row in conn.execute(
                        "SELECT version FROM schema_migrations ORDER BY version"
                    ).fetchall()
                ]

            self.assertTrue({"negocios", "users", "fichajes", "correcciones"}.issubset(tables))
            self.assertEqual(applied_versions, ["001_initial_schema"])


if __name__ == "__main__":
    unittest.main()
