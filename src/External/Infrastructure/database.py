from __future__ import annotations

from sqlmodel import SQLModel, create_engine


def create_sqlite_engine(database_url: str = "sqlite:///taetigkeitsbericht.db"):
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, connect_args=connect_args)


def init_db(engine) -> None:
    import External.Infrastructure.sqlmodel_tables  # noqa: F401 - Tabellen bei SQLModel registrieren

    SQLModel.metadata.create_all(engine)
