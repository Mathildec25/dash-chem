import dash
from dash import callback, Input, Output, State, no_update, ctx, dcc, ALL
import dash_bootstrap_components as dbc
from dash import dcc, html
import plotly.express as px
import pandas as pd
import os
import base64
import io

SAVE_FOLDER = r"C:\Users\ThBrHu\Dev\dash-chem" # folder in the server
os.makedirs(SAVE_FOLDER, exist_ok=True)

TRACKING_FILE = os.path.join(SAVE_FOLDER, "Excel_names.xlsx") #File in the folder which tracks names
tracking_filename = os.path.basename(TRACKING_FILE) # save its name to not include it in the dropdown

# Valid extensions
valid_extensions = ('.xlsx', '.xls', '.csv')
existing_files = [
    f for f in os.listdir(SAVE_FOLDER)
    if f.lower().endswith(valid_extensions)
    and f != tracking_filename
    and os.path.isfile(os.path.join(SAVE_FOLDER, f))
]

# Create tracking file if not already existing
if not os.path.exists(TRACKING_FILE):
    df = pd.DataFrame({"filename": existing_files})
    df.to_excel(TRACKING_FILE, index=False)
else:
    df = pd.read_excel(TRACKING_FILE)
    tracked_files = df["filename"].tolist()

    # Add missing files
    new_files = [f for f in existing_files if f not in tracked_files]
    if new_files:
        df = pd.concat([df, pd.DataFrame({"filename": new_files})], ignore_index=True)
        df.to_excel(TRACKING_FILE, index=False)

def get_uploaded_excel_files():
    if os.path.exists(TRACKING_FILE):
        df = pd.read_excel(TRACKING_FILE) # read the tracking file
        return df["filename"][df["filename"].str.endswith(('.xlsx', '.xls'))].tolist() # Only return excel files (CSV later???)
    return []

@callback(
    Output('sheets-DD', 'children'),
    Output('text-DD-2', 'style'),
    Output('redirec-button', 'style'),
    Output('delete-excel-button', 'style'), 
    Input('excels-DD', 'value'),
    Input({'type': 'sheet-dropdown', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def update_dropdown_and_buttons(selected_excel, sheet_values):
    text_dd2_style = {"display": "none"}
    button_style = {"display": "none"}
    delete_button_style = {"display": "none"}  

    if selected_excel is None:
        return None, text_dd2_style, button_style, delete_button_style

    delete_button_style = {"display": "inline-block", "marginTop": "12px"}  

    text_dd2_style = {
        "display": "block",
        "fontSize": "20px",
        "textAlign": "left",
        "marginTop": "12px"
    }

    excel_path = os.path.join(SAVE_FOLDER, selected_excel)

    # Gather sheets names from the selected file
    try:
        if selected_excel.endswith(('.xls', '.xlsx')):
            with pd.ExcelFile(excel_path) as xls:  # use context manager
                sheet_names = xls.sheet_names
        elif selected_excel.endswith('.csv'):
            sheet_names = [f"{selected_excel}"]
        else:
            return html.Div([dbc.Alert(
                f"Unsupported file type: {selected_excel}",
                id="alert-file-reading",
                color="danger",
                is_open=True,
                duration=4000,
            )]), text_dd2_style, button_style, delete_button_style
    except Exception as e:
        return html.Div([dbc.Alert(
            f"Error reading file: {e}",
            id="alert-file-reading",
            color="danger",
            is_open=True,
            duration=4000,
        )]), text_dd2_style, button_style, delete_button_style
    
    # Gather a value for the dropdown if available
    current_sheet_value = sheet_values[0] if sheet_values else None

    # Create the sheet dropdown
    sheet_dropdown = dcc.Dropdown(
        id={'type': 'sheet-dropdown', 'index': selected_excel},
        options=[{"label": name, "value": name} for name in sheet_names],
        placeholder="Select a sheet..." if len(sheet_names) > 1 else None,
        value=current_sheet_value or (sheet_names[0] if len(sheet_names) == 1 else None),
    )

    # Show buttons if a sheet is selected or if there is only one sheet available 
    if current_sheet_value or (len(sheet_names) == 1 and not sheet_values):
        button_style = {
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "padding": "80px"
        }

    return sheet_dropdown, text_dd2_style, button_style, delete_button_style


def update_tracking_file(filename):
    allowed_extensions = ('.csv', '.xls', '.xlsx')
    if not filename.lower().endswith(allowed_extensions):
        return dbc.Alert(
             f"Skipping unsupported file type: {filename}",
            id="alert-file-reading",
            color="warning",
            is_open=True,
            duration=4000,
        )

    # If the tracking file doesn't exist, create it
    if not os.path.exists(TRACKING_FILE):
        df = pd.DataFrame(columns=["filename"])
        df.to_excel(TRACKING_FILE, index=False)

    # Load the existing tracking file
    df = pd.read_excel(TRACKING_FILE)

    # Add the filename only if it’s not already there
    if filename not in df["filename"].values:
        df.loc[len(df)] = {"filename": filename}
        df.to_excel(TRACKING_FILE, index=False)

# Function to decode files which have been uploaded 
def parse_contents(contents, filename):
    allowed_extensions = ('.csv', '.xls', '.xlsx')
    if not filename.lower().endswith(allowed_extensions):
        return dbc.Alert(
            'Unsupported file format.',
            id="alert-file-unsupported",
            color="danger",
            is_open=True,
            duration=4000,
        )
    
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    filepath = os.path.join(SAVE_FOLDER, filename) # ✅ Save to your custom path

    if os.path.exists(filepath):
        return dbc.Alert(
             f"A file named '{filename}' already exists. Please rename your file before uploading.",
            id="alert-file-exists",
            color="warning",
            is_open=True,
            duration=4000,
        )

    with open(filepath, 'wb') as f:
        f.write(decoded)

    # Load into DataFrame (for display in Dash)
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        return dbc.Alert(
            f'Error processing file: {e}',
            id="alert-file-error",
            color="danger",
            is_open=True,
            duration=4000,
        )
    
    update_tracking_file(filename)

    return html.Div([
        dbc.Alert(
            f"Saved file: {filename}",
            id="alert-file-saved",
            is_open=True,
            duration=4000,
        ),
    ])

@callback(
    Output('excels-DD', 'options'),
    Input('output-data-upload', 'children')  # Trigger après un upload
)
def refresh_excel_dropdown(_):
    files = get_uploaded_excel_files()
    return [{"label": f, "value": f} for f in files]

@callback(
    Output('output-data-upload', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def update_output(list_of_contents, list_of_names):
    if list_of_contents is not None:
        if isinstance(list_of_names, str):
            list_of_names = [list_of_names]

        children = []
        for contents, name in zip(list_of_contents, list_of_names):
            if contents and ',' in contents:
                children.append(parse_contents(contents, name))
            else:
                children.append(html.Div(f"Skipping invalid file: {name}"))

        return children
    
# Callback to delete and Excel file
@callback(
    Output('excels-DD', 'value', allow_duplicate=True),
    Output('excels-DD', 'options', allow_duplicate=True),
    Output('output-data-upload', 'children', allow_duplicate=True),
    Input('delete-excel-button', 'n_clicks'),
    State('excels-DD', 'value'),
    prevent_initial_call=True
)
def delete_excel_file(n_clicks, selected_file):
    if not selected_file:
        return dash.no_update, dash.no_update, dbc.Alert(
            "No file selected to delete.",
            color="warning",
            is_open=True,
            duration=4000
        )

    file_path = os.path.join(SAVE_FOLDER, selected_file)

    try:
        if os.path.exists(file_path):
            os.remove(file_path)

        # Supprimer du fichier de suivi
        if os.path.exists(TRACKING_FILE):
            df = pd.read_excel(TRACKING_FILE)
            df = df[df["filename"] != selected_file]
            df.to_excel(TRACKING_FILE, index=False)

        # Mettre à jour les options du dropdown
        new_options = [{"label": f, "value": f} for f in get_uploaded_excel_files()]

        return None, new_options, dbc.Alert(
            f"Deleted: {selected_file}",
            color="success",
            is_open=True,
            duration=4000
        )

    except Exception as e:
        return dash.no_update, dash.no_update, dbc.Alert(
            f"Error deleting file: {e}",
            color="danger",
            is_open=True,
            duration=4000
        )
    
@callback(
    Output("output", "children"),
    Input("multi-text", "value")
)
def update_output(value):
    words = [w.strip() for w in value.replace(",", " ").split() if w.strip()]
    return f"You entered {len(words)} words: {words}"


# # Open modal to create the excel file and name it
# @callback(
#     Output("excel-modal", "is_open"),
#     [Input("create-excel-button", "n_clicks"),
#      Input("confirm-create-excel", "n_clicks"),
#      Input("cancel-create-excel", "n_clicks")],
#     [State("excel-modal", "is_open")]
# )
# def toggle_modal(n_create, n_confirm, n_cancel, is_open):
#     triggered_id = ctx.triggered_id
#     if triggered_id in ["create-excel-button", "cancel-create-excel", "confirm-create-excel"]:
#         return not is_open
#     return is_open


# @callback(
#     Output("excels-DD", "options", allow_duplicate=True),
#     Output("excels-DD", "value", allow_duplicate=True),
#     Output("output-data-upload", "children", allow_duplicate=True),
#     Input("confirm-create-excel", "n_clicks"),
#     State("new-excel-name", "value"),
#     prevent_initial_call='initial_duplicate'
# )
# def create_new_excel(n_clicks, name):
#     if not name:
#         return dash.no_update, dash.no_update, dbc.Alert(
#             "Please enter a name for the Excel file.",
#             color="danger",
#             duration=3000,
#             is_open=True,
#         )

#     filename = name.strip()
#     if not filename.endswith('.xlsx'):
#         filename += '.xlsx'

#     filepath = os.path.join(SAVE_FOLDER, filename)

#     if os.path.exists(filepath):
#         return dash.no_update, dash.no_update, dbc.Alert(
#             f"A file named '{filename}' already exists.",
#             color="warning",
#             duration=3000,
#             is_open=True,
#         )

#     try:
#         # Create a new Excel
#         pd.DataFrame().to_excel(filepath, index=False)
#         update_tracking_file(filename)
#     except Exception as e:
#         return dash.no_update, dash.no_update, dbc.Alert(
#             f"Error creating file: {e}",
#             color="danger",
#             duration=3000,
#             is_open=True,
#         )

#     files = get_uploaded_excel_files()
#     return (
#         [{"label": f, "value": f} for f in files],
#         filename,
#         dbc.Alert(
#             f"Created new Excel file: {filename}",
#             color="success",
#             duration=3000,
#             is_open=True,
#         ),
#     )