import pandas as pd
from dash.dash_table.Format import Format

def load_filtered_df(sheet):
    df = pd.read_excel("results.xlsx", sheet_name=sheet)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.strftime('%d/%m/%Y')
    if all(col in df.columns for col in ['Conversion', 'Yield', 'Selectivity']):
        df = df[~((df['Conversion'] == 'nd') & (df['Yield'] == 'nd') & (df['Selectivity'] == 'nd'))]
    return df

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

def get_column_dropdown_options(df):
    return [{"label": col, "value": col} for col in df.columns]
