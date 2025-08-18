import pandas as pd
from dash.dash_table.Format import Format
import os

from config_path import EXCEL_FOLDER

# Return the selected sheet after formatting the date column
def load_filtered_df(excel, sheet):
    # Ensure extension
    if not excel.endswith(".xlsx"):
        excel += ".xlsx"

    # Build full path
    file_path = os.path.join(EXCEL_FOLDER, excel)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Excel file not found: {file_path}")

    df = pd.read_excel(file_path, sheet_name=sheet, engine="openpyxl")

    if 'Date' in df.columns:    
        df['Date'] = pd.to_datetime(df['Date'], errors="coerce")   # Safe conversion
        df.sort_values(by=['Date'], inplace=True, ascending=False)
        df['Date'] = df['Date'].dt.strftime('%d/%m/%Y')

    return df

# Return the columns of the selected sheet after round needed values
def get_columns(df):
    around_needed = ['Conversion', 'Yield', 'Selectivity']
    columns = []
    for col in df.columns:
        col_info = {"name": col, "id": col}
        if col in around_needed:
            col_info["type"] = "numeric"
            col_info["format"] = Format(precision=0, scheme="f")
        columns.append(col_info)
    return columns

# Return the columns with dropdown for Yes/No col in caracterization sheets
def get_columns_carac(df):
    Yes_No = {"NMR H", "NMR C", "GC", "LC"}  # faster with set
    return [
        {"name": col, "id": col, "presentation": "dropdown", "editable": True} if col in Yes_No else {"name": col, "id": col}
        for col in df.columns
    ]

# Return the correct format for dropdowns 
def get_column_dropdown_options(df):
    return [{"label": col, "value": col} for col in df.columns]
