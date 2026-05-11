from __future__ import annotations

from datetime import date, time
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class ArbeitszeitBasis(BaseModel):
    uhrzeit_von: time = Field(description="Startzeit")
    uhrzeit_bis: time = Field(description="Endzeit")
    pause_beginn: Optional[time] = Field(default=None, description="Start der Unterbrechung")
    pause_ende: Optional[time] = Field(default=None, description="Ende der Unterbrechung")
    pause2_beginn: Optional[time] = Field(default=None, description="Start der zweiten Unterbrechung")
    pause2_ende: Optional[time] = Field(default=None, description="Ende der zweiten Unterbrechung")
    anmerkung: Optional[str] = Field(default=None, max_length=80)

    @model_validator(mode="after")
    def pruefe_zeitraeume(self) -> "ArbeitszeitBasis":
        if self.uhrzeit_von >= self.uhrzeit_bis:
            raise ValueError("uhrzeit_von muss vor uhrzeit_bis liegen.")

        if (self.pause_beginn is None) ^ (self.pause_ende is None):
            raise ValueError("pause_beginn und pause_ende muessen gemeinsam gesetzt sein.")

        if self.pause_beginn and self.pause_ende:
            if self.pause_beginn >= self.pause_ende:
                raise ValueError("pause_beginn muss vor pause_ende liegen.")
            if self.pause_beginn < self.uhrzeit_von or self.pause_ende > self.uhrzeit_bis:
                raise ValueError("Unterbrechung muss innerhalb der Arbeitszeit liegen.")

        if (self.pause2_beginn is None) ^ (self.pause2_ende is None):
            raise ValueError("pause2_beginn und pause2_ende muessen gemeinsam gesetzt sein.")

        if self.pause2_beginn and self.pause2_ende:
            if self.pause2_beginn >= self.pause2_ende:
                raise ValueError("pause2_beginn muss vor pause2_ende liegen.")
            if self.pause2_beginn < self.uhrzeit_von or self.pause2_ende > self.uhrzeit_bis:
                raise ValueError("Die zweite Unterbrechung muss innerhalb der Arbeitszeit liegen.")

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
