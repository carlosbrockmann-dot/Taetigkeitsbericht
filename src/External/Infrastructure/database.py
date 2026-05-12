from __future__ import annotations

from sqlalchemy import text
from sqlmodel import SQLModel, create_engine


def create_sqlite_engine(database_url: str = "sqlite:///taetigkeitsbericht.db"):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def _migrate_krankmeldung_spalten_entfernen(engine) -> None:
    """Entfernt die Spalten krankmeldung und krankmeldungstagsname (Schema vor Mai 2026)."""
    if not str(engine.url).startswith("sqlite"):
        return
    with engine.begin() as conn:
        exists = conn.execute(
            text(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='krankmeldung' LIMIT 1"
            )
        ).fetchone()
        if exists is None:
            return
        cols = [
            row[1]
            for row in conn.execute(text("PRAGMA table_info(krankmeldung)")).fetchall()
        ]
        if "krankmeldung" in cols:
            conn.execute(text("ALTER TABLE krankmeldung DROP COLUMN krankmeldung"))
        if "krankmeldungstagsname" in cols:
            conn.execute(text("ALTER TABLE krankmeldung DROP COLUMN krankmeldungstagsname"))


def init_db(engine) -> None:
    import External.Infrastructure.sqlmodel_tables  # noqa: F401 - Tabellen bei SQLModel registrieren

    SQLModel.metadata.create_all(engine)
    _migrate_krankmeldung_spalten_entfernen(engine)
