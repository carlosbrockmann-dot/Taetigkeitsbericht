from __future__ import annotations

from datetime import date
from typing import Optional

from ..interfaces.feiertag_repository_interface import IFeiertagRepository
from ..models.models_worktime import Feiertag


class FeiertagService:
    def __init__(self, repository: IFeiertagRepository) -> None:
        self._repository = repository

    def erfasse_feiertag(self, eintrag: Feiertag) -> Feiertag:
        vorhandene_eintraege = self._repository.get_by_datum(eintrag.datum)
        if vorhandene_eintraege:
            raise ValueError("Pro Datum ist nur ein Feiertagseintrag erlaubt.")
        return self._repository.add(eintrag)

    def hole_feiertag(self, datum: date) -> list[Feiertag]:
        return self._repository.get_by_datum(datum)

    def liste_feiertage(self, jahr: Optional[int] = None) -> list[Feiertag]:
        return self._repository.list_all(jahr=jahr)

    def loesche_feiertag(self, datum: date) -> bool:
        return self._repository.delete_by_datum(datum)
