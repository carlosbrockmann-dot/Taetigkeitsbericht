from __future__ import annotations

from dataclasses import dataclass

from injector import Module, provider
from sqlmodel import Session

from Core.Domain.interfaces.feiertag_repository_interface import IFeiertagRepository
from Core.Domain.interfaces.stundenplan_repository_interface import IStundenplanRepository
from Core.Domain.interfaces.zeiteintrag_repository_interface import IZeiteintragRepository
from External.Infrastructure.database import create_sqlite_engine, init_db
from External.Infrastructure.repositories.feiertag_sqlmodel_repository import SqlFeiertagRepository
from External.Infrastructure.repositories.stundenplan_sqlmodel_repository import SqlStundenplanRepository
from External.Infrastructure.repositories.zeiteintrag_sqlmodel_repository import SqlZeiteintragRepository


@dataclass(frozen=True)
class InfrastructureConfig:
    database_url: str = "sqlite:///taetigkeitsbericht.db"


class InfrastructureDIModule(Module):
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
