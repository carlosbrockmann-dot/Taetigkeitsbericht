from __future__ import annotations

from injector import Module, provider

from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


class DesktopPresentationDIModule(Module):
    @provider
    def provide_zeiteintrag_view_model(
        self, anwendung: ZeiteintragAnwendung
    ) -> ZeiteintragViewModel:
        return ZeiteintragViewModel(anwendung)

    @provider
    def provide_zeiteintrag_window(self, view_model: ZeiteintragViewModel) -> ZeiteintragWindow:
        return ZeiteintragWindow(view_model)
