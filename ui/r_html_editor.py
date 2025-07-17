from PyQt6.QtWidgets import (
    QDialog, QTextEdit, QVBoxLayout, QToolBar,  QPushButton,
    QFontComboBox, QComboBox, QColorDialog
)
from PyQt6.QtGui import (
    QTextCharFormat, QTextCursor, QFont, QKeySequence, QColor, QAction
)
from PyQt6.QtCore import Qt
import re


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
        self.bold_action = QAction("Grassetto", self)
        self.bold_action.setShortcut(QKeySequence("Ctrl+G"))
        self.bold_action.setCheckable(True)
        self.bold_action.triggered.connect(self.toggle_bold)
        self.toolbar.addAction(self.bold_action)
        self.addAction(self.bold_action)

        # Italic
        self.italic_action = QAction("Corsivo", self)
        self.italic_action.setShortcut(QKeySequence("Ctrl+I"))
        self.italic_action.setCheckable(True)
        self.italic_action.triggered.connect(self.toggle_italic)
        self.toolbar.addAction(self.italic_action)
        self.addAction(self.italic_action)

        # Underline
        self.underline_action = QAction("Sottolinea", self)
        self.underline_action.setShortcut(QKeySequence("Ctrl+S"))
        self.underline_action.setCheckable(True)
        self.underline_action.triggered.connect(self.toggle_underline)
        self.toolbar.addAction(self.underline_action)
        self.addAction(self.underline_action)

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

        self.text_edit.cursorPositionChanged.connect(self.update_format_buttons)

    def _apply_char_format(self, fmt: QTextCharFormat):
        cursor = self.text_edit.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        else:
            self.text_edit.setCurrentCharFormat(fmt)

    def update_format_buttons(self):
        fmt = self.text_edit.currentCharFormat()

        # Aggiorna gli stati dei pulsanti toggle
        self.bold_action.setChecked(fmt.fontWeight() > QFont.Weight.Normal)
        self.italic_action.setChecked(fmt.fontItalic())
        self.underline_action.setChecked(fmt.fontUnderline())

        # Aggiorna la combo della dimensione del font
        point_size = fmt.fontPointSize()
        if point_size <= 0:
            point_size = fmt.font().pointSize()

        if point_size > 0:
            size_str = str(int(point_size))
            if self.size_combo.currentText() != size_str:
                self.size_combo.blockSignals(True)
                self.size_combo.setCurrentText(size_str)
                self.size_combo.blockSignals(False)


    def toggle_bold(self):
        cursor = self.text_edit.textCursor()
        current_fmt = cursor.charFormat() if cursor.hasSelection() else self.text_edit.currentCharFormat()
        new_weight = QFont.Weight.Normal if current_fmt.fontWeight() > QFont.Weight.Normal else QFont.Weight.Bold

        fmt = QTextCharFormat()
        fmt.setFontWeight(new_weight)
        self._apply_char_format(fmt)
        self.bold_action.setChecked(new_weight > QFont.Weight.Normal)

    def toggle_italic(self):
        cursor = self.text_edit.textCursor()
        current_fmt = cursor.charFormat() if cursor.hasSelection() else self.text_edit.currentCharFormat()
        new_italic = not current_fmt.fontItalic()

        fmt = QTextCharFormat()
        fmt.setFontItalic(new_italic)
        self._apply_char_format(fmt)
        self.italic_action.setChecked(new_italic)

    def toggle_underline(self):
        cursor = self.text_edit.textCursor()
        current_fmt = cursor.charFormat() if cursor.hasSelection() else self.text_edit.currentCharFormat()
        new_underline = not current_fmt.fontUnderline()

        fmt = QTextCharFormat()
        fmt.setFontUnderline(new_underline)
        self._apply_char_format(fmt)
        self.underline_action.setChecked(new_underline)

    def set_font_family(self, font):
        fmt = QTextCharFormat()
        fmt.setFontFamily(font.family())
        self._apply_char_format(fmt)

    def set_font_size(self, size_str):
        try:
            size = int(size_str)
        except ValueError:
            return
        fmt = QTextCharFormat()
        fmt.setFontPointSize(size)
        self._apply_char_format(fmt)

    def set_text_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            fmt = QTextCharFormat()
            fmt.setForeground(color)
            self._apply_char_format(fmt)

    def get_html(self):
        # return self.text_edit.toHtml()
        return self.get_html_fragment()

    def get_html_fragment(self):
        full_html = self.text_edit.toHtml()
        match = re.search(r'<body[^>]*>(.*?)</body>', full_html, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1).strip()
        return full_html  # fallback, nel caso non trovi il body
