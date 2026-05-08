from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


@dataclass
class ZeiteintragRow:
    id: UUID | None = None
    datum: str = ""
    uhrzeit_von: str = ""
    uhrzeit_bis: str = ""
    unterbrechung_beginn: str = ""
    unterbrechung_ende: str = ""
    anmerkung: str = ""


class ZeiteintragTableModel(QAbstractTableModel):
    HEADERS = [
        "Datum",
        "Wochentag",
        "Von",
        "Bis",
        "Pause Von",
        "Pause Bis",
        "Kommentar",
    ]
    HEADER_TOOLTIPS = [
        "Erwartetes Format: DD.MM.YYYY, z. B. 07.05.2026",
        "Wird automatisch aus dem Datum ermittelt",
        "Erwartetes Format: HH:MM, z. B. 08:30",
        "Erwartetes Format: HH:MM, z. B. 17:00",
        "Optionales Format: HH:MM, z. B. 12:00",
        "Optionales Format: HH:MM, z. B. 12:30",
        "Freitext (max. 80 Zeichen)",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[ZeiteintragRow] = []
        self._dirty_rows: set[int] = set()

    @property
    def rows(self) -> list[ZeiteintragRow]:
        return self._rows

    def set_rows(self, rows: list[ZeiteintragRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self._rows)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: N802
        if parent.isValid():
            return 0
        return len(self.HEADERS)

    def headerData(  # noqa: N802
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> str | None:
        if section < 0:
            return None

        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            if section >= len(self.HEADERS):
                return None
            return self.HEADERS[section]
        if orientation == Qt.Horizontal and role == Qt.ToolTipRole:
            if section >= len(self.HEADER_TOOLTIPS):
                return None
            return self.HEADER_TOOLTIPS[section]
        if orientation == Qt.Vertical and role == Qt.DisplayRole:
            if section >= len(self._rows):
                return None
            return self._day_of_month_from_date(self._rows[section].datum)
        if role != Qt.DisplayRole:
            return None
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | QColor | None:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.BackgroundRole:
            if self._is_weekend_date(row.datum):
                return QColor("#eeeeee")
            return None
        if role == Qt.ForegroundRole:
            if index.row() in self._dirty_rows:
                return QColor("#b71c1c")
            return QColor("#000000")
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        match index.column():
            case 0:
                return row.datum
            case 1:
                return self._weekday_from_date(row.datum)
            case 2:
                return row.uhrzeit_von
            case 3:
                return row.uhrzeit_bis
            case 4:
                return row.unterbrechung_beginn
            case 5:
                return row.unterbrechung_ende
            case 6:
                return row.anmerkung
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        text = str(value)
        if index.column() != 6:
            text = text.strip()
        if index.column() == 0:
            row.datum = text
        elif index.column() == 1:
            return False
        elif index.column() == 2:
            row.uhrzeit_von = text
        elif index.column() == 3:
            row.uhrzeit_bis = text
        elif index.column() == 4:
            row.unterbrechung_beginn = text
        elif index.column() == 5:
            row.unterbrechung_ende = text
        elif index.column() == 6:
            row.anmerkung = text
        else:
            return False

        if index.column() == 0:
            left = self.index(index.row(), 0)
            right = self.index(index.row(), len(self.HEADERS) - 1)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            self.headerDataChanged.emit(Qt.Vertical, index.row(), index.row())
            return True

        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 1:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def add_empty_row(self) -> None:
        position = len(self._rows)
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.append(ZeiteintragRow())
        self.endInsertRows()

    def remove_rows(self, row_indices: list[int]) -> None:
        for row_index in sorted(set(row_indices), reverse=True):
            if row_index < 0 or row_index >= len(self._rows):
                continue
            self.beginRemoveRows(QModelIndex(), row_index, row_index)
            del self._rows[row_index]
            self.endRemoveRows()

    def set_dirty_rows(self, dirty_rows: set[int]) -> None:
        if self._dirty_rows == dirty_rows:
            return
        self._dirty_rows = set(dirty_rows)
        if not self._rows:
            return
        top_left = self.index(0, 0)
        bottom_right = self.index(len(self._rows) - 1, len(self.HEADERS) - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.ForegroundRole])

    def is_row_dirty(self, row_index: int) -> bool:
        return row_index in self._dirty_rows

    @staticmethod
    def _weekday_from_date(datum_text: str) -> str:
        text = datum_text.strip()
        if not text:
            return ""
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return ""
        return ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][datum.weekday()]

    @staticmethod
    def _day_of_month_from_date(datum_text: str) -> str:
        text = datum_text.strip()
        if not text:
            return ""
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return ""
        return f"{datum.day:02d}"

    @staticmethod
    def _is_weekend_date(datum_text: str) -> bool:
        text = datum_text.strip()
        if not text:
            return False
        try:
            datum = datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            return False
        return datum.weekday() >= 5
