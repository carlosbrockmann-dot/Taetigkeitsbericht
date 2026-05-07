from __future__ import annotations

from typing import Protocol

from .models_worktime import Stundenplan


class IStundenplanRepository(Protocol):
    def add(self, eintrag: Stundenplan) -> Stundenplan:
        ...

    def get_by_wochentag(self, wochentag: int) -> list[Stundenplan]:
        ...

    def list_all(self) -> list[Stundenplan]:
        ...

    def delete_by_wochentag(self, wochentag: int) -> bool:
        ...
