from PyQt6.QtWidgets import QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QDropEvent


from PyQt6.QtWidgets import QTableWidget, QAbstractItemView
from PyQt6.QtGui import QDropEvent, QDragMoveEvent, QDragEnterEvent, QCursor
from PyQt6.QtCore import Qt, QMimeData, QDataStream, QIODevice, QPoint
from PyQt6.QtWidgets import QAbstractItemView

from core.model import FIELD_TYPES


class DraggableTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent

    def dropEvent(self, event: QDropEvent):
        # Allow only internal drags (from this table)
        if not event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            super().dropEvent(event)
            return

        drop_pos = event.position().toPoint()
        drop_index = self.indexAt(drop_pos)
        drop_row = drop_index.row()

        # If drop is below all existing rows
        if drop_row == -1:
            drop_row = self.rowCount()

        # Try to extract dragged rows (custom format)
        mime = event.mimeData()
        raw_data = mime.data("application/x-qtablewidget-rows")
        rows_to_move = []

        if raw_data:
            stream = QDataStream(raw_data, QIODevice.OpenModeFlag.ReadOnly)
            while not stream.atEnd():
                rows_to_move.append(stream.readInt32())
        else:
            # Fallback: use selected rows
            rows_to_move = [i.row() for i in self.selectedIndexes()]
        rows_to_move = sorted(set(rows_to_move))

        first = rows_to_move[0]
        last = rows_to_move[-1] + 1  # exclusive

        # Case 1: Drop inside the same block of rows → reject
        if first <= drop_row < last:
            event.ignore()
            return

        # Case 2: Drop visually inside a row instead of between rows → reject
        indicator = self.dropIndicatorPosition()
        print(indicator)
        if indicator == QAbstractItemView.DropIndicatorPosition.OnItem:
            print("ON ITEM!!!!")
            event.ignore()
            return

        # All checks passed → proceed with default behavior
        super().dropEvent(event)

        if self.parent_window:
            self.parent_window.sync_table_to_model()

    def leaveEvent(self, event):
        # Reset cursor when leaving the widget
        self.setCursor(Qt.CursorShape.ArrowCursor)
        super().leaveEvent(event)


