from __future__ import annotations

from datetime import date
from typing import Optional, Protocol

from ..models.models_worktime import Zeiteintrag


class IZeiteintragRepository(Protocol):
    def add(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        ...

    def get_by_datum(self, datum: date) -> list[Zeiteintrag]:
        ...

    def list_all(self, jahr: Optional[int] = None) -> list[Zeiteintrag]:
        ...

    def delete_by_datum(self, datum: date) -> bool:
        ...
