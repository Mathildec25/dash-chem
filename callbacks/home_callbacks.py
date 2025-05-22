from dash import callback, Input, Output, State, no_update, ctx, dcc
import plotly.express as px
import pandas as pd

excel_files = ["results.xlsx","Test-1.xlsx","Test-2.xlsx"]
all_names=[]
for i in range(len(excel_files)):
    names = pd.ExcelFile(excel_files[i]).sheet_names
    all_names.append(names)


@callback(
    Output('sheets-DD', 'children'),
    Input('excels-DD', 'value')
)
def update_sub_dropdown(selected_excel):
    if selected_excel is None:
        return None

    index = excel_files.index(selected_excel)
    return dcc.Dropdown(
        id={'type': 'sheet-dropdown', 'index': selected_excel},
        options=[{"label": name, "value": name} for name in all_names[index]],
        placeholder="Select a sheet..."
    )