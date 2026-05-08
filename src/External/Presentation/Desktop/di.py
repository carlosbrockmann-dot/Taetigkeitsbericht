from __future__ import annotations

from injector import Module, provider, singleton

from Core.Application.feiertag_anwendung import FeiertagAnwendung
from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Presentation.Desktop.feiertag_registry import FeiertagRegistry
from External.Presentation.Desktop.feiertag_view import FeiertagView
from External.Presentation.Desktop.feiertag_view_model import FeiertagViewModel
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


class DesktopPresentationDIModule(Module):
    @singleton
    @provider
    def provide_feiertag_registry(self) -> FeiertagRegistry:
        return FeiertagRegistry()

    @provider
    def provide_zeiteintrag_view_model(
        self,
        anwendung: ZeiteintragAnwendung,
        feiertag_anwendung: FeiertagAnwendung,
        feiertag_registry: FeiertagRegistry,
    ) -> ZeiteintragViewModel:
        return ZeiteintragViewModel(anwendung, feiertag_anwendung, feiertag_registry)

    @provider
    def provide_stundenplan_view_model(
        self, anwendung: StundenplanAnwendung
    ) -> StundenplanViewModel:
        return StundenplanViewModel(anwendung)

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
    ) -> ZeiteintragWindow:
        return ZeiteintragWindow(view_model, stundenplan_view, feiertag_view)
