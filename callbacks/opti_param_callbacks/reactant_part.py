import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os



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