from __future__ import annotations

import sys
from pathlib import Path

# Erlaubt direkten Start dieser Datei ohne gesetztes PYTHONPATH.
SRC_ROOT = Path(__file__).resolve().parents[3]
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from PySide6.QtWidgets import QApplication

from Core.Application.zeiteintrag_anwendung import ZeiteintragAnwendung
from External.Infrastructure.dependency_injection import create_injector
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel
from External.Presentation.Desktop.zeiteintrag_window import ZeiteintragWindow


def main() -> int:
    app = QApplication(sys.argv)

    injector = create_injector()
    zeiteintrag_anwendung = injector.get(ZeiteintragAnwendung)

    view_model = ZeiteintragViewModel(zeiteintrag_anwendung)
    window = ZeiteintragWindow(view_model)
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
