from __future__ import annotations

from datetime import date

from .models import Zeiteintrag
from .zeiteintrag_repository import ZeiteintragRepository


class ZeiteintragService:
    def __init__(self, repository: ZeiteintragRepository) -> None:
        self._repository = repository

    def erfasse_zeiteintrag(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        vorhandener_eintrag = self._repository.get_by_datum(eintrag.datum)
        if vorhandener_eintrag is not None:
            raise ValueError(f"Fuer das Datum {eintrag.datum} existiert bereits ein Eintrag.")
        return self._repository.add(eintrag)

    def hole_zeiteintrag(self, datum: date) -> Zeiteintrag | None:
        return self._repository.get_by_datum(datum)

    def liste_zeiteintraege(self) -> list[Zeiteintrag]:
        return self._repository.list_all()

    def loesche_zeiteintrag(self, datum: date) -> bool:
        return self._repository.delete_by_datum(datum)
