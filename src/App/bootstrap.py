from __future__ import annotations

import sys
from pathlib import Path

from injector import Injector

# Erlaubt direkten Start dieser Datei ohne gesetztes PYTHONPATH.
SRC_ROOT = Path(__file__).resolve().parents[1]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from Core.Application.di import ApplicationDIModule
from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Infrastructure.di import InfrastructureConfig, InfrastructureDIModule
from External.Presentation.Desktop.di import DesktopPresentationDIModule


def create_injector(database_url: str = "sqlite:///taetigkeitsbericht.db") -> Injector:
    config = InfrastructureConfig(database_url=database_url)
    return Injector(
        [
            InfrastructureDIModule(),
            ApplicationDIModule(),
            DesktopPresentationDIModule(),
            lambda binder: binder.bind(InfrastructureConfig, to=config),
        ]
    )


def build_applications(injector_instance: Injector) -> tuple[
    ZeiteintragAnwendung,
    StundenplanAnwendung,
    FeiertagAnwendung,
]:
    return (
        injector_instance.get(ZeiteintragAnwendung),
        injector_instance.get(StundenplanAnwendung),
        injector_instance.get(FeiertagAnwendung),
    )
