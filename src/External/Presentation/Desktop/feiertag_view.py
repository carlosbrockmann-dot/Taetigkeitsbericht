from __future__ import annotations

from datetime import date

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.feiertag_view_model import FeiertagViewModel


class FeiertagView(QWidget):
    def __init__(self, view_model: FeiertagViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._build_ui()
        self._bind_view_model()

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802
        super().showEvent(event)
        if self._initial_load_done:
            return
        self._initial_load_done = True
        self._lade_auswahl_jahr()

    def _build_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        toolbar_layout = QHBoxLayout()
        add_layout = QHBoxLayout()

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._laden_button = QPushButton("Laden", self)
        self._import_button = QPushButton("Import starten", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addWidget(self._import_button)

        self._datum_input = QLineEdit(self)
        self._datum_input.setPlaceholderText("Datum (DD.MM.YYYY)")
        self._bezeichnung_input = QLineEdit(self)
        self._bezeichnung_input.setPlaceholderText("Bezeichnung freier Tag")
        self._hinzufuegen_button = QPushButton("Freien Tag hinzufuegen", self)
        self._loeschen_button = QPushButton("Markierten Tag loeschen", self)

        add_layout.addWidget(self._datum_input)
        add_layout.addWidget(self._bezeichnung_input)
        add_layout.addWidget(self._hinzufuegen_button)
        add_layout.addWidget(self._loeschen_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        header = self._table.horizontalHeader()
        header.setStretchLastSection(False)
        header.resizeSection(0, 95)
        header.resizeSection(1, 260)
        header.setStretchLastSection(True)
        self._table.verticalHeader().setVisible(True)

        self._status_label = QLabel("Bereit.", self)

        root_layout.addLayout(toolbar_layout)
        root_layout.addLayout(add_layout)
        root_layout.addWidget(self._table)
        root_layout.addWidget(self._status_label)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._import_button.clicked.connect(self._on_import_starten)
        self._hinzufuegen_button.clicked.connect(self._on_hinzufuegen)
        self._loeschen_button.clicked.connect(self._on_loeschen)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _lade_auswahl_jahr(self) -> None:
        self._view_model.lade_fuer_jahr(self._jahr_spin.value())

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_import_starten(self) -> None:
        try:
            self._view_model.lade_aus_api_und_speichere(jahr=self._jahr_spin.value())
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _on_hinzufuegen(self) -> None:
        try:
            self._view_model.fuege_freien_tag_hinzu(
                datum_text=self._datum_input.text(),
                bezeichnung=self._bezeichnung_input.text(),
            )
            self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _on_loeschen(self) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            self._show_error("Bitte zuerst eine Zeile markieren.")
            return
        row_index = selected_rows[0].row()
        row = self._view_model.table_model.rows[row_index]
        try:
            self._view_model.loesche_nach_datum(row.datum)
            self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Feiertag-Fehler", message)
