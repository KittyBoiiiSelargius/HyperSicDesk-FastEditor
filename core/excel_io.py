# core/excel_io.py
import pandas as pd
from core.model import FormDocument


def load_excel_file(path: str) -> FormDocument:
    document = FormDocument()
    try:
        df = pd.read_excel(path)
        document.load_from_dataframe(df)
        return document
    except Exception as e:
        raise RuntimeError(f"Error reading Excel file: {e}")


def save_excel_file(path: str, document: FormDocument):
    try:
        df = pd.DataFrame(document.export_to_dataframe())
        df.to_excel(path, index=False)
    except Exception as e:
        raise RuntimeError(f"Error writing Excel file: {e}")