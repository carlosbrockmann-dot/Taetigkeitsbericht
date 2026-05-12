from __future__ import annotations

from datetime import date

from pydantic import ValidationError
from PySide6.QtCore import QDate, QLocale
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.krankmeldung_view_model import KrankmeldungViewModel
from External.Presentation.Desktop.table_view_styles import STANDARD_TABLE_VIEW_STYLESHEET


class KrankmeldungView(QWidget):
    def __init__(
        self, view_model: KrankmeldungViewModel, parent: QWidget | None = None
    ) -> None:
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

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._laden_button = QPushButton("Laden", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addStretch()

        form_group = QGroupBox("Neue Krankmeldung", self)
        form_layout = QFormLayout(form_group)

        locale_de = QLocale(QLocale.Language.German, QLocale.Country.Germany)
        heute_q = QDate(date.today().year, date.today().month, date.today().day)

        self._krank_von_input = QDateEdit(form_group)
        self._krank_von_input.setCalendarPopup(True)
        self._krank_von_input.setDisplayFormat("dd.MM.yyyy")
        self._krank_von_input.setLocale(locale_de)
        self._krank_von_input.setDate(heute_q)

        self._krank_bis_input = QDateEdit(form_group)
        self._krank_bis_input.setCalendarPopup(True)
        self._krank_bis_input.setDisplayFormat("dd.MM.yyyy")
        self._krank_bis_input.setLocale(locale_de)
        self._krank_bis_input.setDate(heute_q)

        for de in (self._krank_von_input, self._krank_bis_input):
            de.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            de.setFixedWidth(de.sizeHint().width())
        self._krankmeldungstage_spin = QSpinBox(form_group)
        self._krankmeldungstage_spin.setRange(0, 366)
        self._krankmeldungstage_spin.setValue(1)

        form_layout.addRow("Krank von:", self._krank_von_input)
        form_layout.addRow("Krank bis:", self._krank_bis_input)
        form_layout.addRow("Krankheitstage:", self._krankmeldungstage_spin)

        buttons_layout = QHBoxLayout()
        self._speichern_button = QPushButton("Krankmeldung speichern", self)
        self._loeschen_button = QPushButton("Markierte Zeile loeschen", self)
        buttons_layout.addWidget(self._speichern_button)
        buttons_layout.addWidget(self._loeschen_button)
        buttons_layout.addStretch()

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setStyleSheet(STANDARD_TABLE_VIEW_STYLESHEET)
        header = self._table.horizontalHeader()
        header.resizeSection(0, 95)
        header.resizeSection(1, 95)
        header.resizeSection(2, 72)
        header.setStretchLastSection(True)

        self._status_label = QLabel("Bereit.", self)

        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(form_group)
        root_layout.addLayout(buttons_layout)
        root_layout.addWidget(self._table)
        root_layout.addWidget(self._status_label)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._loeschen_button.clicked.connect(self._on_loeschen)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _lade_auswahl_jahr(self) -> None:
        self._view_model.lade_fuer_jahr(self._jahr_spin.value())

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_speichern(self) -> None:
        try:
            self._view_model.speichere_eintrag(
                krank_von_text=self._krank_von_input.date().toString("dd.MM.yyyy"),
                krank_bis_text=self._krank_bis_input.date().toString("dd.MM.yyyy"),
                krankmeldungstage_text=str(self._krankmeldungstage_spin.value()),
            )
            self._lade_auswahl_jahr()
        except (ValueError, ValidationError) as exc:
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
            self._view_model.loesche_nach_id(row.id)
            self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Krankmeldung", message)
