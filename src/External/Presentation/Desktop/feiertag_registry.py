from __future__ import annotations

from datetime import date

from PySide6.QtCore import QObject, Signal

from Core.Domain.models.models_worktime import Feiertag


class FeiertagRegistry(QObject):
    """Gemeinsamer Speicher für Feiertage (nach Datum) mit Benachrichtigung bei Änderungen."""

    feiertage_geaendert = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._nach_datum: dict[date, Feiertag] = {}

    def aktualisiere_jahr(
        self,
        jahr: int,
        eintraege: list[Feiertag],
        benachrichtigen: bool = True,
    ) -> None:
        for d in list(self._nach_datum.keys()):
            if d.year == jahr:
                del self._nach_datum[d]
        for eintrag in eintraege:
            self._nach_datum[eintrag.datum] = eintrag
        if benachrichtigen:
            self.feiertage_geaendert.emit(jahr)

    def nach_datum(self, d: date) -> Feiertag | None:
        return self._nach_datum.get(d)

    def snapshot_fuer_monat(self, jahr: int, monat: int) -> dict[date, Feiertag]:
        return {
            d: e
            for d, e in self._nach_datum.items()
            if d.year == jahr and d.month == monat
        }
