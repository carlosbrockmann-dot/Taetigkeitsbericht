from __future__ import annotations

from PySide6.QtCore import QObject, Signal

from Core.Domain.models.models_worktime import Stundenplan
from External.Presentation.Desktop.stundenplan_table_model import (
    StundenplanRow,
    StundenplanTableModel,
)


class StundenplanRegistry(QObject):
    """Gemeinsamer Index Stundenplan: (Wochentag, Von) → Soll-Stunden (HH:MM)."""

    stundenplan_geaendert = Signal()

    def __init__(self) -> None:
        super().__init__()
        self._soll_nach_wochentag_und_von: dict[tuple[int, str], str] = {}

    def aktualisiere_aus_domain(
        self,
        eintraege: list[Stundenplan],
        benachrichtigen: bool = True,
    ) -> None:
        self._soll_nach_wochentag_und_von.clear()
        for eintrag in eintraege:
            von_s = eintrag.uhrzeit_von.strftime("%H:%M")
            bis_s = eintrag.uhrzeit_bis.strftime("%H:%M")
            pause_von = (
                eintrag.pause_beginn.strftime("%H:%M")
                if eintrag.pause_beginn
                else ""
            )
            pause_bis = (
                eintrag.pause_ende.strftime("%H:%M")
                if eintrag.pause_ende
                else ""
            )
            pause2_von = (
                eintrag.pause2_beginn.strftime("%H:%M")
                if eintrag.pause2_beginn
                else ""
            )
            pause2_bis = (
                eintrag.pause2_ende.strftime("%H:%M")
                if eintrag.pause2_ende
                else ""
            )
            soll = StundenplanTableModel._calculate_zuleistende_zeit(
                von_s, bis_s, pause_von, pause_bis, pause2_von, pause2_bis
            )
            schluessel = (eintrag.wochentag, self._normalisiere_uhrzeit(von_s))
            if soll:
                self._soll_nach_wochentag_und_von[schluessel] = soll
        if benachrichtigen:
            self.stundenplan_geaendert.emit()

    def aktualisiere_aus_zeilen(
        self,
        zeilen: list[StundenplanRow],
        benachrichtigen: bool = True,
    ) -> None:
        self._soll_nach_wochentag_und_von.clear()
        for row in zeilen:
            if not (row.uhrzeit_von.strip() or row.uhrzeit_bis.strip()):
                continue
            soll = StundenplanTableModel._calculate_zuleistende_zeit(
                row.uhrzeit_von,
                row.uhrzeit_bis,
                row.pause_beginn,
                row.pause_ende,
                row.pause2_beginn,
                row.pause2_ende,
            )
            schluessel = (row.wochentag, self._normalisiere_uhrzeit(row.uhrzeit_von))
            if soll:
                self._soll_nach_wochentag_und_von[schluessel] = soll
        if benachrichtigen:
            self.stundenplan_geaendert.emit()

    def soll_fuer(self, wochentag: int, uhrzeit_von: str) -> str:
        schluessel = (wochentag, self._normalisiere_uhrzeit(uhrzeit_von))
        return self._soll_nach_wochentag_und_von.get(schluessel, "")

    def gesamt_soll_fuer_wochentag(self, wochentag: int) -> str:
        """Summe aller Soll-Zeiten des Stundenplans fuer einen Wochentag (mehrere Bloecke)."""
        summe_minuten = 0
        for (wt, _von), soll in self._soll_nach_wochentag_und_von.items():
            if wt != wochentag:
                continue
            minuten = StundenplanRegistry._minuten_aus_hhmm(soll)
            if minuten is not None:
                summe_minuten += minuten
        if summe_minuten <= 0:
            return ""
        stunden, minuten = divmod(summe_minuten, 60)
        return f"{stunden:02d}:{minuten:02d}"

    @staticmethod
    def _minuten_aus_hhmm(text: str) -> int | None:
        roh = text.strip()
        if not roh or ":" not in roh:
            return None
        teile = roh.split(":", 1)
        if len(teile) != 2:
            return None
        try:
            h = int(teile[0])
            m = int(teile[1])
        except ValueError:
            return None
        if h < 0 or not 0 <= m < 60:
            return None
        return h * 60 + m

    @staticmethod
    def _normalisiere_uhrzeit(text: str) -> str:
        roh = text.strip()
        if not roh:
            return ""
        teile = roh.split(":", 1)
        if len(teile) != 2:
            return roh
        try:
            stunden = int(teile[0])
            minuten = int(teile[1])
        except ValueError:
            return roh
        return f"{stunden:02d}:{minuten:02d}"
