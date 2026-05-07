from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import extract
from sqlmodel import Session, select

from Core.Domain.models.models_worktime import Zeiteintrag
from External.Infrastructure.sqlmodel_tables import ZeiteintragTable


def _row_to_domain(row: ZeiteintragTable) -> Zeiteintrag:
    return Zeiteintrag(
        id=UUID(row.id),
        datum=row.datum,
        uhrzeit_von=row.uhrzeit_von,
        uhrzeit_bis=row.uhrzeit_bis,
        unterbrechung_beginn=row.unterbrechung_beginn,
        unterbrechung_ende=row.unterbrechung_ende,
        anmerkung=row.anmerkung,
    )


class SqlZeiteintragRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        row_id = str(eintrag.id or uuid4())
        row = self._session.get(ZeiteintragTable, row_id)
        if row is None:
            row = ZeiteintragTable(
                id=row_id,
                datum=eintrag.datum,
                uhrzeit_von=eintrag.uhrzeit_von,
                uhrzeit_bis=eintrag.uhrzeit_bis,
                unterbrechung_beginn=eintrag.unterbrechung_beginn,
                unterbrechung_ende=eintrag.unterbrechung_ende,
                anmerkung=eintrag.anmerkung,
            )
            self._session.add(row)
        else:
            row.datum = eintrag.datum
            row.uhrzeit_von = eintrag.uhrzeit_von
            row.uhrzeit_bis = eintrag.uhrzeit_bis
            row.unterbrechung_beginn = eintrag.unterbrechung_beginn
            row.unterbrechung_ende = eintrag.unterbrechung_ende
            row.anmerkung = eintrag.anmerkung
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_datum(self, datum: date) -> list[Zeiteintrag]:
        stmt = (
            select(ZeiteintragTable)
            .where(ZeiteintragTable.datum == datum)
            .order_by(ZeiteintragTable.uhrzeit_von)
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def list_all(self, jahr: Optional[int] = None, monat: Optional[int] = None) -> list[Zeiteintrag]:
        stmt = select(ZeiteintragTable).order_by(ZeiteintragTable.datum, ZeiteintragTable.uhrzeit_von)
        if jahr is not None and monat is not None:
            stmt = stmt.where(extract("year", ZeiteintragTable.datum) == jahr).where(
                extract("month", ZeiteintragTable.datum) == monat
            )
        elif jahr is not None:
            stmt = stmt.where(extract("year", ZeiteintragTable.datum) == jahr)
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_datum(self, datum: date) -> bool:
        rows = list(self._session.exec(select(ZeiteintragTable).where(ZeiteintragTable.datum == datum)).all())
        for row in rows:
            self._session.delete(row)
        self._session.commit()
        return len(rows) > 0
