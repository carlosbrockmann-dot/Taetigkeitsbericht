from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


@dataclass
class KrankmeldungRow:
    id: int | None
    krank_von: str
    krank_bis: str
    krankmeldungstage: str


class KrankmeldungTableModel(QAbstractTableModel):
    HEADERS = [
        "Von",
        "Bis",
        "Tage",
    ]

    def __init__(self) -> None:
        super().__init__()
        self._rows: list[KrankmeldungRow] = []

    @property
    def rows(self) -> list[KrankmeldungRow]:
        return self._rows

    def set_rows(self, rows: list[KrankmeldungRow]) -> None:
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
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            if 0 <= section < len(self.HEADERS):
                return self.HEADERS[section]
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
            return str(section + 1)
        return None

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> str | None:
        if not index.isValid() or role not in (Qt.DisplayRole, Qt.EditRole):
            return None
        row = self._rows[index.row()]
        col = index.column()
        if col == 0:
            return row.krank_von
        if col == 1:
            return row.krank_bis
        if col == 2:
            return row.krankmeldungstage
        return None

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled
