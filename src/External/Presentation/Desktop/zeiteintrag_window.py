from __future__ import annotations

from datetime import date

from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel


class ZeiteintragWindow(QMainWindow):
    def __init__(self, view_model: ZeiteintragViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self.setWindowTitle("Taetigkeitsbericht - Zeiteintrag Erfassung")
        self.resize(1100, 640)
        self._build_ui()
        self._bind_view_model()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        toolbar_layout = QHBoxLayout()

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")

        self._laden_button = QPushButton("Laden", self)
        self._zeile_hinzufuegen_button = QPushButton("Zeile hinzufuegen", self)
        self._zeile_loeschen_button = QPushButton("Markierte Zeile(n) loeschen", self)
        self._speichern_button = QPushButton("Alle Zeilen speichern", self)
        self._status_label = QLabel("Bereit.", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._zeile_hinzufuegen_button)
        toolbar_layout.addWidget(self._zeile_loeschen_button)
        toolbar_layout.addWidget(self._speichern_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.verticalHeader().setVisible(True)

        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(self._table)
        root_layout.addWidget(self._status_label)
        self.setCentralWidget(central_widget)

        self._laden_button.clicked.connect(self._on_laden)
        self._zeile_hinzufuegen_button.clicked.connect(self._on_zeile_hinzufuegen)
        self._zeile_loeschen_button.clicked.connect(self._on_zeile_loeschen)
        self._speichern_button.clicked.connect(self._on_speichern)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _on_laden(self) -> None:
        self._view_model.lade_jahr(self._jahr_spin.value())

    def _on_zeile_hinzufuegen(self) -> None:
        self._view_model.add_row()

    def _on_zeile_loeschen(self) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        row_indices = [
            index.row()
            for index in selection_model.selectedRows()
            if selection_model.isRowSelected(index.row(), index.parent())
        ]
        if not row_indices:
            return
        self._view_model.remove_rows(row_indices)
        selection_model.clearSelection()

    def _on_speichern(self) -> None:
        self._view_model.speichere_alle()

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Fehler beim Speichern/Laden", message)
