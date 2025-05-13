from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
from components.Figures import load_filtered_df_graph
import pandas as pd

### CALLBACKS TO GENERATE THE TABLE PARTS###

# Load and return the table for the selected sheet and return the column dropdown options and values
@callback(
    [Output("main-content", "children"),
     Output("column-dropdown", "options"),
     Output("column-dropdown", "value"),],
    Input("selected-sheet-store", "data")
)
def load_table_for_sheet(sheet):
    if not sheet:
        return html.Div("No sheet selected"), [], []

    df = load_filtered_df(sheet)
    columns = get_columns(df)
    options = get_column_dropdown_options(df)

    # Create the DataTable component
    table = dash_table.DataTable(
        id={"type": "editable-table", "sheet": sheet},
        data=df.to_dict('records'),
        columns=columns,
        css=[
            {"selector": ".dash-spreadsheet-container", "rule": "max-height: 100vh !important; height: 75vh !important;"},
            {"selector": ".dash-spreadsheet-inner", "rule": "max-height: 100vh !important; height: 75vh !important;"},
            {"selector": ".dash-table-container", "rule": "max-height: 100vh !important; height: 75vh !important;"}
        ],
        tooltip_data=[
            {column: {'value': str(value), 'type': 'markdown'} for column, value in row.items()}
            for row in df.to_dict('records')
        ],
        tooltip_delay=0,
        tooltip_duration=None,
        editable=True,
        style_header={
            'backgroundColor': 'white', 'textAlign': 'left', 'fontSize': '14px',
            'fontWeight': 'bold', 'border': '1px solid black'
        },
        fixed_rows={'headers': True},
        style_data_conditional=[
            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
        ],    
        style_cell_conditional=[
            {'if': {'column_id': c}, 'textAlign': 'left'} for c in [
                'Date', 'Exp code', 'Operator', 'System', 'React 1', 'React 2', 'React 3',
                'React 4', 'Catalyst', 'Additive 1', 'Additive 2', 'Solvent', 'Comments']
        ],
        style_as_list_view=True,
        style_cell={'padding': '8px'},
        page_action='none',
        style_table={'width': '99.5%', 'overflowY': 'auto', 'overflowX': 'auto'},
        style_data={'width': '125px', 'minWidth': '125px', 'maxWidth': '125px', 'overflow': 'hidden', 'textOverflow': 'ellipsis'},
        filter_action='native',
        sort_action='native',
        sort_mode='single',
        filter_options={"placeholder_text": "Filter.."}
    )

    return html.Div(table, style={"padding": "4px"}), options, [opt["value"] for opt in options]

# Update the columns of the table based on the selected columns in the dropdown
@callback(
    Output({"type": "editable-table", "sheet": MATCH}, "columns"),
    Input("column-dropdown", "value"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def update_columns(selected_columns, selected_sheet):
    if not selected_sheet or not selected_columns:
        return no_update
    df = load_filtered_df(selected_sheet)
    full_columns = get_columns(df)
    return [col for col in full_columns if col["id"] in selected_columns]

# Add a new row to the table when the button is clicked
@callback(
    Output({"type": "editable-table", "sheet": MATCH}, "data"),
    Input("editing-rows-button", "n_clicks"),
    State({"type": "editable-table", "sheet": MATCH}, "data"),
    State({"type": "editable-table", "sheet": MATCH}, "columns"),
    prevent_initial_call=True
)
def add_row(n_clicks, rows, columns):
    if n_clicks > 0:
        rows.append({c['id']: '' for c in columns})
    return rows

# Save changes to the Excel file when the button is clicked (BE CAREFUL !!!)
@callback(
    Output("save-button", "children"),
    Input("save-button", "n_clicks"),
    State({"type": "editable-table", "sheet": ALL}, "data"),
    State({"type": "editable-table", "sheet": ALL}, "columns"),
    State("selected-sheet-store", "data"),
    prevent_initial_call=True
)
def save_changes(n_clicks, all_tables_data, all_tables_columns, sheet):
    if n_clicks > 0 and all_tables_data and all_tables_columns and sheet:
        df = pd.DataFrame(all_tables_data[0], columns=[c["id"] for c in all_tables_columns[0]])
        with pd.ExcelWriter("results.xlsx", engine="openpyxl", mode="a", if_sheet_exists="replace") as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)
        return "Changes saved ✅"
    return "Save Changes"

# Return options for all dropdowns in the visualization part of the dashboard
@callback(
    [Output("DD-x-axis-scatter", "options"),
     Output("DD-y-axis-scatter", "options"),
     Output("DD-colors-scatter", "options"),
     Output("DD-x-axis-box", "options"),
     Output("DD-y-axis-box", "options"),
     Output("DD-col-histo", "options"),
     Output("DD-col1-2Dhisto", "options"),
     Output("DD-col2-2Dhisto", "options"),],
    Input("selected-sheet-store", "data")
)
def fill_dropdowns(sheet):
    if not sheet:
        return [], [], [], [], [], [], [], [], 

    df = load_filtered_df_graph(sheet)

    options = get_column_dropdown_options(df)
    return  options, options, options, options, options, options, options, options


# @callback(
#     Output("DD-filtre-val-contour", "options"),
#     Input("DD-filtre-col-contour", "value"),
#     State("selected-sheet-store", "data"),
#     prevent_initial_call=True
# )
# def update_dropdown(selected_col, sheet):
#     if not sheet or not selected_col:
#         return []
#     df = load_filtered_df(sheet)
#     if selected_col == "System":
#         unique_values = ["flow", "batch"]
#         options = [{"label": str(value), "value": value} for value in unique_values if pd.notna(value)]
#         return options
#     unique_values = df[selected_col].unique()
#     options = [{"label": str(value), "value": value} for value in unique_values if pd.notna(value)]
#     return options