import dash
from dash import callback, Input, Output, State, no_update, ctx, dcc, ALL
import plotly.express as px
import pandas as pd

excel_files = ["results.xlsx","Test-1.xlsx","Test-2.xlsx"]
all_names=[]
for i in range(len(excel_files)):
    names = pd.ExcelFile(excel_files[i]).sheet_names
    all_names.append(names)


@callback(
    Output('sheets-DD', 'children'),
    Output('text-DD-2', 'style'),
    Output('redirec-button', 'style'),
    Input('excels-DD', 'value'),
    Input({'type': 'sheet-dropdown', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_dropdown_and_buttons(selected_excel, sheet_values):
    ctx = dash.callback_context
    
    # Default styles
    text_dd2_style = {"display": "none"}
    button_style = {"display": "none"}
    
    # If no excel file is selected
    if selected_excel is None:
        return None, text_dd2_style, button_style
    
    # Show the "Select the sheet here" text when excel is selected
    text_dd2_style = {"display": "block", "fontSize": "20px", "textAlign": "left", "marginTop":"12px"}
    
    # Determine the current sheet value
    current_sheet_value = None
    if sheet_values and len(sheet_values) > 0:
        current_sheet_value = sheet_values[0]  # Get the first (and should be only) value
    
    # Create the sheet dropdown with preserved value
    index = excel_files.index(selected_excel)
    sheet_dropdown = dcc.Dropdown(
        id={'type': 'sheet-dropdown', 'index': selected_excel},
        options=[{"label": name, "value": name} for name in all_names[index]],
        placeholder="Select a sheet...",
        value=current_sheet_value  # Preserve the selected value
    )
    
    # Check if any sheet is selected
    if current_sheet_value is not None:
        # Show the buttons when a sheet is selected
        button_style = {"display": "flex", "alignItems": "center", "justifyContent": "center", "padding": "80px"}
    
    return sheet_dropdown, text_dd2_style, button_style