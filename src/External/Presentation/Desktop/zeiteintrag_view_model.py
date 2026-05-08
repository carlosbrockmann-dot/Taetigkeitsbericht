from __future__ import annotations

from calendar import monthrange
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

    def add_row(self, position: int | None = None, datum: str = "") -> int:
        return self._table_model.add_empty_row(position=position, datum=datum)

    def remove_rows(self, row_indices: list[int]) -> None:
        self._table_model.remove_rows(row_indices)

    def lade_zeitraum(self, jahr: int, monat: int) -> None:
        eintraege = self._anwendung.liste(jahr=jahr, monat=monat)
        eintraege_nach_tag: dict[date, list[Zeiteintrag]] = {}
        for eintrag in eintraege:
            eintraege_nach_tag.setdefault(eintrag.datum, []).append(eintrag)

        tage_im_monat = monthrange(jahr, monat)[1]
        rows: list[ZeiteintragRow] = []
        for tag in range(1, tage_im_monat + 1):
            aktuelles_datum = date(jahr, monat, tag)
            tages_eintraege = eintraege_nach_tag.get(aktuelles_datum, [])
            if tages_eintraege:
                rows.extend(self._map_to_row(eintrag) for eintrag in tages_eintraege)
                continue
            rows.append(ZeiteintragRow(datum=aktuelles_datum.strftime("%d.%m.%Y")))

        self._table_model.set_rows(rows)
        self.status_changed.emit(
            f"{len(rows)} Zeile(n) fuer {monat:02d}/{jahr} geladen ({len(eintraege)} aus Datenbank)."
        )

    def speichere_alle(self) -> bool:
        if not self._table_model.rows:
            self.error_occurred.emit("Es sind keine Zeilen zum Speichern vorhanden.")
            return False

        zeilen_zum_speichern = [
            (zeilen_nummer, row)
            for zeilen_nummer, row in enumerate(self._table_model.rows, start=1)
            if row.uhrzeit_von.strip() or row.uhrzeit_bis.strip()
        ]
        if not zeilen_zum_speichern:
            self.error_occurred.emit(
                "Es wurden keine Zeilen mit ausgefuellter Spalte 'Von' oder 'Bis' gefunden."
            )
            return False

        erfolgreich = 0
        fehler: list[str] = []
        for zeilen_nummer, row in zeilen_zum_speichern:
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

    @staticmethod
    def _map_to_row(eintrag: Zeiteintrag) -> ZeiteintragRow:
        return ZeiteintragRow(
            id=eintrag.id,
            datum=eintrag.datum.strftime("%d.%m.%Y"),
            uhrzeit_von=eintrag.uhrzeit_von.strftime("%H:%M"),
            uhrzeit_bis=eintrag.uhrzeit_bis.strftime("%H:%M"),
            unterbrechung_beginn=eintrag.unterbrechung_beginn.strftime("%H:%M")
            if eintrag.unterbrechung_beginn
            else "",
            unterbrechung_ende=eintrag.unterbrechung_ende.strftime("%H:%M") if eintrag.unterbrechung_ende else "",
            anmerkung=eintrag.anmerkung or "",
        )
