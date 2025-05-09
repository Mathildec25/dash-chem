import pandas as pd
from dash.dash_table.Format import Format

# Return the selected sheet after formatting the date column
def load_filtered_df(sheet):
    df = pd.read_excel("results.xlsx", sheet_name=sheet)
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
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

# Return the correct format for dropdowns 
def get_column_dropdown_options(df):
    return [{"label": col, "value": col} for col in df.columns]
