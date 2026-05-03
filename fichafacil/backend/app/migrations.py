"""Database migration runner for FichaFácil.

This lightweight runner keeps the project dependency-free while still
introducing versioned, idempotent schema migrations.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
SCHEMA_MIGRATIONS_TABLE = "schema_migrations"


@dataclass(frozen=True)
class Migration:
    version: str
    path: Path
    sql: str


def _load_migrations() -> list[Migration]:
    migrations: list[Migration] = []
    for path in sorted(MIGRATIONS_DIR.glob("*.sql")):
        sql = path.read_text(encoding="utf-8").strip()
        if not sql:
            continue
        migrations.append(Migration(version=path.stem, path=path, sql=sql))
    return migrations


async def _ensure_migrations_table(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            f"""
            CREATE TABLE IF NOT EXISTS {SCHEMA_MIGRATIONS_TABLE} (
                version VARCHAR(64) PRIMARY KEY,
                applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
    )


async def _applied_versions(conn: AsyncConnection) -> set[str]:
    result = await conn.execute(text(f"SELECT version FROM {SCHEMA_MIGRATIONS_TABLE}"))
    return {row[0] for row in result.fetchall()}


async def apply_migrations(conn: AsyncConnection) -> list[str]:
    """Apply any pending SQL migrations in order.

    Returns the list of versions applied during this run.
    """
    await _ensure_migrations_table(conn)
    applied = await _applied_versions(conn)
    pending = [migration for migration in _load_migrations() if migration.version not in applied]

    applied_now: list[str] = []
    for migration in pending:
        for statement in (part.strip() for part in migration.sql.split(";") if part.strip()):
            await conn.execute(text(statement))
        await conn.execute(
            text(f"INSERT INTO {SCHEMA_MIGRATIONS_TABLE} (version) VALUES (:version)"),
            {"version": migration.version},
        )
        applied_now.append(migration.version)

    return applied_now
