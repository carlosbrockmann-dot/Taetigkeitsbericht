from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ArbeitszeitBasis(BaseModel):
    uhrzeit_von: time = Field(description="Startzeit")
    uhrzeit_bis: time = Field(description="Endzeit")
    unterbrechung_beginn: Optional[time] = Field(default=None, description="Start der Unterbrechung")
    unterbrechung_ende: Optional[time] = Field(default=None, description="Ende der Unterbrechung")
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> "ArbeitszeitBasis":
        if self.uhrzeit_von >= self.uhrzeit_bis:
            raise ValueError("uhrzeit_von muss vor uhrzeit_bis liegen.")

        if (self.unterbrechung_beginn is None) ^ (self.unterbrechung_ende is None):
            raise ValueError("unterbrechung_beginn und unterbrechung_ende muessen gemeinsam gesetzt sein.")

        if self.unterbrechung_beginn and self.unterbrechung_ende:
            if self.unterbrechung_beginn >= self.unterbrechung_ende:
                raise ValueError("unterbrechung_beginn muss vor unterbrechung_ende liegen.")
            if self.unterbrechung_beginn < self.uhrzeit_von or self.unterbrechung_ende > self.uhrzeit_bis:
                raise ValueError("Unterbrechung muss innerhalb der Arbeitszeit liegen.")

        return self


class Zeiteintrag(ArbeitszeitBasis):
    id: Optional[UUID] = None
    datum: date


class Stundenplan(ArbeitszeitBasis):
    id: Optional[int] = None
    wochentag: int = Field(ge=1, le=7, description="1=Montag, 7=Sonntag")


class Feiertag(BaseModel):
    datum: date
    feiertagsname: str = Field(max_length=80, description="Name des Feiertags")
    hinweis: Optional[str] = Field(default=None, max_length=80, description="Zusatzinfo, z. B. aus Feiertags-API")
