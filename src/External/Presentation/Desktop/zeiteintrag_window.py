from __future__ import annotations

from datetime import date
from uuid import UUID

from PySide6.QtGui import QCloseEvent, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QComboBox,
    QLineEdit,
    QStyledItemDelegate,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel


class LiveCommitDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):  # noqa: N802
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            editor.editingFinished.connect(lambda e=editor: self._commit_live(e))
        return editor

    def paint(self, painter, option, index):  # noqa: N802
        paint_option = option
        model = index.model()
        if hasattr(model, "is_row_dirty"):
            paint_option = type(option)(option)
            text_color = "#b71c1c" if model.is_row_dirty(index.row()) else "#000000"
            paint_option.palette.setColor(QPalette.Text, text_color)
            paint_option.palette.setColor(QPalette.HighlightedText, text_color)
        super().paint(painter, paint_option, index)

    def _commit_live(self, editor: QLineEdit) -> None:
        editor.setProperty("_live_commit", True)
        self.commitData.emit(editor)
        editor.setProperty("_live_commit", False)

    def setModelData(self, editor, model, index):  # noqa: N802
        if isinstance(editor, QLineEdit):
            text = editor.text()
            if index.column() != 6:
                text = text.strip()
            is_live_commit = bool(editor.property("_live_commit"))
            if not is_live_commit and index.column() in (2, 3, 4, 5) and text.isdigit():
                hour = int(text)
                if 0 <= hour <= 23:
                    text = f"{hour:02d}:00"
            model.setData(index, text)
            return
        super().setModelData(editor, model, index)


class ZeiteintragWindow(QMainWindow):
    def __init__(self, view_model: ZeiteintragViewModel) -> None:
        super().__init__()
        self._view_model = view_model
        self._has_unsaved_changes = False
        self._current_loaded_year: int | None = None
        self._current_loaded_month: int | None = None
        self._ignore_period_change = False
        self._suspend_dirty_tracking = False
        self._baseline_rows: list[tuple[object, str, str, str, str, str, str]] = []
        self.setWindowTitle("Taetigkeitsbericht - Zeiteintrag Erfassung")
        self.resize(1100, 640)
        self._build_ui()
        self._bind_view_model()
        self._load_selected_period()

    def _build_ui(self) -> None:
        central_widget = QWidget(self)
        root_layout = QVBoxLayout(central_widget)
        toolbar_layout = QHBoxLayout()

        self._jahr_spin = QSpinBox(self)
        self._jahr_spin.setRange(2000, 2100)
        self._jahr_spin.setValue(date.today().year)
        self._jahr_spin.setPrefix("Jahr: ")
        self._monat_combo = QComboBox(self)
        for monat in range(1, 13):
            self._monat_combo.addItem(f"{monat:02d}", monat)
        self._monat_combo.setCurrentIndex(date.today().month - 1)

        self._laden_button = QPushButton("Laden", self)
        self._zeile_hinzufuegen_button = QPushButton("Zeile hinzufuegen", self)
        self._zeile_loeschen_button = QPushButton("Markierte Zeile(n) loeschen", self)
        self._speichern_button = QPushButton("Alle Zeilen speichern", self)
        self._status_label = QLabel("Bereit.", self)

        toolbar_layout.addWidget(self._jahr_spin)
        toolbar_layout.addWidget(self._monat_combo)
        toolbar_layout.addWidget(self._laden_button)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self._zeile_hinzufuegen_button)
        toolbar_layout.addWidget(self._zeile_loeschen_button)
        toolbar_layout.addWidget(self._speichern_button)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setItemDelegate(LiveCommitDelegate(self._table))
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setStyleSheet(
            "QTableView::item:selected {"
            "background-color: #fff9c4;"
            "}"
        )
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
        self._table.doubleClicked.connect(self._on_table_double_clicked)
        self._jahr_spin.valueChanged.connect(self._on_period_changed)
        self._monat_combo.currentIndexChanged.connect(self._on_period_changed)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)
        model = self._view_model.table_model
        model.dataChanged.connect(self._on_model_mutated)
        model.rowsInserted.connect(self._on_model_mutated)
        model.rowsRemoved.connect(self._on_model_mutated)
        model.modelReset.connect(self._on_model_mutated)

    def _on_laden(self) -> None:
        self._load_selected_period()

    def _on_period_changed(self, *_args) -> None:
        if self._ignore_period_change:
            return
        self._load_selected_period()

    def _selected_period(self) -> tuple[int, int]:
        monat = self._monat_combo.currentData()
        if monat is None:
            monat = date.today().month
        return self._jahr_spin.value(), int(monat)

    def _set_period(self, jahr: int, monat: int) -> None:
        self._ignore_period_change = True
        try:
            self._jahr_spin.setValue(jahr)
            self._monat_combo.setCurrentIndex(monat - 1)
        finally:
            self._ignore_period_change = False

    def _confirm_discard_unsaved_changes(self) -> bool:
        return (
            QMessageBox.question(
                self,
                "Ungespeicherte Aenderungen",
                "Es gibt ungespeicherte Zeilen. Beim Wechsel von Jahr/Monat gehen diese verloren. Trotzdem wechseln?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def _confirm_close_with_unsaved_changes(self) -> bool:
        return (
            QMessageBox.question(
                self,
                "Ungespeicherte Aenderungen",
                "Es gibt ungespeicherte Zeilen. Beim Schliessen gehen diese verloren. Trotzdem schliessen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            == QMessageBox.Yes
        )

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._has_unsaved_changes and not self._confirm_close_with_unsaved_changes():
            event.ignore()
            return
        event.accept()

    def _load_selected_period(self) -> None:
        selected_year, selected_month = self._selected_period()
        period_changed = (
            self._current_loaded_year != selected_year or self._current_loaded_month != selected_month
        )

        if not period_changed and self._current_loaded_year is not None:
            return

        if self._has_unsaved_changes and period_changed:
            if not self._confirm_discard_unsaved_changes():
                if self._current_loaded_year is not None and self._current_loaded_month is not None:
                    self._set_period(self._current_loaded_year, self._current_loaded_month)
                return

        self._suspend_dirty_tracking = True
        try:
            self._view_model.lade_zeitraum(selected_year, selected_month)
        finally:
            self._suspend_dirty_tracking = False

        self._current_loaded_year = selected_year
        self._current_loaded_month = selected_month
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())

    def _on_zeile_hinzufuegen(self) -> None:
        selection_model = self._table.selectionModel()
        position: int | None = None
        datum = ""
        if selection_model is not None:
            selected_rows = [index.row() for index in selection_model.selectedRows()]
            if not selected_rows:
                current_index = selection_model.currentIndex()
                if current_index.isValid():
                    selected_rows = [current_index.row()]
            if selected_rows:
                anchor_row = max(selected_rows)
                position = anchor_row + 1
                model_rows = self._view_model.table_model.rows
                if 0 <= anchor_row < len(model_rows):
                    datum = model_rows[anchor_row].datum

        new_row_index = self._view_model.add_row(position=position, datum=datum)

        if selection_model is not None:
            new_index = self._view_model.table_model.index(new_row_index, 0)
            selection_model.clearSelection()
            self._table.setCurrentIndex(new_index)
            self._table.scrollTo(new_index)

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
        if self._view_model.speichere_alle():
            self._capture_baseline()
            self._has_unsaved_changes = False
            self._view_model.table_model.set_dirty_rows(set())

    def _on_table_double_clicked(self, index) -> None:
        if index.column() != 0:
            return
        vorhandener_wert = self._view_model.table_model.data(index)
        if isinstance(vorhandener_wert, str) and vorhandener_wert.strip():
            return
        datum_heute = date.today().strftime("%d.%m.%Y")
        self._view_model.table_model.setData(index, datum_heute)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Fehler beim Speichern/Laden", message)

    def _on_model_mutated(self, *_args) -> None:
        if self._suspend_dirty_tracking:
            return
        self._update_dirty_state()

    def _capture_baseline(self) -> None:
        self._baseline_rows = self._current_rows_snapshot()

    def _current_rows_snapshot(self) -> list[tuple[object, str, str, str, str, str, str]]:
        snapshot: list[tuple[object, str, str, str, str, str, str]] = []
        for row in self._view_model.table_model.rows:
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            unterbrechung_beginn = row.unterbrechung_beginn.strip()
            unterbrechung_ende = row.unterbrechung_ende.strip()
            anmerkung = row.anmerkung.strip()
            if not self._is_row_relevant_for_unsaved(uhrzeit_von, uhrzeit_bis):
                continue
            snapshot.append(
                (
                    row.id,
                    datum,
                    uhrzeit_von,
                    uhrzeit_bis,
                    unterbrechung_beginn,
                    unterbrechung_ende,
                    anmerkung,
                )
            )
        return snapshot

    def _update_dirty_state(self) -> None:
        self._has_unsaved_changes = self._current_rows_snapshot() != self._baseline_rows
        self._view_model.table_model.set_dirty_rows(self._compute_dirty_row_indices())

    def _compute_dirty_row_indices(self) -> set[int]:
        baseline_by_id: dict[UUID, tuple[str, str, str, str, str, str]] = {
            row_id: (datum, uhrzeit_von, uhrzeit_bis, unterbrechung_beginn, unterbrechung_ende, anmerkung)
            for row_id, datum, uhrzeit_von, uhrzeit_bis, unterbrechung_beginn, unterbrechung_ende, anmerkung in self._baseline_rows
            if isinstance(row_id, UUID)
        }
        dirty_rows: set[int] = set()
        for index, row in enumerate(self._view_model.table_model.rows):
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            unterbrechung_beginn = row.unterbrechung_beginn.strip()
            unterbrechung_ende = row.unterbrechung_ende.strip()
            anmerkung = row.anmerkung.strip()

            if not self._is_row_relevant_for_unsaved(uhrzeit_von, uhrzeit_bis):
                continue

            if row.id is None:
                dirty_rows.add(index)
                continue

            baseline_values = baseline_by_id.get(row.id)
            current_values = (
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                unterbrechung_beginn,
                unterbrechung_ende,
                anmerkung,
            )
            if baseline_values != current_values:
                dirty_rows.add(index)

        return dirty_rows

    @staticmethod
    def _is_row_relevant_for_unsaved(uhrzeit_von: str, uhrzeit_bis: str) -> bool:
        return bool(uhrzeit_von)
