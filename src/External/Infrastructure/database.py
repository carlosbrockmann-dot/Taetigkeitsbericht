from __future__ import annotations

from sqlalchemy import inspect, text
from sqlmodel import SQLModel, create_engine


def create_sqlite_engine(database_url: str = "sqlite:///taetigkeitsbericht.db"):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def _ensure_feiertag_hinweis_column(engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "feiertag" not in inspector.get_table_names():
        return
    spalten = {c["name"] for c in inspector.get_columns("feiertag")}
    if "hinweis" in spalten:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE feiertag ADD COLUMN hinweis VARCHAR(80)"))


def init_db(engine) -> None:
    import External.Infrastructure.sqlmodel_tables  # noqa: F401 - Tabellen bei SQLModel registrieren

    SQLModel.metadata.create_all(engine)
    _ensure_feiertag_hinweis_column(engine)
