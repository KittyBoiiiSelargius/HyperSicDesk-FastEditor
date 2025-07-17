# core/model.py
from core.annotations_presets import beautiful_line

FIELD_TYPES = {
    "Casella di selezione": "CS",
    "Campo testo": "TE",
    "Annotazione": "AN",
    "Data": "DA"
}


class FormField:
    def __init__(self, code: str, data_type: str, description: str, mandatory: int, group=None, default_data: str=None,
                 classification: int = None, order: int = 0, annotation: str = "", hypersic_module=None,
                 linked_field: str = ""):
        self.code = code if isinstance(code, str) else ""  # Unique identifier (e.g., FIGLIO_COGNOME)
        self.data_type = data_type if isinstance(data_type, str) else "TE"  # "CS", "TE", or "AN"
        self.description = description if isinstance(description, str) else ""  # Display text or HTML (for AN)
        self.group = group if isinstance(group, str) else ""  # Optional logical group
        self.mandatory = mandatory
        self.default_data = default_data if isinstance(default_data, str) else ""
        self.classification = classification
        self.order = order,
        self.annotation = annotation
        self.hypersic_module = hypersic_module
        self.linked_field = linked_field

        if code.startswith("FL"):
            self.data_type = "CS"

    def to_dict(self):
        return {
            "CLASSIFICAZIONE": self.classification,
            "ORDINE": self.order,
            "CODICE": self.code,
            "DESCRIZIONE": self.description,
            "CATEGORIA": self.group or "",
            "OBBLIGO": -1 if self.mandatory else 0,
            "TIPOLOGIA": self.data_type,
            "DATI": self.default_data,
            "ANNOTAZIONI": self.annotation,
            "MODULO_HYPERSIC": self.hypersic_module,
            "CAMPO_COLLEGATO": self.linked_field
        }

    def copy(self):
        return FormField(
            code=self.code,
            data_type=self.data_type,
            description=self.description,
            mandatory=self.mandatory,
            group=self.group,
            default_data=self.default_data
        )

    def __str__(self):
        return f" {self.code}\t{self.data_type}\t{self.mandatory}\t{self.group or ""}"

    @staticmethod
    def create_line():
        return FormField(code="RIGO", data_type="AN", description=beautiful_line, mandatory=False)

    @staticmethod
    def create_empty():
        return FormField(
                code="NEW_CODE",
                data_type="AN",
                description="",
                group=None,
                mandatory=False,
                default_data=""
            )


class FormDocument:
    def __init__(self):
        self.fields = []  # List of FormField
        self.classification = None

    def __str__(self):
        result = ""
        for n, i in enumerate(self.fields):
            result += str(n) + str(i) + "\n"
        return result

    def add_field(self, field: FormField, position=None):
        if position is None:
            self.fields.append(field)
        else:
            self.fields.insert(position, field)
        self._refresh()

    def remove_field(self, index: int):
        if 0 <= index < len(self.fields):
            del self.fields[index]
        self._refresh()

    def update_group(self, indexes: list[int], group_value: str):
        for idx in indexes:
            if 0 <= idx < len(self.fields):
                self.fields[idx].group = group_value

    def update_default_data(self, indexes: list[int], default_value):
        for idx in indexes:
            if 0 <= idx < len(self.fields):
                self.fields[idx].default_data = default_value

    def assign_group(self, indices, group):
        for i in indices:
            self.fields[i].group = group

    def move_field(self, from_index, to_index):
        field = self.fields.pop(from_index)
        self.fields.insert(to_index, field)
        self._refresh()

    def load_from_dataframe(self, df):
        self.fields.clear()
        self.classification = None
        for _, row in df.iterrows():
            field = FormField(
                classification=row.get("CLASSIFICAZIONE", ""),
                code=row.get("CODICE", ""),
                data_type=row.get("TIPOLOGIA", ""),
                description=row.get("DESCRIZIONE", ""),
                mandatory=row.get("OBBLIGO", ""),
                group=row.get("CATEGORIA", ""),
                default_data=row.get("DATI", ""),
                annotation=row.get("ANNOTAZIONI", ""),
                hypersic_module=row.get("MODULO_HYPERSIC", ""),
                linked_field=row.get("LINKED_FIELD", "")
            )
            if isinstance(field.classification, int) and field.classification > 0:
                self.classification = field.classification
                print(self.classification)
            self.add_field(field)
        self._refresh()

    def __len__(self):
        return len(self.fields)

    def _refresh(self):
        for n, field in enumerate(self.fields):
            field.order = n * 100
            field.classification = self.classification
            codes = [field.code for field in self.fields]
            while field.code in codes[0:n]:
                field.code += "*"

    def export_to_dataframe(self):
        self._refresh()
        return [field.to_dict() for field in self.fields]
