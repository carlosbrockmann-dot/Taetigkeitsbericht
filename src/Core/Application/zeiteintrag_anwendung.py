from __future__ import annotations

from datetime import date
from typing import Optional

from Core.Domain.models.models_worktime import Stundenplan, Zeiteintrag
from Core.Domain.services.zeiteintrag_service import ZeiteintragService


class ZeiteintragAnwendung:
    def __init__(self, service: ZeiteintragService) -> None:
        self._service = service

    def erfasse(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        return self._service.erfasse_zeiteintrag(eintrag)

    def erfasse_aus_stundenplan(
        self, datum: date, stundenplan_eintrag: Stundenplan
    ) -> Zeiteintrag:
        # Wie Stundenplan.wochentag: 1 = Montag, 7 = Sonntag (ISO 8601)
        erwarteter_wochentag = datum.isoweekday()
        if stundenplan_eintrag.wochentag != erwarteter_wochentag:
            raise ValueError(
                "Das Datum passt nicht zum Wochentag des Stundenplaneintrags "
                f"(Stundenplan: {stundenplan_eintrag.wochentag}, "
                f"fuer das Datum erwartet: {erwarteter_wochentag})."
            )
        zeiteintrag = Zeiteintrag(
            datum=datum,
            uhrzeit_von=stundenplan_eintrag.uhrzeit_von,
            uhrzeit_bis=stundenplan_eintrag.uhrzeit_bis,
            unterbrechung_beginn=stundenplan_eintrag.unterbrechung_beginn,
            unterbrechung_ende=stundenplan_eintrag.unterbrechung_ende,
            anmerkung=stundenplan_eintrag.anmerkung,
        )
        return self.erfasse(zeiteintrag)

    def hole_fuer_datum(self, datum: date) -> list[Zeiteintrag]:
        return self._service.hole_zeiteintrag(datum)

    def liste(self, jahr: Optional[int] = None) -> list[Zeiteintrag]:
        return self._service.liste_zeiteintraege(jahr=jahr)

    def loesche_fuer_datum(self, datum: date) -> bool:
        return self._service.loesche_zeiteintrag(datum)
