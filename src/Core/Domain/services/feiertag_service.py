from __future__ import annotations

from datetime import date
import json
from pathlib import Path
import urllib.parse
import urllib.request
from typing import Optional
import tomllib

from ..interfaces.feiertag_repository_interface import IFeiertagRepository
from ..models.models_worktime import Feiertag


class FeiertagService:
    _STANDARD_KALENDER_ID = "de.german#holiday@group.v.calendar.google.com"
    _BUNDESLAND_ZU_CONFIG_KEY: dict[str, str] = {
        "hessen": "kalender_id_hessen",
    }

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

    def lade_feiertage_von_google(
        self,
        jahr: int,
        api_key: str,
        kalender_id: str | None = None,
    ) -> list[Feiertag]:
        if jahr < 1900:
            raise ValueError("jahr muss >= 1900 sein.")
        if not api_key.strip():
            raise ValueError("api_key darf nicht leer sein.")

        config_path = Path(__file__).resolve().parents[3] / "feiertag.toml"
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        google_config = config.get("google", {})
        basis_url = str(google_config.get("url", "")).strip()
        if not basis_url:
            raise ValueError("google.url fehlt in src/feiertag.toml.")
        genutzte_kalender_id = self._resolve_kalender_id(
            google_config=google_config,
            kalender_id=kalender_id,
        )

        params = {
            "key": api_key.strip(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "timeMin": f"{jahr}-01-01T00:00:00Z",
            "timeMax": f"{jahr + 1}-01-01T00:00:00Z",
        }
        encoded_kalender_id = urllib.parse.quote(genutzte_kalender_id, safe="")
        query = urllib.parse.urlencode(params)
        request_url = f"{basis_url.format(calendar_id=encoded_kalender_id)}?{query}"

        request = urllib.request.Request(
            request_url,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))

        feiertage: list[Feiertag] = []
        for item in payload.get("items", []):
            start_info = item.get("start", {})
            datum_text = str(start_info.get("date", "")).strip()
            feiertagsname = str(item.get("summary", "")).strip()
            if not datum_text or not feiertagsname:
                continue
            try:
                datum = date.fromisoformat(datum_text)
            except ValueError:
                continue
            feiertage.append(Feiertag(datum=datum, feiertagsname=feiertagsname))

        return feiertage

    def _resolve_kalender_id(
        self,
        google_config: dict[str, object],
        kalender_id: str | None,
    ) -> str:
        if kalender_id and kalender_id.strip():
            return kalender_id.strip()

        bundesland = str(google_config.get("bundesland", "")).strip().lower()
        config_key = self._BUNDESLAND_ZU_CONFIG_KEY.get(bundesland)
        if config_key:
            regionale_kalender_id = str(google_config.get(config_key, "")).strip()
            if regionale_kalender_id:
                return regionale_kalender_id

        return self._STANDARD_KALENDER_ID
