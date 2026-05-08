from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor


WOCHENTAG_LABELS: list[tuple[int, str]] = [
    (1, "Mo"),
    (2, "Di"),
    (3, "Mi"),
    (4, "Do"),
    (5, "Fr"),
    (6, "Sa"),
    (7, "So"),
]


@dataclass
class StundenplanRow:
    id: int | None = None
    wochentag: int = 1
    uhrzeit_von: str = ""
    uhrzeit_bis: str = ""
    unterbrechung_beginn: str = ""
    unterbrechung_ende: str = ""
    anmerkung: str = ""


class StundenplanTableModel(QAbstractTableModel):
    HEADERS = [
        "Wochentag",
        "Von",
        "Bis",
        "Pause Von",
        "Pause Bis",
        "Soll",
        "Kommentar",
    ]
    HEADER_TOOLTIPS = [
        "Wochentag (Mo-So)",
        "Erwartetes Format: HH:MM, z. B. 08:30",
        "Erwartetes Format: HH:MM, z. B. 17:00",
        "Optionales Format: HH:MM, z. B. 12:00",
        "Optionales Format: HH:MM, z. B. 12:30",
        "Zu leistende Zeit (Bis - Von - Pause), Format HH:MM",
        "Freitext (max. 80 Zeichen)",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[StundenplanRow] = []
        self._dirty_rows: set[int] = set()

    @property
    def rows(self) -> list[StundenplanRow]:
        return self._rows

    def set_rows(self, rows: list[StundenplanRow]) -> None:
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
            return str(section + 1)
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | QColor | int | None:
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        if role == Qt.BackgroundRole:
            if row.wochentag in (6, 7):
                return QColor("#eeeeee")
            return QColor("#ffffff")
        if role == Qt.ForegroundRole:
            if index.row() in self._dirty_rows:
                return QColor("#b71c1c")
            return QColor("#000000")
        if role == Qt.EditRole and index.column() == 0:
            return row.wochentag
        if role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        match index.column():
            case 0:
                return _label_for_wochentag(row.wochentag)
            case 1:
                return row.uhrzeit_von
            case 2:
                return row.uhrzeit_bis
            case 3:
                return row.unterbrechung_beginn
            case 4:
                return row.unterbrechung_ende
            case 5:
                return self._calculate_zuleistende_zeit(
                    row.uhrzeit_von,
                    row.uhrzeit_bis,
                    row.unterbrechung_beginn,
                    row.unterbrechung_ende,
                )
            case 6:
                return row.anmerkung
            case _:
                return None

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        if index.column() == 0:
            wochentag = self._coerce_wochentag(value)
            if wochentag is None:
                return False
            row.wochentag = wochentag
            left = self.index(index.row(), 0)
            right = self.index(index.row(), len(self.HEADERS) - 1)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            return True

        text = str(value)
        if index.column() != 6:
            text = text.strip()
        if index.column() == 1:
            row.uhrzeit_von = text
        elif index.column() == 2:
            row.uhrzeit_bis = text
        elif index.column() == 3:
            row.unterbrechung_beginn = text
        elif index.column() == 4:
            row.unterbrechung_ende = text
        elif index.column() == 5:
            return False
        elif index.column() == 6:
            row.anmerkung = text
        else:
            return False

        if index.column() in (1, 2, 3, 4):
            left = self.index(index.row(), index.column())
            right = self.index(index.row(), 5)
            self.dataChanged.emit(
                left, right, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole]
            )
            return True

        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole, Qt.BackgroundRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        if index.column() == 5:
            return Qt.ItemIsSelectable | Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def add_empty_row(self, position: int | None = None, wochentag: int = 1) -> int:
        if position is None or position < 0 or position > len(self._rows):
            position = len(self._rows)
        if not 1 <= wochentag <= 7:
            wochentag = 1
        self.beginInsertRows(QModelIndex(), position, position)
        self._rows.insert(position, StundenplanRow(wochentag=wochentag))
        self.endInsertRows()
        return position

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
    def _coerce_wochentag(value: object) -> int | None:
        if isinstance(value, int) and 1 <= value <= 7:
            return value
        if isinstance(value, str):
            text = value.strip()
            for wert, label in WOCHENTAG_LABELS:
                if text.lower() == label.lower():
                    return wert
            try:
                num = int(text)
            except ValueError:
                return None
            if 1 <= num <= 7:
                return num
        return None

    @staticmethod
    def _calculate_zuleistende_zeit(
        uhrzeit_von: str,
        uhrzeit_bis: str,
        pause_von: str,
        pause_bis: str,
    ) -> str:
        von_minuten = StundenplanTableModel._parse_minutes(uhrzeit_von)
        bis_minuten = StundenplanTableModel._parse_minutes(uhrzeit_bis)
        if von_minuten is None or bis_minuten is None:
            return ""
        delta = bis_minuten - von_minuten
        if delta <= 0:
            return ""
        pause_von_minuten = StundenplanTableModel._parse_minutes(pause_von)
        pause_bis_minuten = StundenplanTableModel._parse_minutes(pause_bis)
        if pause_von_minuten is not None and pause_bis_minuten is not None:
            pause_delta = pause_bis_minuten - pause_von_minuten
            if pause_delta > 0:
                delta -= pause_delta
        if delta <= 0:
            return ""
        stunden, minuten = divmod(delta, 60)
        return f"{stunden:02d}:{minuten:02d}"

    @staticmethod
    def _parse_minutes(text: str) -> int | None:
        cleaned = text.strip()
        if not cleaned:
            return None
        if ":" not in cleaned:
            return None
        teile = cleaned.split(":", 1)
        if len(teile) != 2:
            return None
        try:
            stunden = int(teile[0])
            minuten = int(teile[1])
        except ValueError:
            return None
        if stunden < 0 or not 0 <= minuten < 60:
            return None
        return stunden * 60 + minuten


def _label_for_wochentag(wochentag: int) -> str:
    for wert, label in WOCHENTAG_LABELS:
        if wert == wochentag:
            return label
    return ""
