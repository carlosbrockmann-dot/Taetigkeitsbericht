from __future__ import annotations

from sqlmodel import Session, select

from Core.Domain.models_worktime import Stundenplan
from External.Infrastructure.sqlmodel_tables import StundenplanTable


def _row_to_domain(row: StundenplanTable) -> Stundenplan:
    return Stundenplan(
        wochentag=row.wochentag,
        uhrzeit_von=row.uhrzeit_von,
        uhrzeit_bis=row.uhrzeit_bis,
        unterbrechung_beginn=row.unterbrechung_beginn,
        unterbrechung_ende=row.unterbrechung_ende,
        anmerkung=row.anmerkung,
    )


class SqlStundenplanRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, eintrag: Stundenplan) -> Stundenplan:
        row = StundenplanTable(
            wochentag=eintrag.wochentag,
            uhrzeit_von=eintrag.uhrzeit_von,
            uhrzeit_bis=eintrag.uhrzeit_bis,
            unterbrechung_beginn=eintrag.unterbrechung_beginn,
            unterbrechung_ende=eintrag.unterbrechung_ende,
            anmerkung=eintrag.anmerkung,
        )
        self._session.add(row)
        self._session.commit()
        self._session.refresh(row)
        return _row_to_domain(row)

    def get_by_wochentag(self, wochentag: int) -> list[Stundenplan]:
        stmt = (
            select(StundenplanTable)
            .where(StundenplanTable.wochentag == wochentag)
            .order_by(StundenplanTable.uhrzeit_von)
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def list_all(self) -> list[Stundenplan]:
        stmt = select(StundenplanTable).order_by(
            StundenplanTable.wochentag,
            StundenplanTable.uhrzeit_von,
        )
        rows = list(self._session.exec(stmt).all())
        return [_row_to_domain(r) for r in rows]

    def delete_by_wochentag(self, wochentag: int) -> bool:
        rows = list(
            self._session.exec(
                select(StundenplanTable).where(StundenplanTable.wochentag == wochentag)
            ).all()
        )
        for row in rows:
            self._session.delete(row)
        self._session.commit()
        return len(rows) > 0
