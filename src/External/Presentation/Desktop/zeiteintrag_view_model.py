from __future__ import annotations

from datetime import date, datetime, time

from PySide6.QtCore import QObject, Signal

from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from Core.Domain.models.models_worktime import Zeiteintrag
from External.Presentation.Desktop.zeiteintrag_table_model import ZeiteintragRow, ZeiteintragTableModel


class ZeiteintragViewModel(QObject):
    status_changed = Signal(str)
    error_occurred = Signal(str)

    def __init__(self, anwendung: ZeiteintragAnwendung) -> None:
        super().__init__()
        self._anwendung = anwendung
        self._table_model = ZeiteintragTableModel()

    @property
    def table_model(self) -> ZeiteintragTableModel:
        return self._table_model

    def add_row(self) -> None:
        self._table_model.add_empty_row()

    def remove_rows(self, row_indices: list[int]) -> None:
        self._table_model.remove_rows(row_indices)

    def lade_zeitraum(self, jahr: int, monat: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr, monat=monat)
        rows = [
            ZeiteintragRow(
                id=e.id,
                datum=e.datum.strftime("%d.%m.%Y"),
                uhrzeit_von=e.uhrzeit_von.strftime("%H:%M"),
                uhrzeit_bis=e.uhrzeit_bis.strftime("%H:%M"),
                unterbrechung_beginn=e.unterbrechung_beginn.strftime("%H:%M") if e.unterbrechung_beginn else "",
                unterbrechung_ende=e.unterbrechung_ende.strftime("%H:%M") if e.unterbrechung_ende else "",
                anmerkung=e.anmerkung or "",
            )
            for e in eintraege
        ]
        self._table_model.set_rows(rows)
        self.status_changed.emit(f"{len(rows)} Eintrag/Eintreage fuer {monat:02d}/{jahr} geladen.")

    def speichere_alle(self) -> bool:
        if not self._table_model.rows:
            self.error_occurred.emit("Es sind keine Zeilen zum Speichern vorhanden.")
            return False

        erfolgreich = 0
        fehler: list[str] = []
        for zeilen_nummer, row in enumerate(self._table_model.rows, start=1):
            try:
                eintrag = Zeiteintrag(
                    id=row.id,
                    datum=self._parse_date(row.datum),
                    uhrzeit_von=self._parse_time(row.uhrzeit_von, "uhrzeit_von"),
                    uhrzeit_bis=self._parse_time(row.uhrzeit_bis, "uhrzeit_bis"),
                    unterbrechung_beginn=self._parse_optional_time(row.unterbrechung_beginn),
                    unterbrechung_ende=self._parse_optional_time(row.unterbrechung_ende),
                    anmerkung=row.anmerkung or None,
                )
                gespeicherter_eintrag = self._anwendung.erfasse(eintrag)
                row.id = gespeicherter_eintrag.id
                erfolgreich += 1
            except Exception as exc:  # noqa: BLE001
                fehler.append(f"Zeile {zeilen_nummer}: {exc}")

        if fehler:
            self.error_occurred.emit("\n".join(fehler))
        self.status_changed.emit(f"{erfolgreich} Zeile(n) gespeichert, {len(fehler)} Fehler.")
        return not fehler

    @staticmethod
    def _parse_date(value: str) -> date:
        return datetime.strptime(value.strip(), "%d.%m.%Y").date()

    @staticmethod
    def _parse_time(value: str, feldname: str) -> time:
        text = value.strip()
        if not text:
            raise ValueError(f"{feldname} darf nicht leer sein.")
        return datetime.strptime(text, "%H:%M").time()

    @staticmethod
    def _parse_optional_time(value: str) -> time | None:
        text = value.strip()
        if not text:
            return None
        return datetime.strptime(text, "%H:%M").time()
