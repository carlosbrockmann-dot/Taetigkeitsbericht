from __future__ import annotations

from Core.Domain.models_worktime import Stundenplan
from Core.Domain.stundenplan_service import StundenplanService


class StundenplanAnwendung:
    def __init__(self, service: StundenplanService) -> None:
        self._service = service

    def erfasse(self, eintrag: Stundenplan) -> Stundenplan:
        return self._service.erfasse_stundenplaneintrag(eintrag)

    def hole_fuer_wochentag(self, wochentag: int) -> list[Stundenplan]:
        return self._service.hole_stundenplan(wochentag)

    def liste(self) -> list[Stundenplan]:
        return self._service.liste_stundenplaeneintraege()

    def loesche_fuer_wochentag(self, wochentag: int) -> bool:
        return self._service.loesche_stundenplan(wochentag)
