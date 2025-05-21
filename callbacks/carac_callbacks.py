from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd


# Add a row to the table
@callback(
    Output("carac-table", "data"),
    Input("editing-rows-button-carac", "n_clicks"),
    State("carac-table", "data"),
    State("carac-table", "columns"),
    prevent_initial_call=True
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
        rows.insert(0, rows.pop(len(rows)-1))  # Move the new row to the top
    return rows


# Save changes to the Excel file when the button is clicked (BE CAREFUL !!!)
@callback(
    Output("save-button-carac", "children"),
    Input("save-button-carac", "n_clicks"),
    State("carac-table", "data"),
    State("carac-table", "columns"),
    prevent_initial_call=True
)
def save_changes(n_clicks, table_data, table_columns):
    if n_clicks > 0 and table_data and table_columns:
        df = pd.DataFrame(table_data, columns=[col["id"] for col in table_columns])
        with pd.ExcelWriter("Test-caracterization.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, index=False)
        return "Changes saved ✅"
    return "Save Changes"