# core/model.py
from core.annotations_presets import beautiful_line

FIELD_TYPES = {
    "Casella di selezione": "CS",
    "Campo testo": "TE",
    "Annotazione": "AN"
}


class FormField:
    def __init__(self, code, data_type, description, mandatory, group=None, default_data=None):
        self.code = code  # Unique identifier (e.g., FIGLIO_COGNOME)
        self.data_type = data_type  # "CS", "TE", or "AN"
        self.description = description  # Display text or HTML (for AN)
        self.group = group  # Optional logical group
        self.mandatory = mandatory
        self.default_data = default_data

    def to_dict(self):
        return {
            "CODICE": self.code,
            "TIPOLOGIA": self.data_type,
            "DESCRIZIONE": self.description,
            "OBBLIGO": -1 if self.mandatory else 0,
            "CATEGORIA": self.group or "",
            "DATI": self.default_data
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


class FormDocument:
    def __init__(self):
        self.fields = []  # List of FormField
        self.groups = set()

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

    def remove_field(self, index: int):
        if 0 <= index < len(self.fields):
            del self.fields[index]

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
        self.groups.add(group)

    def add_group(self, name):
        self.groups.add(name)

    def remove_group(self, name):
        self.groups.discard(name)
        for field in self.fields:
            if field.group == name:
                field.group = None

    def move_field(self, from_index, to_index):
        field = self.fields.pop(from_index)
        self.fields.insert(to_index, field)

    def load_from_dataframe(self, df):
        self.fields.clear()
        self.groups.clear()
        for _, row in df.iterrows():
            field = FormField(
                code=row.get("CODICE", ""),
                data_type=row.get("TIPOLOGIA", ""),
                description=row.get("DESCRIZIONE", ""),
                mandatory=row.get("OBBLIGO", ""),
                group=row.get("CATEGORIA", None),
                default_data=row.get("DATI", "")
            )
            self.add_field(field)

    def __len__(self):
        return len(self.fields)

    def export_to_dataframe(self):
        return [field.to_dict() for field in self.fields]
