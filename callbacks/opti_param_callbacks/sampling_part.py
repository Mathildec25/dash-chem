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

# Create/Store domain and excel callback with proper error handling
@callback(
    Output("current-excel-file", "data"),
    Input("create-domain-btn", "n_clicks"),
    [State("parameter-store", "data"),
     State("objective-store", "data"),
     State("extra-columns-store", "data"),
     State("project-name-store", "data"),
     State("starting-sampling-DD", "value"),
     State("nb-sampling-points", "value")],
    prevent_initial_call=True,
    suppress_callback_exceptions=True  # This is crucial to handle missing components
)
def create_domain_and_excel_callback(n_clicks, parameters, objectives, extra_columns, 
                                    excel_name, sampling_method, nb_points):
    """Create domain and Excel file with sampling when button is clicked"""
    
    if not n_clicks:
        raise PreventUpdate
    
    # Handle case where sampling components might not exist (e.g., on different pages)
    try:
        # Call the domain creation function with error handling
        message, excel_filename = create_domain_and_excel_with_storage(
            n_clicks=n_clicks,
            parameters=parameters,
            objectives=objectives,
            extra_columns=extra_columns,
            excel_name=excel_name,
            sampling_method=sampling_method,  # Will be None if component doesn't exist
            nb_points=nb_points  # Will be None if component doesn't exist
        )
        
        # Return the excel filename for storage
        # If creation failed, excel_filename will be None
        return excel_filename
        
    except Exception as e:
        # If there's any error (including missing components), just return None
        print(f"Domain creation error: {e}")
        raise PreventUpdate