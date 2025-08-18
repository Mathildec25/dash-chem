import dash
from dash import callback, Input, Output, State, MATCH, ALL, dash_table, html, no_update, dcc, ctx
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from utils.data_handling import load_filtered_df, get_columns, get_column_dropdown_options
import pandas as pd
import uuid
import json
import os
from excel_storage import EXCEL_FOLDER, TRACKING_FILE, TRACKING_FILENAME  

from domain_storage import (
    DomainStorage, 
    create_domain_and_excel_with_storage, 
    check_domain_availability,
    prepare_experiments_from_excel_data, 
    load_experiments_from_excel_file
)

# 2. Replace your existing create_domain_and_excel callback with this:
@callback(
        [Output("domain-create-message", "children"),
         Output("current-excel-file", "data")],
        Input("run-BO-btn", "n_clicks"),
        [State("parameter-store", "data"),
         State("objective-store", "data"),
         State("extra-columns-store", "data"),
         State("project-name-store", "data"),
         State("starting-sampling-DD", "value"),
         State("nb-sampling-points", "value")],
        prevent_initial_call=True
    )
def create_domain_and_excel_callback(n_clicks, parameters, objectives, extra_columns, 
                                    excel_name, sampling_method, nb_points):
    """Create domain and Excel file with sampling when button is clicked"""
    
    if not n_clicks:
        return dash.no_update, dash.no_update
    
    # Call the domain creation function
    message, excel_filename = create_domain_and_excel_with_storage(
        n_clicks=n_clicks,
        parameters=parameters,
        objectives=objectives,
        extra_columns=extra_columns,
        excel_name=excel_name,
        sampling_method=sampling_method,
        nb_points=nb_points
    )
    
    # If successful, the message will contain success info and excel_filename will be set
    # If failed, message will contain error info and excel_filename will be None
    
    return message, excel_filename