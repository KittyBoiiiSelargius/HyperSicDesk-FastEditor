from PyQt6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QToolBar,  QPushButton,
    QFontComboBox, QComboBox, QColorDialog
)
from PyQt6.QtGui import (
    QTextCharFormat, QTextCursor, QFont, QKeySequence, QColor, QAction
)
from PyQt6.QtCore import Qt


class RichTextEditorDialog(QDialog):
    def __init__(self, initial_html="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Editor HTML")
        self.setMinimumSize(750, 550)

        self.text_edit = QTextEdit()
        self.text_edit.setAcceptRichText(True)
        self.text_edit.setHtml(initial_html)

        self.toolbar = QToolBar()

        # Font family selector
        self.font_combo = QFontComboBox()
        self.font_combo.currentFontChanged.connect(self.set_font_family)
        self.toolbar.addWidget(self.font_combo)

        # Font size selector
        self.size_combo = QComboBox()
        self.size_combo.setEditable(True)
        for size in range(8, 30, 2):
            self.size_combo.addItem(str(size))
        self.size_combo.setCurrentText("12")
        self.size_combo.currentTextChanged.connect(self.set_font_size)
        self.toolbar.addWidget(self.size_combo)

        # Bold
        bold_action = QAction("Grassetto", self)
        bold_action.setShortcut(QKeySequence("Ctrl+G"))
        bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(bold_action)
        self.addAction(bold_action)

        # Italic
        italic_action = QAction("Corsivo", self)
        italic_action.setShortcut(QKeySequence("Ctrl+I"))
        italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(italic_action)
        self.addAction(italic_action)

        # Underline
        underline_action = QAction("Sottolinea", self)
        underline_action.setShortcut(QKeySequence("Ctrl+S"))
        underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(underline_action)
        self.addAction(underline_action)

        # Text color
        color_action = QAction("Color", self)
        color_action.triggered.connect(self.set_text_color)
        self.toolbar.addAction(color_action)

        # Insert line
        br_action = QAction("Line", self)
        br_action.triggered.connect(lambda: self.text_edit.insertHtml("<hr>"))
        br_action.setShortcut(QKeySequence("Ctrl+Space"))
        self.toolbar.addAction(br_action)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.text_edit)

        close_button = QPushButton("Chiudi")
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

        self.setLayout(layout)

    def _merge_format_on_selection(self, callback):
        cursor = self.text_edit.textCursor()
        if not cursor.hasSelection():
            cursor.select(QTextCursor.SelectionType.WordUnderCursor)
        fmt = cursor.charFormat()
        callback(fmt)
        cursor.mergeCharFormat(fmt)
        self.text_edit.mergeCurrentCharFormat(fmt)

    def toggle_bold(self):
        def callback(fmt):
            weight = fmt.fontWeight()
            fmt.setFontWeight(QFont.Weight.Normal if weight > QFont.Weight.Normal else QFont.Weight.Bold)
        self._merge_format_on_selection(callback)

    def toggle_italic(self):
        def callback(fmt):
            fmt.setFontItalic(not fmt.fontItalic())
        self._merge_format_on_selection(callback)

    def toggle_underline(self):
        def callback(fmt):
            fmt.setFontUnderline(not fmt.fontUnderline())
        self._merge_format_on_selection(callback)

    def set_font_family(self, font):
        def callback(fmt):
            fmt.setFontFamily(font.family())
        self._merge_format_on_selection(callback)

    def set_font_size(self, size_str):
        try:
            size = int(size_str)
        except ValueError:
            return
        def callback(fmt):
            fmt.setFontPointSize(size)
        self._merge_format_on_selection(callback)

    def set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            def callback(fmt):
                fmt.setForeground(color)
            self._merge_format_on_selection(callback)

    def get_html(self):
        return self.text_edit.toHtml()
