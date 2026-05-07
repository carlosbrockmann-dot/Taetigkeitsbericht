from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass
class ZeiteintragRow:
    datum: str = ""
    uhrzeit_von: str = ""
    uhrzeit_bis: str = ""
    unterbrechung_beginn: str = ""
    unterbrechung_ende: str = ""
    anmerkung: str = ""


class ZeiteintragTableModel(QAbstractTableModel):
    HEADERS = [
        "Datum (YYYY-MM-DD)",
        "Von (HH:MM)",
        "Bis (HH:MM)",
        "Pause Beginn (HH:MM)",
        "Pause Ende (HH:MM)",
        "Anmerkung",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[ZeiteintragRow] = []

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
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self.HEADERS[section]
        return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        row = self._rows[index.row()]
        values = [
            row.datum,
            row.uhrzeit_von,
            row.uhrzeit_bis,
            row.unterbrechung_beginn,
            row.unterbrechung_ende,
            row.anmerkung,
        ]
        return values[index.column()]

    def setData(self, index: QModelIndex, value: object, role: int = Qt.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.EditRole:
            return False

        row = self._rows[index.row()]
        text = str(value).strip()
        if index.column() == 0:
            row.datum = text
        elif index.column() == 1:
            row.uhrzeit_von = text
        elif index.column() == 2:
            row.uhrzeit_bis = text
        elif index.column() == 3:
            row.unterbrechung_beginn = text
        elif index.column() == 4:
            row.unterbrechung_ende = text
        elif index.column() == 5:
            row.anmerkung = text
        else:
            return False

        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
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
