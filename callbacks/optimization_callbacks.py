import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os

from dash import Input, Output, State, callback, html, ctx
import dash

## MARCHE PAS POUR DRAWING PART
@callback(
    Output("smiles-output", "children"),
    Input("smiles-store", "data")
)
def display_smiles(stored_smiles):
    if not stored_smiles or not isinstance(stored_smiles, dict):
        raise PreventUpdate
    return [
        html.Div(f"{reactant}: {smiles_list[0]}")
        for reactant, smiles_list in stored_smiles.items()
    ]

## PARAMETERS PART ##

# Update layout dynamically
@callback(
    Output({'type': 'parameter-type-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_type_dropdown(name):
    if not name:
        return ""

    return html.Div([
        dbc.Label("Select the type"),
        dcc.Dropdown(
            id={'type': 'parameter-type', 'index': ctx.triggered_id['index']},
            options=[
                {"label": "Integer", "value": "int"},
                {"label": "Continuous", "value": "float"},
                {"label": "Categorical", "value": "cat"},
                {"label": "Ordinal", "value": "ord"},
                {"label": "Chemical", "value": "chem"},
            ],
            placeholder="Select type",
            style={"fontSize": "18px"},
        )
    ])

# Add a new parameter block
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Input("add-para-button", "n_clicks"),
    State("parameter-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_new_parameter(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_block = html.Div(
        id={'type': 'parameter-block', 'index': new_id},
        children=[
            dbc.Row(
                children=[
                    dbc.Col([
                        dbc.Label("Name of the parameter"),
                        dbc.Input(
                            id={'type': 'parameter-name', 'index': new_id},
                            placeholder="Type here...",
                            type="text",
                            size="sm",
                            style={"fontSize": "18px"}
                        ),
                    ], width=5),
                    dbc.Col([
                        html.Div(id={'type': 'parameter-type-container', 'index': new_id})
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-parameter', 'index': new_id},
                            color="danger",
                            size="sm"
                        )
                    ], width=2)
                ],
                style={"marginBottom": "10px"}
            ),
            html.Div(id={'type': 'parameter-type-specific-container', 'index': new_id})
        ]
    )

    return current_children + [new_block]

# Add the component according to the type selected
@callback(
    Output({'type': 'parameter-type-specific-container', 'index': MATCH}, 'children'),
    Input({'type': 'parameter-type', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def render_type_specific_component(selected_type):
    if not selected_type:
        return ""

    if selected_type in ['int', 'float']:
        # RangeSlider with reasonable default min/max and marks
        return dbc.Row([
            dbc.Label("Select range:", style={"marginBottom": "5px"}),
            dcc.RangeSlider(
                min=-200, max=200, step=1 if selected_type=='int' else 0.1,
                marks={i: str(i) for i in range(-200, 200, 20)},
                tooltip={"placement": "bottom", "always_visible": True},
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']}
            )
        ], style={"marginBottom": "15px"})

    elif selected_type in ['cat', 'chem']:
        # Upload component
        return dbc.Row([
            dbc.Label("Upload values:", style={"marginBottom": "5px"}),
            dcc.Upload(
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                children=html.Div([
                    'Drag and Drop or ',
                    html.A('Select Files')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'marginBottom': '15px'
                },
                multiple=True
            )
        ])

    elif selected_type == 'ord':
        # Input box for ordinal values
        return dbc.Row([
            dbc.Label("Enter ordinal values:", style={"marginBottom": "5px"}),
            dbc.Input(
                id={'type': 'parameter-type-specific', 'index': ctx.triggered_id['index']},
                placeholder="Enter values separated by commas",
                type="text",
                style={"marginBottom": "15px"}
            )
        ])

    else:
        return ""
    
# Save parameters part information described by the user / auto-update display if one is removed
@callback(
    Output("parameter-store", "data"),
    Output("parameter-display", "children"),
    Input("save-parameters-btn", "n_clicks"),
    Input({"type": "parameter-name", "index": ALL}, "value"),
    Input({"type": "parameter-type", "index": ALL}, "value"),
    Input({"type": "parameter-type-specific", "index": ALL}, "value"),
    State("parameter-store", "data"),
    prevent_initial_call=False
)
def update_parameters(n_clicks, names, types, type_values, current_store):
    triggered_id = ctx.triggered_id

    # Build the parameters list from current inputs
    parameters = []
    for name, typ, typ_val in zip(names, types, type_values):
        if name and typ:
            parameters.append({
                "name": name,
                "type": typ,
                "type_info": typ_val
            })

    # Prepare the display (always update)
    display = html.Pre(
        json.dumps(parameters, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    # Update store data only if Save button triggered this callback
    if triggered_id == "save-parameters-btn" and n_clicks:
        return parameters, display
    else:
        # If triggered by other inputs (e.g., parameter changes), update display but keep store as-is
        return dash.no_update, display

# Delete parametre block and saved information
@callback(
    Output("parameter-container", "children", allow_duplicate=True),
    Output("parameter-store", "data", allow_duplicate=True),
    Input({'type': 'delete-parameter', 'index': ALL}, 'n_clicks'),
    State("parameter-container", "children"),
    State("parameter-store", "data"),
    prevent_initial_call=True
)
def delete_parameter(n_clicks_list, container_children, stored_data):
    if not any(n_clicks_list):
        raise PreventUpdate

    # Find which delete button was clicked
    triggered_id = ctx.triggered_id
    if not triggered_id:
        raise PreventUpdate

    index_to_delete = triggered_id['index']

    # Remove the block with that index from container children
    new_children = []
    for child in container_children:
        if child['props']['id'].get('index') != index_to_delete:
            new_children.append(child)

    # Also update the store data
    new_store = []
    for param in stored_data:
        if not param['name'].endswith(str(index_to_delete)):
            new_store.append(param)

    return new_children, new_store
    
## OBJECTIVES PART ##

# Add a new objective block
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Input("add-objective-button", "n_clicks"),
    State("objective-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_new_objective(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_block = html.Div(
        id={'type': 'objective-block', 'index': new_id},
        children=[
            dbc.Row(
                children=[
                    dbc.Col([
                        dbc.Label("Name of the objective"),
                        dbc.Input(
                            id={'type': 'objective-name', 'index': new_id},
                            placeholder="Type here...",
                            type="text",
                            size="sm",
                            style={"fontSize": "18px"}
                        ),
                    ], width=5),
                    dbc.Col([
                        html.Div(id={'type': 'objective-direction-container', 'index': new_id})
                    ], width=5),
                    dbc.Col([
                        dbc.Button(
                            "✕",
                            id={'type': 'delete-objective-btn', 'index': new_id},
                            color="danger",
                            size="sm",
                        )
                    ], width=2),
                ],
                style={"marginBottom": "10px"}
            )
        ])
        
    return current_children + [new_block]

# Display the dropdown to choose Min/Max
@callback(
    Output({'type': 'objective-direction-container', 'index': MATCH}, 'children'),
    Input({'type': 'objective-name', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def show_objective_direction(name):
    if not name:
        return ""

    return html.Div([
        dbc.Label("Select direction"),
        dcc.Dropdown(
            id={'type': 'objective-direction', 'index': ctx.triggered_id['index']},
            options=[
                {"label": "Minimize", "value": "min"},
                {"label": "Maximize", "value": "max"},
            ],
            placeholder="Choose direction",
        )
    ])

# Delete objective block and saved information
@callback(
    Output("objective-container", "children", allow_duplicate=True),
    Output("objective-store", "data", allow_duplicate=True),
    Input({'type': 'delete-objective-btn', 'index': ALL}, 'n_clicks'),
    State("objective-container", "children"),
    State("objective-store", "data"),
    prevent_initial_call=True
)
def delete_objective(n_clicks_list, current_children, stored_data):
    ctx_trigger = ctx.triggered_id
    if not ctx_trigger:
        raise dash.exceptions.PreventUpdate
    
    # Check if any delete button was actually clicked
    if not any(n_clicks_list) or all(clicks is None for clicks in n_clicks_list):
        raise dash.exceptions.PreventUpdate

    delete_index = ctx_trigger['index']

    # Remove the block from the layout
    new_children = [
        child for child in current_children
        if child['props']['id']['index'] != delete_index
    ]

    # Remove the corresponding objective from the store
    new_store = [
        obj for obj in stored_data
        if obj.get('id') != delete_index  # Assuming you store the ID
    ]

    return new_children, new_store

# Save objectives part information described by the user
@callback(
    Output("objective-store", "data"),
    Output("objective-display", "children"),
    Input("save-objectives-btn", "n_clicks"),
    Input({"type": "objective-name", "index": ALL}, "value"),
    Input({"type": "objective-direction", "index": ALL}, "value"),
    State("objective-store", "data"),
    prevent_initial_call=False
)
def update_objectives(n_clicks, names, directions, current_store):
    triggered_id = ctx.triggered_id

    objectives = []
    for name, direction in zip(names, directions):
        if name and direction:
            objectives.append({
                "name": name,
                "direction": direction
            })

    display = html.Pre(
        json.dumps(objectives, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    # Only update store if Save button clicked
    if triggered_id == "save-objectives-btn" and n_clicks:
        return objectives, display
    else:
        # Update display only
        return dash.no_update, display
    
## EXTRA COLUMNS PART ##

# Add a new other column block
@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Input("add-extra-column-button", "n_clicks"),
    State("extra-column-container", "children"),
    prevent_initial_call="initial_duplicate"
)
def add_extra_column(n_clicks, current_children):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    new_id = str(uuid.uuid4())

    new_row = dbc.Row([
        dbc.Col([
            dbc.Input(
                id={'type': 'extra-column-name', 'index': new_id},
                placeholder="Enter column name...",
                type="text",
                style={"marginBottom": "8px"}
            )
        ], width=10),
        dbc.Col([
            dbc.Button(
                "✕",
                id={'type': 'delete-extra-column-btn', 'index': new_id},
                color="danger",
                size="sm",
                style={"marginBottom": "8px"}
            )
        ], width=2),
    ], style={"marginBottom": "5px"})

    return current_children + [new_row]

@callback(
    Output("extra-column-container", "children", allow_duplicate=True),
    Output("extra-columns-store", "data", allow_duplicate=True),
    Input({'type': 'delete-extra-column-btn', 'index': ALL}, 'n_clicks'),
    State("extra-column-container", "children"),
    State("extra-columns-store", "data"),
    prevent_initial_call=True
)
def delete_extra_column(n_clicks_list, current_children, stored_data):
    ctx_trigger = ctx.triggered_id
    if not ctx_trigger:
        raise dash.exceptions.PreventUpdate
    
    # Check if any delete button was clicked
    if not any(n_clicks_list) or all(click is None for click in n_clicks_list):
        raise dash.exceptions.PreventUpdate

    delete_index = ctx_trigger["index"]
    new_children = []

    for child in current_children:
        try:
            # Loop through Cols inside the Row
            row_cols = child["props"]["children"]
            found = False

            for col in row_cols:
                col_children = col["props"].get("children", [])
                # Force into list if it's a single component
                if isinstance(col_children, dict):
                    col_children = [col_children]

                for comp in col_children:
                    comp_id = comp["props"].get("id")
                    if isinstance(comp_id, dict) and comp_id.get("type") == "delete-extra-column-btn" and comp_id.get("index") == delete_index:
                        found = True
                        break

                if found:
                    break

            if not found:
                new_children.append(child)
        except Exception as e:
            print("Skipping a child due to error:", e)
            new_children.append(child)

    # Store remains untouched (will be saved again on save button)
    return new_children, stored_data

# Save extra columns part information described by the user
@callback(
    Output("extra-columns-store", "data", allow_duplicate=True),
    Output("extra-columns-display", "children", allow_duplicate=True),
    Input("save-extra-columns-btn", "n_clicks"),
    Input({"type": "extra-column-name", "index": ALL}, "value"),
    State("extra-columns-store", "data"),
    prevent_initial_call=True
)
def save_extra_columns(n_clicks, column_names, current_store):
    triggered_id = ctx.triggered_id

    columns = []
    for name in column_names:
        if name:
            columns.append({
                "name": name
            })

    display = html.Pre(
        json.dumps(columns, indent=2),
        style={"whiteSpace": "pre-wrap", "fontSize": "14px"}
    )

    # Only update store if Save button clicked
    if triggered_id == "save-extra-columns-btn" and n_clicks:
        return columns, display
    else:
        # Update display only
        return dash.no_update, display

# Save Excel name 
@callback(
    Output("excel-name-store", "data"),
    Output("excel-confirmation", "children"),
    Input("save-excel-name-btn", "n_clicks"),
    State("excel-name-input", "value"),
    prevent_initial_call=True
)
def save_excel_name(n_clicks, filename):
    if not filename:
        raise dash.exceptions.PreventUpdate

    return filename, f"✔️ Saved: '{filename}'"

# Display the create excel button when the name is saved
@callback(
    Output("create-excel-btn-container", "style"),
    Input("excel-name-store", "data"),
    prevent_initial_call=True
)
def show_create_excel_button(excel_name):
    if excel_name:
        return {"display": "block"}
    return {"display": "none"}



### NEED CHANGEMENT BEFORE DEPLOY IT ###
SAVE_FOLDER = r"C:\Users\ThBrHu\Dev\dash-chem"
TRACKING_FILE = os.path.join(SAVE_FOLDER, "Excel_names.xlsx")

# Create the Excel from all store components 
@callback(
    Output("excel-create-message", "children"),
    Input("create-excel-btn", "n_clicks"),
    State("extra-columns-store", "data"),
    State("parameter-store", "data"),
    State("objective-store", "data"),
    State("excel-name-store", "data"),
    prevent_initial_call=True
)
def create_excel_file(n_clicks, extra_cols, parameters, objectives, excel_name):
    if not excel_name:
        return "❌ Please provide a valid Excel file name."

    # Ensure .xlsx extension
    if not excel_name.endswith(".xlsx"):
        excel_name += ".xlsx"

    file_path = os.path.join(SAVE_FOLDER, excel_name)

    headers = []

    # 1. Extra columns: expect a list of strings
    if extra_cols :
        headers.extend([col.get("name") for col in extra_cols])

    # 2. Parameters: expect list of dicts with "name"
    if parameters:
        headers.extend([param.get("name") for param in parameters])

    # 3. Objectives: expect list of dicts with "name"
    if objectives:
        headers.extend([obj.get("name") for obj in objectives])

    if not headers:
        return "⚠️ No columns to write into Excel."

    df = pd.DataFrame(columns=headers)

    try:
        # Save Excel file
        df.to_excel(file_path, index=False, engine='openpyxl')

        # Update tracking file if needed
        if os.path.exists(TRACKING_FILE):
            df_tracking = pd.read_excel(TRACKING_FILE)
        else:
            df_tracking = pd.DataFrame(columns=["filename"])

        if excel_name not in df_tracking["filename"].values:
            df_tracking.loc[len(df_tracking)] = [excel_name]
            df_tracking.to_excel(TRACKING_FILE, index=False)

        return f"✅ Excel file '{excel_name}' created successfully with {len(headers)} columns."

    except Exception as e:
        return f"❌ Failed to create Excel file: {str(e)}"
