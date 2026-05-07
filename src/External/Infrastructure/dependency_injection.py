from __future__ import annotations

from dataclasses import dataclass

from injector import Binder, Injector, Module, provider
from sqlmodel import Session

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
from External.Infrastructure.database import create_sqlite_engine, init_db
from External.Infrastructure.repositories.feiertag_sqlmodel_repository import SqlFeiertagRepository
from External.Infrastructure.repositories.stundenplan_sqlmodel_repository import SqlStundenplanRepository
from External.Infrastructure.repositories.zeiteintrag_sqlmodel_repository import SqlZeiteintragRepository


@dataclass(frozen=True)
class InfrastructureConfig:
    database_url: str = "sqlite:///taetigkeitsbericht.db"


class AppDIModule(Module):
    def configure(self, binder: Binder) -> None:
        binder.bind(IAuthService, to=AuthService)

    @provider
    def provide_session(self, config: InfrastructureConfig) -> Session:
        engine = create_sqlite_engine(config.database_url)
        init_db(engine)
        return Session(engine)

    @provider
    def provide_feiertag_repository(self, session: Session) -> IFeiertagRepository:
        return SqlFeiertagRepository(session)

    @provider
    def provide_stundenplan_repository(self, session: Session) -> IStundenplanRepository:
        return SqlStundenplanRepository(session)

    @provider
    def provide_zeiteintrag_repository(self, session: Session) -> IZeiteintragRepository:
        return SqlZeiteintragRepository(session)

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


def create_injector(database_url: str = "sqlite:///taetigkeitsbericht.db") -> Injector:
    config = InfrastructureConfig(database_url=database_url)
    return Injector([AppDIModule(), lambda binder: binder.bind(InfrastructureConfig, to=config)])


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
