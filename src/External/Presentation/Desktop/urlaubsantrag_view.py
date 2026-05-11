from __future__ import annotations

from datetime import date, datetime

from pydantic import ValidationError
from PySide6.QtCore import QDate, QLocale, Qt
from PySide6.QtGui import QFontMetrics, QKeySequence, QShortcut, QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QDateEdit,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QDoubleSpinBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from External.Presentation.Desktop.urlaubsantrag_table_model import UrlaubsantragRow
from External.Presentation.Desktop.urlaubsantrag_view_model import UrlaubsantragViewModel


class UrlaubsantragView(QWidget):
    def __init__(self, view_model: UrlaubsantragViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._view_model = view_model
        self._initial_load_done = False
        self._bearbeitungs_id: int | None = None
        self._suspend_selection_sync = False
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

        self._form_group = QGroupBox("Neuer Urlaubsantrag", self)
        self._form_group.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum
        )
        form_layout = QFormLayout(self._form_group)
        form_layout.setSpacing(4)
        form_layout.setContentsMargins(8, 10, 8, 8)

        locale_de = QLocale(QLocale.Language.German, QLocale.Country.Germany)
        heute_q = QDate(date.today().year, date.today().month, date.today().day)

        self._datum_von_input = QDateEdit(self._form_group)
        self._datum_von_input.setCalendarPopup(True)
        self._datum_von_input.setDisplayFormat("dd.MM.yyyy")
        self._datum_von_input.setLocale(locale_de)
        self._datum_von_input.setDate(heute_q)

        self._datum_bis_input = QDateEdit(self._form_group)
        self._datum_bis_input.setCalendarPopup(True)
        self._datum_bis_input.setDisplayFormat("dd.MM.yyyy")
        self._datum_bis_input.setLocale(locale_de)
        self._datum_bis_input.setDate(heute_q)

        for de in (self._datum_von_input, self._datum_bis_input):
            de.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            de.setFixedWidth(de.sizeHint().width())

        datum_zeile = QWidget(self._form_group)
        datum_layout = QHBoxLayout(datum_zeile)
        datum_layout.setContentsMargins(0, 0, 0, 0)
        datum_layout.setSpacing(6)
        datum_layout.addWidget(QLabel("von", datum_zeile))
        datum_layout.addWidget(self._datum_von_input)
        datum_layout.addWidget(QLabel("bis", datum_zeile))
        datum_layout.addWidget(self._datum_bis_input)
        datum_layout.addStretch()

        self._urlaubstyp_input = QLineEdit(self._form_group)
        self._urlaubstyp_input.setText("Jahresurlaub")
        self._urlaubstyp_input.setPlaceholderText("z. B. Erholungsurlaub")
        self._urlaubstyp_input.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._urlaubstage_spin = QDoubleSpinBox(self._form_group)
        self._urlaubstage_spin.setRange(0.0, 366.0)
        self._urlaubstage_spin.setDecimals(1)
        self._urlaubstage_spin.setSingleStep(0.5)
        self._urlaubstage_spin.setLocale(locale_de)
        self._urlaubstage_spin.setValue(1.0)
        self._urlaubstage_spin.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        fm_stage = QFontMetrics(self._urlaubstage_spin.font())
        self._urlaubstage_spin.setFixedWidth(
            fm_stage.horizontalAdvance("366,0") + 36
        )

        self._genehmigt_check = QCheckBox("Genehmigt", self._form_group)

        stage_genehmigt_zeile = QWidget(self._form_group)
        stage_genehmigt_layout = QHBoxLayout(stage_genehmigt_zeile)
        stage_genehmigt_layout.setContentsMargins(0, 0, 0, 0)
        stage_genehmigt_layout.setSpacing(12)
        stage_genehmigt_layout.addWidget(self._urlaubstage_spin)
        stage_genehmigt_layout.addWidget(self._genehmigt_check)
        stage_genehmigt_layout.addStretch()

        form_layout.addRow("Zeitraum:", datum_zeile)
        form_layout.addRow("Urlaubstyp:", self._urlaubstyp_input)
        form_layout.addRow("Urlaubstage:", stage_genehmigt_zeile)

        self._speichern_button = QPushButton("Antrag speichern", self)
        self._speichern_button.setSizePolicy(
            QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed
        )

        self._neuer_antrag_button = QPushButton("Neuer Antrag", self)
        self._neuer_antrag_button.setToolTip(
            "Eingabe zuruecksetzen fuer einen neuen Urlaubsantrag."
        )

        aktions_spalte = QVBoxLayout()
        aktions_spalte.setSpacing(6)
        aktions_spalte.setContentsMargins(0, 0, 0, 0)
        aktions_spalte.addWidget(self._speichern_button)
        aktions_spalte.addWidget(self._neuer_antrag_button)

        aktions_wrap = QWidget(self)
        aktions_wrap.setLayout(aktions_spalte)
        aktions_wrap.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Maximum)

        formular_zeile = QHBoxLayout()
        formular_zeile.setContentsMargins(0, 0, 0, 0)
        formular_zeile.addWidget(
            self._form_group,
            stretch=1,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        formular_zeile.addWidget(
            aktions_wrap,
            stretch=0,
            alignment=Qt.AlignmentFlag.AlignTop,
        )
        formular_zeile.addStretch(1)

        self._table = QTableView(self)
        self._table.setModel(self._view_model.table_model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setStyleSheet(
            "QTableView::item:selected {"
            "background-color: #fff9c4;"
            "color: #000000;"
            "}"
            "QTableView::item:selected:active {"
            "color: #000000;"
            "}"
            "QTableView::item:selected:!active {"
            "background-color: #fff9c4;"
            "color: #000000;"
            "}"
        )
        header = self._table.horizontalHeader()
        header.resizeSection(0, 95)
        header.resizeSection(1, 95)
        header.resizeSection(2, 120)
        header.resizeSection(3, 50)
        header.setStretchLastSection(True)

        loeschen_layout = QHBoxLayout()
        self._loeschen_button = QPushButton("Markierten Antrag loeschen", self)
        self._loeschen_button.setToolTip(
            "Loeschen der markierten Tabellenzeile (Taste Entf)."
        )
        loeschen_layout.addWidget(self._loeschen_button)
        loeschen_layout.addStretch()

        self._status_label = QLabel("Bereit.", self)

        root_layout.setSpacing(6)
        root_layout.setContentsMargins(8, 8, 8, 8)

        root_layout.addLayout(toolbar_layout)
        root_layout.addLayout(formular_zeile)
        root_layout.addWidget(self._table)
        root_layout.addLayout(loeschen_layout)
        root_layout.addWidget(self._status_label)

        loeschen_shortcut = QShortcut(QKeySequence.StandardKey.Delete, self._table)
        loeschen_shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        loeschen_shortcut.activated.connect(self._on_loeschen)

        self._laden_button.clicked.connect(self._lade_auswahl_jahr)
        self._jahr_spin.valueChanged.connect(self._on_jahr_changed)
        self._speichern_button.clicked.connect(self._on_speichern)
        self._neuer_antrag_button.clicked.connect(self._on_neuer_antrag)
        self._loeschen_button.clicked.connect(self._on_loeschen)

        selection_model = self._table.selectionModel()
        if selection_model is not None:
            selection_model.selectionChanged.connect(self._on_tabellen_auswahl_geaendert)

    def _bind_view_model(self) -> None:
        self._view_model.status_changed.connect(self._status_label.setText)
        self._view_model.error_occurred.connect(self._show_error)

    def _aktualisiere_formular_titel(self) -> None:
        if self._bearbeitungs_id is not None:
            self._form_group.setTitle("Urlaubsantrag editieren")
            self._form_group.setStyleSheet(
                "QGroupBox {"
                "border: 1px dashed #757575;"
                "border-radius: 5px;"
                "margin-top: 14px;"
                "padding-top: 14px;"
                "}"
                "QGroupBox::title {"
                "subcontrol-origin: margin;"
                "subcontrol-position: top left;"
                "left: 12px;"
                "padding: 0 5px;"
                "}"
            )
        else:
            self._form_group.setTitle("Neuer Urlaubsantrag")
            self._form_group.setStyleSheet("")

    def _reset_formular_defaults(self) -> None:
        heute_q = QDate(date.today().year, date.today().month, date.today().day)
        self._datum_von_input.setDate(heute_q)
        self._datum_bis_input.setDate(heute_q)
        self._urlaubstyp_input.setText("Jahresurlaub")
        self._urlaubstage_spin.setValue(1.0)
        self._genehmigt_check.setChecked(False)

    def _zeile_ins_formular(self, row: UrlaubsantragRow) -> None:
        dv = datetime.strptime(row.datum_von, "%d.%m.%Y").date()
        db = datetime.strptime(row.datum_bis, "%d.%m.%Y").date()
        self._datum_von_input.setDate(QDate(dv.year, dv.month, dv.day))
        self._datum_bis_input.setDate(QDate(db.year, db.month, db.day))
        self._urlaubstyp_input.setText(row.urlaubstyp)
        stage_txt = row.urlaubstage.strip().replace(",", ".")
        self._urlaubstage_spin.setValue(float(stage_txt))
        self._genehmigt_check.setChecked(row.genehmigt.strip().lower() == "ja")

    def _on_neuer_antrag(self) -> None:
        self._suspend_selection_sync = True
        try:
            self._table.clearSelection()
        finally:
            self._suspend_selection_sync = False
        self._bearbeitungs_id = None
        self._reset_formular_defaults()
        self._aktualisiere_formular_titel()

    def _on_tabellen_auswahl_geaendert(self, *_args) -> None:
        if self._suspend_selection_sync:
            return
        selection_model = self._table.selectionModel()
        if selection_model is None:
            return
        selected_rows = selection_model.selectedRows()
        if not selected_rows:
            return
        row_index = selected_rows[0].row()
        rows = self._view_model.table_model.rows
        if row_index < 0 or row_index >= len(rows):
            return
        row = rows[row_index]
        self._bearbeitungs_id = row.id
        self._zeile_ins_formular(row)
        self._aktualisiere_formular_titel()

    def _lade_auswahl_jahr(self) -> None:
        self._suspend_selection_sync = True
        try:
            self._view_model.lade_fuer_jahr(self._jahr_spin.value())
        finally:
            self._suspend_selection_sync = False
        self._bearbeitungs_id = None
        self._reset_formular_defaults()
        self._aktualisiere_formular_titel()

    def _on_jahr_changed(self, _value: int) -> None:
        self._lade_auswahl_jahr()

    def _on_speichern(self) -> None:
        try:
            self._view_model.speichere_antrag(
                datum_von_text=self._datum_von_input.date().toString("dd.MM.yyyy"),
                datum_bis_text=self._datum_bis_input.date().toString("dd.MM.yyyy"),
                urlaubstyp=self._urlaubstyp_input.text(),
                urlaubstage_text=str(self._urlaubstage_spin.value()),
                genehmigt=self._genehmigt_check.isChecked(),
                antrag_id=self._bearbeitungs_id,
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
            self._show_error("Bitte zuerst eine Zeile in der Tabelle markieren.")
            return
        row_index = selected_rows[0].row()
        table_model = self._view_model.table_model
        if row_index < 0 or row_index >= len(table_model.rows):
            self._show_error("Ungueltige Zeilenauswahl.")
            return
        row = table_model.rows[row_index]
        if row.id is None:
            self._show_error(
                "Dieser Eintrag kann nicht geloescht werden (fehlende Datensatz-Id)."
            )
            return
        antwort = QMessageBox.question(
            self,
            "Urlaubsantrag loeschen",
            f"Urlaubsantrag vom {row.datum_von} bis {row.datum_bis} endgueltig loeschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if antwort != QMessageBox.StandardButton.Yes:
            return
        try:
            if self._view_model.loesche_nach_id(row.id):
                self._lade_auswahl_jahr()
        except Exception as exc:  # noqa: BLE001
            self._show_error(str(exc))

    def _show_error(self, message: str) -> None:
        QMessageBox.warning(self, "Urlaubsantrag", message)
