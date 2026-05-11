from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from PySide6.QtCore import QPersistentModelIndex, QRect, Qt
from PySide6.QtGui import QCloseEvent, QColor, QGuiApplication, QIcon, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTableView,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.feiertag_view import FeiertagView
from External.Presentation.Desktop.stundenplan_view import StundenplanView
from External.Presentation.Desktop.zeiteintrag_table_model import ZeiteintragTableModel
from External.Presentation.Desktop.zeiteintrag_view_model import ZeiteintragViewModel


class LiveCommitDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):  # noqa: N802
        editor = super().createEditor(parent, option, index)
        if isinstance(editor, QLineEdit):
            persistent = QPersistentModelIndex(index)

            def on_editing_finished() -> None:
                if not persistent.isValid():
                    return
                model = persistent.model()
                if model is None:
                    return
                idx = model.index(
                    persistent.row(),
                    persistent.column(),
                    persistent.parent(),
                )
                if not idx.isValid():
                    return
                editor.setProperty("_live_commit", True)
                self.setModelData(editor, model, idx)
                editor.setProperty("_live_commit", False)

            editor.editingFinished.connect(on_editing_finished)
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

    def setModelData(self, editor, model, index):  # noqa: N802
        if isinstance(editor, QLineEdit):
            text = editor.text()
            if index.column() != 10:
                text = text.strip()
            is_live_commit = bool(editor.property("_live_commit"))
            if not is_live_commit and index.column() in (2, 3, 4, 5, 6, 7) and text.isdigit():
                hour = int(text)
                if 0 <= hour <= 23:
                    text = f"{hour:02d}:00"
            model.setData(index, text)
            return
        super().setModelData(editor, model, index)


class WochentagMitSternDelegate(LiveCommitDelegate):
    """Wochentagskürzel links, Feiertags-Stern-Icon rechts in Spalte 0."""

    def paint(self, painter, option, index):  # noqa: N802
        if index.column() != 0:
            super().paint(painter, option, index)
            return

        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)

        model = index.model()
        if model is not None and hasattr(model, "is_row_dirty") and model.is_row_dirty(index.row()):
            opt.palette.setColor(QPalette.ColorRole.Text, QColor("#b71c1c"))
            opt.palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#b71c1c"))

        widget = option.widget
        style = widget.style() if widget is not None else None

        painter.save()
        painter.setClipRect(option.rect)

        if style is not None:
            style.drawPrimitive(
                QStyle.PrimitiveElement.PE_PanelItemViewItem,
                opt,
                painter,
                widget,
            )

        text = index.data(Qt.ItemDataRole.DisplayRole)
        text = "" if text is None else str(text)
        icon = index.data(Qt.ItemDataRole.DecorationRole)

        rand = 4
        if isinstance(icon, QIcon) and not icon.isNull():
            icon_breite = 14
            icon_rect = QRect(
                option.rect.right() - rand - icon_breite,
                option.rect.center().y() - icon_breite // 2,
                icon_breite,
                icon_breite,
            )
            text_rect = QRect(
                option.rect.left() + rand,
                option.rect.top(),
                icon_rect.left() - option.rect.left() - rand - 2,
                option.rect.height(),
            )
        else:
            text_rect = option.rect.adjusted(rand, 0, -rand, 0)
            icon_rect = None

        painter.setFont(option.font)
        painter.setPen(opt.palette.color(QPalette.ColorRole.Text))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            text,
        )
        if icon_rect is not None:
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)
        painter.restore()


class ZeiteintragWindow(QMainWindow):
    def __init__(
        self,
        view_model: ZeiteintragViewModel,
        stundenplan_view: StundenplanView,
        feiertag_view: FeiertagView,
    ) -> None:
        super().__init__()
        self._view_model = view_model
        self._stundenplan_view = stundenplan_view
        self._feiertag_view = feiertag_view
        self._has_unsaved_changes = False
        self._current_loaded_year: int | None = None
        self._current_loaded_month: int | None = None
        self._ignore_period_change = False
        self._suspend_dirty_tracking = False
        self._baseline_rows: list[tuple[object, str, str, str, str, str, str, str, str]] = []
        self.setWindowTitle("Taetigkeitsbericht - Erfassung")
        self.resize(1100, 640)
        self._build_ui()
        self._bind_view_model()
        self._load_selected_period()

    def _build_ui(self) -> None:
        zeiteintrag_widget = QWidget(self)
        root_layout = QVBoxLayout(zeiteintrag_widget)
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
        self._summen_label = QLabel("", self)

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
        self._table.setItemDelegateForColumn(0, WochentagMitSternDelegate(self._table))
        self._table.setAlternatingRowColors(True)
        self._table.setShowGrid(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setStyleSheet(
            "QTableView::item:selected {"
            "background-color: #fff9c4;"
            "}"
        )
        horizontal_header = self._table.horizontalHeader()
        horizontal_header.setStretchLastSection(True)
        horizontal_header.resizeSection(0, 50)
        horizontal_header.resizeSection(4, 62)
        horizontal_header.resizeSection(5, 62)
        horizontal_header.resizeSection(6, 62)
        horizontal_header.resizeSection(7, 62)
        horizontal_header.resizeSection(8, 80)
        horizontal_header.resizeSection(9, 72)
        self._table.verticalHeader().setVisible(True)

        root_layout.addLayout(toolbar_layout)
        root_layout.addWidget(self._table)
        fuss_layout = QHBoxLayout()
        fuss_layout.addWidget(self._status_label, 1)
        fuss_layout.addWidget(self._summen_label)
        root_layout.addLayout(fuss_layout)

        self._tab_widget = QTabWidget(self)
        self._tab_widget.addTab(zeiteintrag_widget, "Zeiteintraege")
        self._tab_widget.addTab(self._stundenplan_view, "Stundenplan")
        self._tab_widget.addTab(self._feiertag_view, "Feiertage")
        self.setCentralWidget(self._tab_widget)

        self._laden_button.clicked.connect(self._on_laden)
        self._zeile_hinzufuegen_button.clicked.connect(self._on_zeile_hinzufuegen)
        self._zeile_loeschen_button.clicked.connect(self._on_zeile_loeschen)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._table.doubleClicked.connect(self._on_table_double_clicked)
        self._jahr_spin.valueChanged.connect(self._on_period_changed)
        self._monat_combo.currentIndexChanged.connect(self._on_period_changed)

        copy_shortcut = QShortcut(QKeySequence.Copy, self._table)
        copy_shortcut.setContext(Qt.WidgetWithChildrenShortcut)
        copy_shortcut.activated.connect(self._kopiere_markierte_zellen_in_zwischenablage)
        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_selection_changed)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)
        model = self._view_model.table_model
        model.dataChanged.connect(self._on_model_mutated)
        model.rowsInserted.connect(self._on_model_mutated)
        model.rowsRemoved.connect(self._on_model_mutated)
        model.modelReset.connect(self._on_model_mutated)
        self._aktualisiere_summen_anzeige()

    def _aktualisiere_summen_anzeige(self) -> None:
        model = self._view_model.table_model
        g_min, s_min = model.summen_geleistet_und_soll_minuten()
        g_txt = ZeiteintragTableModel.minuten_als_hh_mm(g_min)
        s_txt = ZeiteintragTableModel.minuten_als_hh_mm(s_min)
        self._summen_label.setText(f"Geleistet: {g_txt}   Soll: {s_txt}")

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
        gibt_offene_aenderungen = (
            self._has_unsaved_changes or self._stundenplan_view.has_unsaved_changes
        )
        if gibt_offene_aenderungen and not self._confirm_close_with_unsaved_changes():
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
            new_index = self._view_model.table_model.index(new_row_index, 1)
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
        if not self._view_model.speichere_alle():
            return
        self._capture_baseline()
        self._has_unsaved_changes = False
        self._view_model.table_model.set_dirty_rows(set())
        self._reload_current_period()

    def _reload_current_period(self) -> None:
        selected_year, selected_month = self._selected_period()
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

    def _on_selection_changed(self, *_args) -> None:
        self._kopiere_markierte_zellen_in_zwischenablage(silent=True)

    def _kopiere_markierte_zellen_in_zwischenablage(self, silent: bool = False) -> None:
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        indexes = [index for index in selection_model.selectedIndexes() if index.isValid()]
        if not indexes:
            return

        indexes.sort(key=lambda idx: (idx.row(), idx.column()))
        model = self._view_model.table_model
        zeilen_texte: list[str] = []
        current_row = indexes[0].row()
        current_cells: list[str] = []
        for idx in indexes:
            if idx.row() != current_row:
                zeilen_texte.append("\t".join(current_cells))
                current_cells = []
                current_row = idx.row()
            wert = model.data(idx, Qt.DisplayRole)
            current_cells.append("" if wert is None else str(wert))
        zeilen_texte.append("\t".join(current_cells))

        text = "\n".join(zeilen_texte)
        clipboard = QGuiApplication.clipboard()
        if clipboard is None:
            return
        clipboard.setText(text)

        if not silent:
            zeilen_anzahl = len(zeilen_texte)
            self._status_label.setText(
                f"{zeilen_anzahl} Zeile(n) in die Zwischenablage kopiert."
            )

    def _on_table_double_clicked(self, index) -> None:
        if index.column() != 1:
            return
        model = self._view_model.table_model
        row_idx = index.row()
        row = model.rows[row_idx]
        datum_text = row.datum.strip()
        if not datum_text:
            datum_text = date.today().strftime("%d.%m.%Y")
            model.setData(index, datum_text)

        if row.uhrzeit_von.strip() or row.uhrzeit_bis.strip():
            return

        try:
            datum = datetime.strptime(datum_text, "%d.%m.%Y").date()
        except ValueError:
            return

        if model.ist_feiertag(datum_text):
            return

        passende_stundenplan_zeilen = self._stundenplan_view.zeilen_fuer_wochentag(
            datum.isoweekday()
        )
        if not passende_stundenplan_zeilen:
            return

        zeiteintrag_zeilen_am_tag = [
            idx
            for idx, zeile in enumerate(model.rows)
            if zeile.datum.strip() == datum_text
        ]
        if row_idx not in zeiteintrag_zeilen_am_tag:
            return

        eintrags_index = zeiteintrag_zeilen_am_tag.index(row_idx)
        if eintrags_index >= len(passende_stundenplan_zeilen):
            return
        stundenplan_zeile = passende_stundenplan_zeilen[eintrags_index]

        feld_zu_spalte = {
            "uhrzeit_von": 2,
            "uhrzeit_bis": 3,
            "pause_beginn": 4,
            "pause_ende": 5,
            "pause2_beginn": 6,
            "pause2_ende": 7,
            "anmerkung": 10,
        }
        for feldname, spalte in feld_zu_spalte.items():
            zielwert = getattr(row, feldname).strip()
            if zielwert:
                continue
            quellwert = getattr(stundenplan_zeile, feldname).strip()
            if not quellwert:
                continue
            model.setData(model.index(row_idx, spalte), quellwert)

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Fehler beim Speichern/Laden", message)

    def _on_model_mutated(self, *_args) -> None:
        self._aktualisiere_summen_anzeige()
        if self._suspend_dirty_tracking:
            return
        self._update_dirty_state()

    def _capture_baseline(self) -> None:
        self._baseline_rows = self._current_rows_snapshot()

    def _current_rows_snapshot(self) -> list[tuple[object, str, str, str, str, str, str, str, str]]:
        snapshot: list[tuple[object, str, str, str, str, str, str, str, str]] = []
        for row in self._view_model.table_model.rows:
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            pause_beginn = row.pause_beginn.strip()
            pause_ende = row.pause_ende.strip()
            pause2_beginn = row.pause2_beginn.strip()
            pause2_ende = row.pause2_ende.strip()
            anmerkung = row.anmerkung.strip()
            if not self._is_row_relevant_for_unsaved(uhrzeit_von, uhrzeit_bis):
                continue
            snapshot.append(
                (
                    row.id,
                    datum,
                    uhrzeit_von,
                    uhrzeit_bis,
                    pause_beginn,
                    pause_ende,
                    pause2_beginn,
                    pause2_ende,
                    anmerkung,
                )
            )
        return snapshot

    def _update_dirty_state(self) -> None:
        self._has_unsaved_changes = self._current_rows_snapshot() != self._baseline_rows
        self._view_model.table_model.set_dirty_rows(self._compute_dirty_row_indices())

    def _compute_dirty_row_indices(self) -> set[int]:
        baseline_by_id: dict[UUID, tuple[str, str, str, str, str, str, str, str]] = {
            row_id: (
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            )
            for (
                row_id,
                datum,
                uhrzeit_von,
                uhrzeit_bis,
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            ) in self._baseline_rows
            if isinstance(row_id, UUID)
        }
        dirty_rows: set[int] = set()
        for index, row in enumerate(self._view_model.table_model.rows):
            datum = row.datum.strip()
            uhrzeit_von = row.uhrzeit_von.strip()
            uhrzeit_bis = row.uhrzeit_bis.strip()
            pause_beginn = row.pause_beginn.strip()
            pause_ende = row.pause_ende.strip()
            pause2_beginn = row.pause2_beginn.strip()
            pause2_ende = row.pause2_ende.strip()
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
                pause_beginn,
                pause_ende,
                pause2_beginn,
                pause2_ende,
                anmerkung,
            )
            if baseline_values != current_values:
                dirty_rows.add(index)

        return dirty_rows

    @staticmethod
    def _is_row_relevant_for_unsaved(uhrzeit_von: str, uhrzeit_bis: str) -> bool:
        return bool(uhrzeit_von)
