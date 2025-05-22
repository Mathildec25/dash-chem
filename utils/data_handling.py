import pandas as pd
from dash.dash_table.Format import Format

# Return the selected sheet after formatting the date column
def load_filtered_df(excel, sheet):
    df = pd.read_excel(excel, sheet_name=sheet)
    if 'Date' in df.columns:    
        df['Date'] = pd.to_datetime(df['Date'])     # Transform to datetime
        df.sort_values(by=['Date'], inplace=True, ascending=False)      # Sort by date and descending
        df['Date']=df['Date'].dt.strftime('%d/%m/%Y')       # Apply the good format
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
