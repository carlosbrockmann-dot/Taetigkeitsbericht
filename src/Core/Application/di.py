from __future__ import annotations

from injector import Binder, Module, provider

from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from Core.Domain.interfaces.auth_interface import IAuthService
from Core.Domain.interfaces.feiertag_repository_interface import IFeiertagRepository
from Core.Domain.interfaces.stundenplan_repository_interface import IStundenplanRepository
from Core.Domain.interfaces.zeiteintrag_repository_interface import IZeiteintragRepository
from Core.Domain.services.auth_service import AuthService
from Core.Domain.services.feiertag_service import FeiertagService
from Core.Domain.services.stundenplan_service import StundenplanService
from Core.Domain.services.zeiteintrag_service import ZeiteintragService


class ApplicationDIModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(IAuthService, to=AuthService)

    @provider
    def provide_zeiteintrag_service(
        self, repository: IZeiteintragRepository
    ) -> ZeiteintragService:
        return ZeiteintragService(repository)

    @provider
    def provide_stundenplan_service(
        self, repository: IStundenplanRepository
    ) -> StundenplanService:
        return StundenplanService(repository)

    @provider
    def provide_feiertag_service(self, repository: IFeiertagRepository) -> FeiertagService:
        return FeiertagService(repository)

    @provider
    def provide_zeiteintrag_anwendung(
        self, service: ZeiteintragService
    ) -> ZeiteintragAnwendung:
        return ZeiteintragAnwendung(service)

    @provider
    def provide_stundenplan_anwendung(
        self, service: StundenplanService
    ) -> StundenplanAnwendung:
        return StundenplanAnwendung(service)

    @provider
    def provide_feiertag_anwendung(self, service: FeiertagService) -> FeiertagAnwendung:
        return FeiertagAnwendung(service)
