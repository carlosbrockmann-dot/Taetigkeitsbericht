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


def _rename_pause_columns(engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    tabellen = set(inspector.get_table_names())
    umbenennungen = (
        ("zeiteintrag", "unterbrechung_beginn", "pause_beginn"),
        ("zeiteintrag", "unterbrechung_ende", "pause_ende"),
        ("stundenplan", "unterbrechung_beginn", "pause_beginn"),
        ("stundenplan", "unterbrechung_ende", "pause_ende"),
    )
    with engine.begin() as conn:
        for tabellenname, alt, neu in umbenennungen:
            if tabellenname not in tabellen:
                continue
            spalten = {c["name"] for c in inspector.get_columns(tabellenname)}
            if neu in spalten or alt not in spalten:
                continue
            conn.execute(
                text(f"ALTER TABLE {tabellenname} RENAME COLUMN {alt} TO {neu}")
            )


def _drop_urlaubsantrag_urlaubstagsname_column(engine) -> None:
    """SQLite 3.35+: entfernt die nicht mehr genutzte Spalte urlaubstagsname."""
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    if "urlaubsantrag" not in inspector.get_table_names():
        return
    spalten = {c["name"] for c in inspector.get_columns("urlaubsantrag")}
    if "urlaubstagsname" not in spalten:
        return
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE urlaubsantrag DROP COLUMN urlaubstagsname"))


def _ensure_pause2_columns(engine) -> None:
    if not str(engine.url).startswith("sqlite"):
        return
    inspector = inspect(engine)
    additions = (
        ("zeiteintrag", "pause2_beginn", "TIME"),
        ("zeiteintrag", "pause2_ende", "TIME"),
        ("stundenplan", "pause2_beginn", "TIME"),
        ("stundenplan", "pause2_ende", "TIME"),
    )
    with engine.begin() as conn:
        for tabellenname, spaltenname, spaltentyp in additions:
            if tabellenname not in inspector.get_table_names():
                continue
            spalten = {c["name"] for c in inspector.get_columns(tabellenname)}
            if spaltenname in spalten:
                continue
            conn.execute(
                text(
                    f"ALTER TABLE {tabellenname} ADD COLUMN {spaltenname} {spaltentyp}"
                )
            )


def init_db(engine) -> None:
    import External.Infrastructure.sqlmodel_tables  # noqa: F401 - Tabellen bei SQLModel registrieren

    SQLModel.metadata.create_all(engine)
    _ensure_feiertag_hinweis_column(engine)
    _rename_pause_columns(engine)
    _ensure_pause2_columns(engine)
    _drop_urlaubsantrag_urlaubstagsname_column(engine)
