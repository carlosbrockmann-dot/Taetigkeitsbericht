from __future__ import annotations

from injector import Module, provider, singleton

from App.app_config import AppConfig
from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Presentation.Desktop.feiertag_registry import FeiertagRegistry
from External.Presentation.Desktop.feiertag_view import FeiertagView
from External.Presentation.Desktop.feiertag_view_model import FeiertagViewModel
from External.Presentation.Desktop.stundenplan_registry import StundenplanRegistry
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


class DesktopPresentationDIModule(Module):
    @singleton
    @provider
    def provide_feiertag_registry(self) -> FeiertagRegistry:
        return FeiertagRegistry()

    @singleton
    @provider
    def provide_stundenplan_registry(self) -> StundenplanRegistry:
        return StundenplanRegistry()

    @provider
    def provide_zeiteintrag_view_model(
        self,
        anwendung: ZeiteintragAnwendung,
        feiertag_anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
        stundenplan_anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
        app_config: AppConfig,
    ) -> ZeiteintragViewModel:
        return ZeiteintragViewModel(
            anwendung,
            feiertag_anwendung,
            feiertag_registry,
            stundenplan_anwendung,
            stundenplan_registry,
            app_config.soll_nach_vertrag_nach_wochentag,
        )

    @provider
    def provide_stundenplan_view_model(
        self,
        anwendung: StundenplanAnwendung,
        stundenplan_registry: StundenplanRegistry,
    ) -> StundenplanViewModel:
        return StundenplanViewModel(anwendung, stundenplan_registry)

    @provider
    def provide_feiertag_view_model(
        self,
        anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
    ) -> FeiertagViewModel:
        return FeiertagViewModel(anwendung, feiertag_registry)

    @provider
    def provide_stundenplan_view(
        self, view_model: StundenplanViewModel
    ) -> StundenplanView:
        return StundenplanView(view_model)

    @provider
    def provide_feiertag_view(
        self, view_model: FeiertagViewModel
    ) -> FeiertagView:
        return FeiertagView(view_model)

    @provider
    def provide_zeiteintrag_window(
        self,
        view_model: ZeiteintragViewModel,
        stundenplan_view: StundenplanView,
        feiertag_view: FeiertagView,
        app_config: AppConfig,
    ) -> ZeiteintragWindow:
        return ZeiteintragWindow(
            view_model,
            stundenplan_view,
            feiertag_view,
            excel_export=app_config.zeiteintrag_excel_export,
        )
