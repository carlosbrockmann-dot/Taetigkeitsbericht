from __future__ import annotations

from datetime import date
from typing import Protocol

from .models import Zeiteintrag


class ZeiteintragRepository(Protocol):
    def add(self, eintrag: Zeiteintrag) -> Zeiteintrag:
        ...

    def get_by_datum(self, datum: date) -> Zeiteintrag | None:
        ...

    def list_all(self) -> list[Zeiteintrag]:
        ...

    def delete_by_datum(self, datum: date) -> bool:
        ...
