# ui/main_window.py
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtGui import QKeySequence
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QFileDialog,
    QTableWidget, QTableWidgetItem, QMenu, QMessageBox,
    QComboBox, QCheckBox, QHBoxLayout, QDialog,
    QTextEdit, QPushButton, QLabel, QAbstractItemView, QInputDialog, QHeaderView
)

from PyQt6.QtGui import QKeyEvent

from core.excel_io import load_excel_file, save_excel_file
from core.model import FormDocument, FormField, FIELD_TYPES
from ui.widgets import DraggableTableWidget
from ui.r_html_editor import RichTextEditorDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self._copied_group = None
        self._copied_default_data = None

        self.setWindowTitle("Hypersic Online Form Editor")
        self.resize(1300, 800)

        self.document = FormDocument()

        self._copied_fields: list[FormField] = []
        self._custom_field_factory = None

        self._cut_fields = []
        self._cut_origin_rows = []

        self.undo_stack = []
        self.redo_stack = []

        # Menu bar
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        self.load_action = QAction("Apri file Excel", self)
        self.load_action.setShortcut(QKeySequence("Ctrl+O"))
        self.load_action.triggered.connect(self.load_file)
        file_menu.addAction(self.load_action)

        self.export_action = QAction("Salva file Excel", self)
        self.export_action.setShortcut(QKeySequence("Ctrl+Shift+S"))
        self.export_action.triggered.connect(self.export_file)
        file_menu.addAction(self.export_action)

        # Menu bar add
        add_menu = menubar.addMenu("Aggiungi")

        self.add_field_action = QAction("Nuovo campo (Annotazione)", self)
        self.add_field_action.setShortcut(QKeySequence("Ctrl+N"))
        self.add_field_action.triggered.connect(self.prompt_field_insertion)
        add_menu.addAction(self.add_field_action)

        self.add_field_action.setEnabled(False)  # disable if no document is loaded!

        self.add_field_action_b = QAction("Nuovo campo (Annotazione) in fondo", self)
        self.add_field_action_b.setShortcut(QKeySequence("Ctrl+Shift+N"))
        self.add_field_action_b.triggered.connect(self.insert_field_b)
        add_menu.addAction(self.add_field_action_b)

        self.add_field_action_b.setEnabled(False)

        # Menu Modifica
        edit_menu = menubar.addMenu("Modifica")

        self.copy_action = QAction("Copia", self)
        self.copy_action.setShortcut(QKeySequence("Ctrl+C"))
        self.copy_action.triggered.connect(self.trigger_copy)
        edit_menu.addAction(self.copy_action)

        self.cut_action = QAction("Taglia", self)
        self.cut_action.setShortcut(QKeySequence("Ctrl+X"))
        self.cut_action.triggered.connect(self.trigger_cut)
        edit_menu.addAction(self.cut_action)

        self.paste_action = QAction("Incolla", self)
        self.paste_action.setShortcut(QKeySequence("Ctrl+V"))
        self.paste_action.triggered.connect(self.trigger_paste)
        edit_menu.addAction(self.paste_action)

        self.assign_group_action = QAction("Assegna a gruppo", self)
        self.assign_group_action.triggered.connect(
            lambda: self.assign_group_dialog(self.table.selectionModel().selectedRows()))
        edit_menu.addAction(self.assign_group_action)

        self.toggle_mandatory_action = QAction("Abilita/disabilita obbligatorietà", self)
        self.toggle_mandatory_action.triggered.connect(
            lambda: self.toggle_mandatory(self.table.selectionModel().selectedRows()))
        edit_menu.addAction(self.toggle_mandatory_action)

        self.delete_action = QAction("Elimina", self)
        self.delete_action.setShortcut(QKeySequence(Qt.Key.Key_Delete))
        self.delete_action.triggered.connect(
            lambda: self.delete_rows(self.table.selectionModel().selectedRows()))
        edit_menu.addAction(self.delete_action)

        self.undo_action = QAction("Annulla", self)
        self.undo_action.setShortcut(QKeySequence("Ctrl+Z"))
        self.undo_action.triggered.connect(self.undo)
        edit_menu.addAction(self.undo_action)

        self.redo_action = QAction("Ripeti", self)
        self.redo_action.setShortcut(QKeySequence("Ctrl+Y"))
        self.redo_action.triggered.connect(self.redo)
        edit_menu.addAction(self.redo_action)

        # Central widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout()
        main_widget.setLayout(layout)

        # Table
        self.table = DraggableTableWidget(parent=self)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)

        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Codice", "Tipologia", "Descrizione", "Raggruppamento", "Campo obbligatorio", "Dati di default"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.open_context_menu)
        self.table.cellChanged.connect(self.sync_table_to_model)
        self.table.cellDoubleClicked.connect(self.handle_double_click)

        # Enable drag and drop inside the table
        self.table.setDragEnabled(True)
        self.table.setAcceptDrops(True)
        self.table.setDragDropOverwriteMode(False)
        self.table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.table.viewport().setAcceptDrops(True)

        # Connect to header press for drag restriction
        self.table.verticalHeader().sectionPressed.connect(self.start_drag_from_header)
        self.table.selectionModel().selectionChanged.connect(self.update_edit_actions)
        self.update_edit_actions()

        layout.addWidget(self.table)

        self._suppress_signal = False
        self._drag_allowed = False

    def update_edit_actions(self):
        selection = self.table.selectionModel().selectedRows()
        has_selection = bool(selection)
        self.copy_action.setEnabled(has_selection)
        self.cut_action.setEnabled(has_selection)
        self.paste_action.setEnabled(has_selection and (bool(self._cut_fields)) or bool(self._copied_fields))
        self.assign_group_action.setEnabled(has_selection)
        self.toggle_mandatory_action.setEnabled(has_selection)
        self.delete_action.setEnabled(has_selection)
        self.undo_action.setEnabled(bool(self.undo_stack))
        self.redo_action.setEnabled(bool(self.redo_stack))

    def trigger_copy(self):
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            self.copy_selected_rows(indexes)
            self.update_edit_actions()

    def trigger_cut(self):
        indexes = self.table.selectionModel().selectedRows()
        if indexes:
            self._copied_fields = []
            self.cut_selected_rows(indexes)

    def trigger_paste(self):
        indexes = self.table.selectionModel().selectedRows()
        if indexes and (bool(self._cut_fields) or bool(self._copied_fields)):
            if bool(self._cut_fields):
                self.save_snapshot()
                row = indexes[0].row() + 1
                for i, field in enumerate(self._cut_fields):
                    self.insert_existing_field_at(row + i, field.copy())
                self._cut_fields = []
                self._cut_origin_rows = []
            else:
                row = indexes[0].row() + 1
                self.paste_fields_at(row)
        self.update_edit_actions()

    def insert_existing_field_at(self, row, field: FormField):
        self.document.add_field(field=field, position=row)
        self.refresh_table()

    def copy_group(self, indexes):
        if indexes:
            first_row = indexes[0].row()
            if 0 <= first_row < len(self.document.fields):
                self._copied_group = self.document.fields[first_row].group

    def paste_group(self, indexes):
        if self._copied_group is not None:
            self.save_snapshot()
            rows = [index.row() for index in indexes]
            self.document.update_group(rows, self._copied_group)
            self.refresh_table()

    def copy_default_data(self, indexes):
        if indexes:
            first_row = indexes[0].row()
            if 0 <= first_row < len(self.document.fields):
                self._copied_default_data = self.document.fields[first_row].default_data
                print(f"[COPY DEFAULT] Default data copiato: {self._copied_default_data}")

    def paste_default_data(self, indexes):
        self.save_snapshot()
        if self._copied_default_data is not None:
            rows = [index.row() for index in indexes]
            self.document.update_default_data(rows, self._copied_default_data)
            self.refresh_table()

    def delete_rows(self, indexes):
        self.save_snapshot()
        rows = sorted([index.row() for index in indexes], reverse=True)
        for row in rows:
            self.document.remove_field(row)
        self.refresh_table()

    def copy_selected_rows(self, indexes):
        rows = [i.row() for i in indexes]
        self._copied_fields = [self.document.fields[i].copy() for i in rows]

    def cut_selected_rows(self, indexes):
        self.save_snapshot()
        if self._cut_fields and self._cut_origin_rows:
            for i, field in zip(self._cut_origin_rows, self._cut_fields):
                self.document.add_field(field.copy(), i)
            self._cut_fields = []
            self._cut_origin_rows = []

        rows = sorted(set(index.row() for index in indexes))
        self._cut_origin_rows = rows
        self._cut_fields = [self.document.fields[i].copy() for i in rows]
        self.delete_rows(indexes)

    def start_drag_from_header(self, index):
        self._drag_allowed = True

    def paste_fields_at(self, row: int):
        self.save_snapshot()
        for i, field in enumerate(self._copied_fields):
            self.insert_existing_field_at(row + i, field.copy())

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Apri file Excel Dati Specifici", "", "Excel Files (*.xlsx *.xls)")
        if path:
            try:
                self.document = load_excel_file(path)
                self.refresh_table()
                self.add_field_action.setEnabled(True)
                self.add_field_action_b.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def export_file(self):
        path, _ = QFileDialog.getSaveFileName(self, "Salva file Excel Dati Specifici", "", "Excel Files (*.xlsx)")
        if path:
            try:
                save_excel_file(path, self.document)
                QMessageBox.information(self, "Export", "Fatto")
            except Exception as e:
                QMessageBox.critical(self, "Errore", str(e))

    def refresh_table(self):
        self._suppress_signal = True
        self.table.setRowCount(len(self.document.fields))
        for i, field in enumerate(self.document.fields):
            self.table.setItem(i, 0, QTableWidgetItem(field.code))

            combo = QComboBox()
            combo.addItems(FIELD_TYPES.keys())
            label = next((k for k, v in FIELD_TYPES.items() if v == field.data_type), None)
            if label:
                combo.setCurrentText(label)
            combo.currentTextChanged.connect(lambda label, row=i: self.update_type(row, FIELD_TYPES[label]))
            self.table.setCellWidget(i, 1, combo)

            self.table.setItem(i, 2, QTableWidgetItem(field.description))
            self.table.setItem(i, 3, QTableWidgetItem(field.group or ""))

            checkbox = QCheckBox()
            checkbox.setChecked(field.mandatory)
            checkbox.stateChanged.connect(lambda _, row=i: self.update_mandatory(row))
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.addWidget(checkbox)
            layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.table.setCellWidget(i, 4, container)

            self.table.setItem(i, 5, QTableWidgetItem(str(field.default_data)))

            selection = self.table.selectionModel().selectedRows()
            has_selection = bool(selection)

            self.copy_action.setEnabled(has_selection)
            self.cut_action.setEnabled(has_selection)
            self.paste_action.setEnabled(has_selection and bool(self._cut_fields))
            self.assign_group_action.setEnabled(has_selection)
            self.toggle_mandatory_action.setEnabled(has_selection)

        self._suppress_signal = False

    def sync_table_to_model(self):
        if self._suppress_signal:
            return
        for i, field in enumerate(self.document.fields):
            # Column 0: Code
            field.code = self.table.item(i, 0).text()

            # Column 1: Type (QComboBox)
            combo = self.table.cellWidget(i, 1)
            if combo and isinstance(combo, QComboBox):
                label = combo.currentText()
                field.data_type = FIELD_TYPES.get(label, label)

            # Column 2: Description
            field.description = self.table.item(i, 2).text()

            # Column 3: Group
            field.group = self.table.item(i, 3).text() or None

            field.default_data = self.table.item(i, 5).text()

        print(self.document)

    def update_type(self, row, value):
        if 0 <= row < len(self.document.fields):
            self.document.fields[row].data_type = value

    def update_mandatory(self, row):
        if 0 <= row < len(self.document.fields):
            container = self.table.cellWidget(row, 4)
            checkbox = container.findChild(QCheckBox)
            if checkbox:
                self.document.fields[row].mandatory = checkbox.isChecked()

    def handle_double_click(self, row, column):
        if column == 2:
            if 0 <= row < len(self.document.fields):
                field = self.document.fields[row]
                if field.data_type == "AN":
                    dialog = RichTextEditorDialog(initial_html=field.description, parent=self)
                    if dialog.exec():
                        new_html = dialog.get_html()
                        self.document.fields[row].description = new_html
                        self.table.item(row, 2).setText(new_html)

    def swap_rows(self, row1, row2):
        self.save_snapshot()
        self.document.swap_field(row1, row2)
        self.refresh_table()

    def open_context_menu(self, position):
        indexes = self.table.selectionModel().selectedRows()
        if not indexes:
            return

        menu = QMenu()

        clicked_row = indexes[0].row()

        add_here_action = QAction("Aggiungi nuova riga qui", self)
        add_here_action.triggered.connect(lambda: self.insert_existing_field_at(
            clicked_row + 1,
            FormField(code="ANNOTA", data_type="AN", description="", group=None, mandatory=False)
        ))
        menu.addAction(add_here_action)

        custom_action = QAction("Aggiungi un campo con una linea qui", self)
        custom_action.triggered.connect(lambda: self.insert_existing_field_at(
            clicked_row + 1,
            FormField.create_line()
        ))
        menu.addAction(custom_action)
        menu.addSeparator()

        copy_action = QAction("Copia righe selezionate", self)
        copy_action.triggered.connect(lambda: self.copy_selected_rows(indexes))
        menu.addAction(copy_action)

        if self._copied_fields:
            paste_action = QAction("Incolla righe qui", self)
            paste_action.triggered.connect(lambda: self.paste_fields_at(clicked_row + 1))
            menu.addAction(paste_action)

        menu.addSeparator()

        assign_action = QAction("Assegna a gruppo", self)
        assign_action.triggered.connect(lambda: self.assign_group_dialog(indexes))
        menu.addAction(assign_action)

        toggle_mandatory_action = QAction("Abilita/disabilita obbligatorietà", self)
        toggle_mandatory_action.triggered.connect(lambda: self.toggle_mandatory(indexes))
        menu.addAction(toggle_mandatory_action)

        menu.addSeparator()

        # --- COPY group / default_data ---
        copy_group_action = QAction("Copia gruppo", self)
        copy_group_action.triggered.connect(lambda: self.copy_group(indexes))
        menu.addAction(copy_group_action)

        copy_default_data_action = QAction("Copia dati di default", self)
        copy_default_data_action.triggered.connect(lambda: self.copy_default_data(indexes))
        menu.addAction(copy_default_data_action)

        # --- PASTE group / default_data ---
        if self._copied_group is not None:
            paste_group_action = QAction("Incolla gruppo nelle righe selezionate", self)
            paste_group_action.triggered.connect(lambda: self.paste_group(indexes))
            menu.addAction(paste_group_action)

        if self._copied_default_data is not None:
            paste_default_action = QAction("Incolla default_data nelle righe selezionate", self)
            paste_default_action.triggered.connect(lambda: self.paste_default_data(indexes))
            menu.addAction(paste_default_action)

        # --- DELETE ---
        menu.addSeparator()
        delete_action = QAction("Elimina riga/e", self)
        delete_action.triggered.connect(lambda: self.delete_rows(indexes))
        menu.addAction(delete_action)

        set_type_menu = QMenu("Imposta tipologia", self)
        for label, code in FIELD_TYPES.items():
            action = QAction(label, self)
            action.triggered.connect(lambda _, c=code: self.set_type(indexes, c))
            set_type_menu.addAction(action)
        menu.addMenu(set_type_menu)

        menu.exec(self.table.viewport().mapToGlobal(position))

    def assign_group_dialog(self, indexes):
        from PyQt6.QtWidgets import QInputDialog
        group_name, ok = QInputDialog.getText(self, "Assegna gruppo", "Gruppo...")
        if ok and group_name:
            self.save_snapshot()
            row_indices = [index.row() for index in indexes]
            self.document.assign_group(row_indices, group_name)
            self.refresh_table()

    def toggle_mandatory(self, indexes):
        for index in indexes:
            row = index.row()
            container = self.table.cellWidget(row, 4)
            checkbox = container.findChild(QCheckBox)
            if checkbox:
                checkbox.setChecked(not checkbox.isChecked())

    def set_type(self, indexes, data_type):
        for index in indexes:
            row = index.row()
            combo = self.table.cellWidget(row, 1)
            if combo:
                label = next((k for k, v in FIELD_TYPES.items() if v == data_type), data_type)
                combo.setCurrentText(label)

    def prompt_field_insertion(self):
        if not self.document or not isinstance(self.document, FormDocument):
            QMessageBox.warning(self, "Errore", "Nessun documento caricato.")
            return

        max_index = len(self.document.fields)
        index, ok = QInputDialog.getInt(
            self,
            "Inserisci nuova riga",
            f"Inserisci la posizione (0–{max_index}):",
            value=max_index,  # di default in fondo
            min=0,
            max=max_index
        )

        if ok:
            self.save_snapshot()
            new_field = FormField.create_empty()
            self.document.add_field(field=new_field, position=index)
            self.refresh_table()

    def insert_field_b(self):
        self.save_snapshot()
        self.document.add_field(FormField.create_empty(), len(self.document))
        self.refresh_table()

    def save_snapshot(self):
        self.undo_stack.append(self.document.copy())
        self.redo_stack.clear()

    def set_document_snapshot(self, snapshot):
        self._suppress_signal = True
        self.table.blockSignals(True)  # blocca TUTTI i segnali widget → slot

        self.document = snapshot
        self.refresh_table()

        self.table.blockSignals(False)
        self._suppress_signal = False

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(self.document.copy())
        # print("miao")
        snapshot = self.undo_stack.pop()
        self.set_document_snapshot(snapshot)

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(self.document.copy())
        snapshot = self.redo_stack.pop()
        self.set_document_snapshot(snapshot)
