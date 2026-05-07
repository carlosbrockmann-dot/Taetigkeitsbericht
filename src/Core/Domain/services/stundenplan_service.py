from __future__ import annotations

from datetime import time

from ..models.models_worktime import Stundenplan
from ..interfaces.stundenplan_repository_interface import IStundenplanRepository


class StundenplanService:
    def __init__(self, repository: IStundenplanRepository) -> None:
        self._repository = repository

    def erfasse_stundenplaneintrag(self, eintrag: Stundenplan) -> Stundenplan:
        vorhandene_eintraege = self._repository.get_by_wochentag(eintrag.wochentag)
        for vorhandener_eintrag in vorhandene_eintraege:
            if self._zeitraeume_ueberschneiden_sich(
                eintrag.uhrzeit_von,
                eintrag.uhrzeit_bis,
                vorhandener_eintrag.uhrzeit_von,
                vorhandener_eintrag.uhrzeit_bis,
            ):
                raise ValueError(
                    "Der Zeitraum ueberschneidet sich mit einem bestehenden Stundenplaneintrag am selben Wochentag."
                )
        return self._repository.add(eintrag)

    def hole_stundenplan(self, wochentag: int) -> list[Stundenplan]:
        return self._repository.get_by_wochentag(wochentag)

    def liste_stundenplaeneintraege(self) -> list[Stundenplan]:
        return self._repository.list_all()

    def loesche_stundenplan(self, wochentag: int) -> bool:
        return self._repository.delete_by_wochentag(wochentag)

    @staticmethod
    def _zeitraeume_ueberschneiden_sich(
        neuer_von: time,
        neuer_bis: time,
        bestehender_von: time,
        bestehender_bis: time,
    ) -> bool:
        return neuer_von < bestehender_bis and bestehender_von < neuer_bis
