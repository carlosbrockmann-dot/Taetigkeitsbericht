from __future__ import annotations

from datetime import date, time
from typing import Optional

from .models_worktime import Zeiteintrag
from .zeiteintrag_repository_interface import IZeiteintragRepository


class ZeiteintragService:
    def __init__(self, repository: IZeiteintragRepository) -> None:
        self._repository = repository

    def erfasse_zeiteintrag(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        vorhandene_eintraege = self._repository.get_by_datum(eintrag.datum)
        for vorhandener_eintrag in vorhandene_eintraege:
            if self._zeitraeume_ueberschneiden_sich(
                eintrag.uhrzeit_von,
                eintrag.uhrzeit_bis,
                vorhandener_eintrag.uhrzeit_von,
                vorhandener_eintrag.uhrzeit_bis,
            ):
                raise ValueError(
                    "Der Zeitraum ueberschneidet sich mit einem bestehenden Zeiteintrag am selben Datum."
                )
        return self._repository.add(eintrag)

    def hole_zeiteintrag(self, datum: date) -> list[Zeiteintrag]:
        return self._repository.get_by_datum(datum)

    def liste_zeiteintraege(self, jahr: Optional[int] = None) -> list[Zeiteintrag]:
        return self._repository.list_all(jahr=jahr)

    def loesche_zeiteintrag(self, datum: date) -> bool:
        return self._repository.delete_by_datum(datum)

    @staticmethod
    def _zeitraeume_ueberschneiden_sich(
        neuer_von: time,
        neuer_bis: time,
        bestehender_von: time,
        bestehender_bis: time,
    ) -> bool:
        return neuer_von < bestehender_bis and bestehender_von < neuer_bis
