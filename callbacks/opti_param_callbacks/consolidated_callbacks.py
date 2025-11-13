"""
Consolidated callbacks for parameter configuration page
Handles the complete flow: domain creation → sampling → Excel generation → redirect
"""

import dash
from dash import callback, Input, Output, State, ALL, no_update
from dash.exceptions import PreventUpdate

from domain_storage import create_domain_and_excel_with_storage


@callback(
    [Output('current-excel-file', 'data', allow_duplicate=True),
     Output('url', 'pathname', allow_duplicate=True)],
    Input('create-domain-btn', 'n_clicks'),
    [State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-type', 'index': ALL}, 'value'),
     State({'type': 'parameter-type-specific-lower', 'index': ALL}, 'value'),
     State({'type': 'parameter-type-specific-upper', 'index': ALL}, 'value'),
     State({'type': 'objective-name', 'index': ALL}, 'id'),
     State({'type': 'objective-name', 'index': ALL}, 'value'),
     State({'type': 'objective-direction', 'index': ALL}, 'value'),
     State({'type': 'objective-lower-bound', 'index': ALL}, 'value'),
     State({'type': 'objective-upper-bound', 'index': ALL}, 'value'),
     State({'type': 'extra-column-name', 'index': ALL}, 'id'),
     State({'type': 'extra-column-name', 'index': ALL}, 'value'),
     State('project-name-store', 'data'),
     State('starting-sampling-DD', 'value'),
     State('nb-sampling-points', 'value')],
    prevent_initial_call=True
)
def create_domain_and_redirect(n_clicks, 
                               param_ids, param_names, param_types, param_lowers, param_uppers,
                               obj_ids, obj_names, obj_directions, obj_lowers, obj_uppers,
                               extra_ids, extra_names,
                               project_name, sampling_method, num_samples):
    """
    Consolidated callback that:
    1. Validates all inputs
    2. Creates parameters and objectives structures
    3. Creates domain with sampling
    4. Generates Excel file
    5. Redirects to optimization page
    """
    
    if not n_clicks:
        raise PreventUpdate
    
    # === 1. VALIDATE PROJECT NAME ===
    if not project_name or not project_name.strip():
        print("❌ No project name provided")
        return no_update, no_update
    
    # === 2. BUILD PARAMETERS ===
    parameters = []
    param_dict = {}
    
    # Create mapping of parameter data by index
    for pid, name, ptype, lower, upper in zip(param_ids, param_names, param_types, param_lowers, param_uppers):
        if not name or not name.strip():
            continue
            
        idx = pid['index']
        param_dict[idx] = {
            'id': idx,
            'name': name.strip(),
            'type': ptype if ptype else 'float',
            'lower': lower,
            'upper': upper
        }
    
    # Convert to proper parameter structure
    for idx, param in param_dict.items():
        ptype = param['type']
        
        if ptype == 'float':  # Continuous
            if param['lower'] is None or param['upper'] is None:
                print(f"⚠️ Parameter '{param['name']}' missing bounds")
                continue
            parameters.append({
                'id': idx,
                'name': param['name'],
                'type': 'float',
                'type_info': {
                    'range': [float(param['lower']), float(param['upper'])]
                }
            })
        
        elif ptype == 'int':  # Discrete
            if param['lower'] is None or param['upper'] is None:
                print(f"⚠️ Parameter '{param['name']}' missing bounds")
                continue
            parameters.append({
                'id': idx,
                'name': param['name'],
                'type': 'int',
                'type_info': {
                    'range': list(range(int(param['lower']), int(param['upper']) + 1))
                }
            })
        
        elif ptype == 'cat':  # Categorical
            # For categorical, bounds are treated as comma-separated values
            if param['lower'] is None:
                print(f"⚠️ Categorical parameter '{param['name']}' missing values")
                continue
            values = [v.strip() for v in str(param['lower']).split(',')]
            parameters.append({
                'id': idx,
                'name': param['name'],
                'type': 'cat',
                'type_info': {
                    'values': values
                }
            })
    
    if not parameters:
        print("❌ No valid parameters defined")
        return no_update, no_update
    
    print(f"✅ Built {len(parameters)} parameters")
    
    # === 3. BUILD OBJECTIVES ===
    objectives = []
    obj_dict = {}
    
    # Create mapping of objective data by index
    for oid, name, direction, lower, upper in zip(obj_ids, obj_names, obj_directions, obj_lowers, obj_uppers):
        if not name or not name.strip() or not direction:
            continue
            
        idx = oid['index']
        obj_dict[idx] = {
            'id': idx,
            'name': name.strip(),
            'direction': direction,
            'lower_bound': lower if lower is not None else 0.0,
            'upper_bound': upper if upper is not None else 1.0
        }
    
    # Convert to objectives list
    for idx, obj in obj_dict.items():
        objectives.append({
            'id': idx,
            'name': obj['name'],
            'direction': obj['direction'],
            'lower_bound': obj['lower_bound'],
            'upper_bound': obj['upper_bound']
        })
    
    if not objectives:
        print("❌ No valid objectives defined")
        return no_update, no_update
    
    print(f"✅ Built {len(objectives)} objectives")
    
    # === 4. BUILD EXTRA COLUMNS ===
    extra_columns = []
    if extra_ids and extra_names:
        for eid, name in zip(extra_ids, extra_names):
            if name and name.strip():
                extra_columns.append({
                    'id': eid['index'],
                    'name': name.strip()
                })
    
    print(f"✅ Built {len(extra_columns)} extra columns")
    
    # === 5. CREATE DOMAIN AND EXCEL WITH SAMPLING ===
    print(f"🚀 Creating domain with sampling: {sampling_method}, {num_samples} points")
    
    try:
        message, excel_filename = create_domain_and_excel_with_storage(
            n_clicks=1,  # Signal we want to create
            parameters=parameters,
            objectives=objectives,
            extra_columns=extra_columns,
            excel_name=project_name,
            sampling_method=sampling_method,
            nb_points=num_samples
        )
        
        if excel_filename:
            print(f"✅ Domain and Excel created successfully: {excel_filename}")
            # Redirect to optimization page with the new Excel file
            return excel_filename, '/Opt-run'
        else:
            print(f"❌ Domain creation failed: {message}")
            return no_update, no_update
            
    except Exception as e:
        print(f"💥 Error creating domain: {e}")
        import traceback
        traceback.print_exc()
        return no_update, no_update