from __future__ import annotations

from injector import Module, provider

from Core.Application.stundenplan_anwendung import StundenplanAnwendung
from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.stundenplan_view_model import StundenplanViewModel
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


class DesktopPresentationDIModule(Module):
    @provider
    def provide_zeiteintrag_view_model(
        self, anwendung: ZeiteintragAnwendung
    ) -> ZeiteintragViewModel:
        return ZeiteintragViewModel(anwendung)

    @provider
    def provide_stundenplan_view_model(
        self, anwendung: StundenplanAnwendung
    ) -> StundenplanViewModel:
        return StundenplanViewModel(anwendung)

    @provider
    def provide_stundenplan_view(
        self, view_model: StundenplanViewModel
    ) -> StundenplanView:
        return StundenplanView(view_model)

    @provider
    def provide_zeiteintrag_window(
        self,
        view_model: ZeiteintragViewModel,
        stundenplan_view: StundenplanView,
    ) -> ZeiteintragWindow:
        return ZeiteintragWindow(view_model, stundenplan_view)
