"""
Domain creation and Excel generation with sampling
Main callback for creating domains and generating initial experiments
"""

import dash
from dash import callback, Input, Output, State, ALL, no_update
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html
import pandas as pd
import os
import uuid

from domain_storage import DomainStorage
from utils.BoFire import create_bofire_domain_from_store
from utils.bofire_optimization import sampling, kmeans_sampling
from config_path import EXCEL_FOLDER, TRACKING_FILE


@callback(
    Output('create-domain-btn', 'disabled'),
    [Input({'type': 'parameter-name', 'index': ALL}, 'value'),
     Input({'type': 'objective-name', 'index': ALL}, 'value'),
     Input('project-name-store', 'data')],
    prevent_initial_call=True
)
def enable_button(param_names, obj_names, project_name):
    """Enable button when minimum requirements are met (no visible warnings)"""
    
    # Check project name
    if not project_name or not project_name.strip():
        return True
    
    # Check at least one parameter
    valid_params = [p for p in param_names if p and p.strip()]
    if not valid_params:
        return True
    
    # Check at least one objective
    valid_objs = [o for o in obj_names if o and o.strip()]
    if not valid_objs:
        return True
    
    return False  # Enable button


@callback(
    [Output('current-excel-file', 'data'),
     Output('url', 'pathname', allow_duplicate=True),
     Output('validation-alert', 'children'),
     Output('validation-alert', 'is_open')],
    Input('create-domain-btn', 'n_clicks'),
    [State('project-name-store', 'data'),
     State({'type': 'parameter-name', 'index': ALL}, 'id'),
     State({'type': 'parameter-name', 'index': ALL}, 'value'),
     State({'type': 'parameter-type', 'index': ALL}, 'value'),
     State({'type': 'parameter-min', 'index': ALL}, 'id'),
     State({'type': 'parameter-min', 'index': ALL}, 'value'),
     State({'type': 'parameter-max', 'index': ALL}, 'id'),
     State({'type': 'parameter-max', 'index': ALL}, 'value'),
     State({'type': 'parameter-categories', 'index': ALL}, 'id'),
     State({'type': 'parameter-categories', 'index': ALL}, 'value'),
     State({'type': 'parameter-step', 'index': ALL}, 'id'), 
     State({'type': 'parameter-step', 'index': ALL}, 'value'),
     State({'type': 'objective-name', 'index': ALL}, 'id'),
     State({'type': 'objective-name', 'index': ALL}, 'value'),
     State({'type': 'objective-direction', 'index': ALL}, 'value'),
     State({'type': 'objective-lower', 'index': ALL}, 'value'),
     State({'type': 'objective-upper', 'index': ALL}, 'value'),
     State({'type': 'extra-column-name', 'index': ALL}, 'id'),
     State({'type': 'extra-column-name', 'index': ALL}, 'value'),
     State('starting-sampling-DD', 'value'),
     State('nb-sampling-points', 'value'),
     State('solvent-config-store', 'data'),
     State('base-config-store', 'data'),
     State('constraints-store', 'data')],
    prevent_initial_call=True
)
def create_domain_and_excel(n_clicks, project_name, 
                           param_ids, param_names, param_types, 
                           min_ids, param_mins, max_ids, param_maxs, 
                           cat_ids, param_cats,
                           step_ids, param_steps,  
                           obj_ids, obj_names, obj_directions, obj_lowers, obj_uppers,
                           extra_ids, extra_names,
                           sampling_method, nb_points,
                           solvent_config, base_config, constraints_config):
    """
    Main callback: Create domain, generate Excel with sampling, and redirect
    """
    
    if not n_clicks:
        raise PreventUpdate
    
    try:
        # ===== 1. BUILD PARAMETERS =====
        parameters = []
        
        # Build lookup dictionaries
        cats_dict = {}
        mins_dict = {}
        maxs_dict = {}
        steps_dict = {}
        
        if cat_ids and param_cats:
            for cid, cval in zip(cat_ids, param_cats):
                cats_dict[cid['index']] = cval
        
        if min_ids and param_mins:
            for mid, mval in zip(min_ids, param_mins):
                mins_dict[mid['index']] = mval
        
        if max_ids and param_maxs:
            for mid, mval in zip(max_ids, param_maxs):
                maxs_dict[mid['index']] = mval
        
        if step_ids and param_steps:
            for sid, sval in zip(step_ids, param_steps):
                if sval is not None:
                    steps_dict[sid['index']] = sval
        
        print(f"🔍 param_ids: {[p['index'] for p in param_ids] if param_ids else []}")
        print(f"🔍 param_names: {param_names}")
        print(f"🔍 param_types: {param_types}")
        print(f"🔍 min_ids: {[m['index'] for m in min_ids] if min_ids else []}")
        print(f"🔍 param_mins: {param_mins}")
        print(f"🔍 max_ids: {[m['index'] for m in max_ids] if max_ids else []}")
        print(f"🔍 param_maxs: {param_maxs}")
        print(f"🔍 cat_ids: {[c['index'] for c in cat_ids] if cat_ids else []}")
        print(f"🔍 param_cats: {param_cats}")
        print(f"🔍 solvent_config: {solvent_config}")
        print(f"🔍 base_config: {base_config}")
        print(f"🔍 constraints_config: {constraints_config}")
        print(f"🔍 cats_dict: {cats_dict}")
        print(f"🔍 mins_dict: {mins_dict}")
        print(f"🔍 maxs_dict: {maxs_dict}")
        print(f"🔍 steps_dict: {steps_dict}")
        
        for i, (pid, name, ptype) in enumerate(zip(param_ids, param_names, param_types)):
            if not name or not name.strip():
                continue
            
            idx = pid['index']
            
            if ptype == 'float':
                lb = mins_dict.get(idx)
                ub = maxs_dict.get(idx)
                
                if lb is None or ub is None:
                    alert = dbc.Alert(f"❌ Parameter '{name}' missing min or max value", color="danger")
                    return no_update, no_update, alert, True
                
                type_info = {'range': [float(lb), float(ub)]}
                step = steps_dict.get(idx)
                if step is not None:
                    type_info['step'] = float(step)
                
                parameters.append({
                    'id': idx,
                    'name': name.strip(),
                    'type': 'float',
                    'type_info': type_info
                })
            
            elif ptype == 'int':
                cats = cats_dict.get(idx)
                if not cats:
                    alert = dbc.Alert(f"❌ Discrete parameter '{name}' needs values (e.g., 1, 2, 3)", color="danger")
                    return no_update, no_update, alert, True
                
                values = []
                for v in str(cats).split(','):
                    v = v.strip()
                    if v:
                        try:
                            values.append(float(v))
                        except ValueError as e:
                            alert = dbc.Alert(f"❌ Discrete parameter '{name}' has invalid values: {str(e)}", color="danger")
                            return no_update, no_update, alert, True
                
                if not values:
                    alert = dbc.Alert(f"❌ Discrete parameter '{name}' needs at least one value", color="danger")
                    return no_update, no_update, alert, True
                
                parameters.append({
                    'id': idx,
                    'name': name.strip(),
                    'type': 'int',
                    'type_info': {'range': values}
                })
            
            elif ptype == 'cat':
                # Categorical: comma-separated values
                cats = cats_dict.get(idx)
                if not cats:
                    alert = dbc.Alert(f"❌ Categorical parameter '{name}' needs values (e.g., A, B, C)", color="danger")
                    return no_update, no_update, alert, True
                
                # Split by comma and clean
                values = [v.strip() for v in str(cats).split(',') if v.strip()]
                if not values:
                    alert = dbc.Alert(f"❌ Categorical parameter '{name}' needs at least one value", color="danger")
                    return no_update, no_update, alert, True
                
                parameters.append({
                    'id': idx,
                    'name': name.strip(),
                    'type': 'cat',
                    'type_info': {'values': values}
                })
        
        if not parameters:
            alert = dbc.Alert("❌ At least one valid parameter is required", color="danger")
            return no_update, no_update, alert, True
        
        print(f"✅ Built {len(parameters)} parameters")
        
        # ===== 2. BUILD OBJECTIVES =====
        objectives = []
        
        for i, (oid, name, direction) in enumerate(zip(obj_ids, obj_names, obj_directions)):
            if not name or not name.strip() or not direction:
                continue
            
            idx = oid['index']
            lower = obj_lowers[i] if i < len(obj_lowers) else 0.0
            upper = obj_uppers[i] if i < len(obj_uppers) else 1.0
            
            objectives.append({
                'id': idx,
                'name': name.strip(),
                'direction': direction,
                'lower_bound': lower if lower is not None else 0.0,
                'upper_bound': upper if upper is not None else 1.0
            })
        
        if not objectives:
            alert = dbc.Alert("❌ At least one valid objective is required", color="danger")
            return no_update, no_update, alert, True
        
        print(f"✅ Built {len(objectives)} objectives")
        
        # ===== 3. BUILD EXTRA COLUMNS =====
        extra_columns = []
        
        if extra_ids and extra_names:
            for eid, name in zip(extra_ids, extra_names):
                if name and name.strip():
                    extra_columns.append({
                        'id': eid['index'],
                        'name': name.strip()
                    })
        
        # Add Point type column automatically
        extra_columns.append({
            'id': str(uuid.uuid4()),
            'name': 'Point type'
        })
        
        print(f"✅ Built {len(extra_columns)} extra columns")
        
        # ===== 4. CREATE DOMAIN =====
        discretization_config = {}
        
        for param in parameters:
            param_id = param.get('id')
            param_name = param.get('name')
            param_type = param.get('type')
            
            # Only discretize float parameters that have a step value
            if param_type == 'float' and param_id in steps_dict:
                step_value = steps_dict[param_id]
                discretization_config[param_name] = float(step_value)
                print(f"   🎯 Will discretize '{param_name}' with step={step_value}")
        
        if discretization_config:
            print(f"📊 Discretization config: {discretization_config}")
        else:
            print(f"ℹ️ No discretization configured (all parameters continuous)")
        
        # Create the domain with discretization
        try:
            domain = create_bofire_domain_from_store(
                parameters, 
                objectives,
                solvent_config=solvent_config,
                base_config=base_config,
                constraints_config=constraints_config,
                discretization_config=discretization_config
            )
            print("✅ BoFire domain created with discretization and native constraints")
            
            # Afficher un résumé
            n_discrete = sum(1 for f in domain.inputs.features if hasattr(f, 'values'))
            n_continuous = sum(1 for f in domain.inputs.features if hasattr(f, 'bounds'))
            n_categorical = sum(1 for f in domain.inputs.features 
                               if not hasattr(f, 'values') and not hasattr(f, 'bounds'))
            
            print(f"   📊 Domain: {n_continuous} continuous, {n_discrete} discrete, "
                  f"{n_categorical} categorical features")
            
            if domain.constraints:
                n_constraints = len(domain.constraints.constraints)
                print(f"   🔒 {n_constraints} native constraint(s) active")
        
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"💥 Domain creation error:\n{error_trace}")
            alert = dbc.Alert(f"❌ Failed to create domain: {str(e)}", color="danger")
            return no_update, no_update, alert, True

        
        # ===== 5. GENERATE EXCEL FILENAME =====
        excel_name = project_name.strip()
        if not excel_name.endswith('.xlsx'):
            excel_name += '.xlsx'
        
        file_path = os.path.join(EXCEL_FOLDER, excel_name)
        
        # ===== 6. PERFORM SAMPLING =====
        sampled_data = None
        
        if sampling_method and sampling_method != 'none' and nb_points and int(nb_points) > 0:
            try:
                if sampling_method == 'kmeans':
                    sampled_data = kmeans_sampling(
                        domain=domain,
                        nb_points=int(nb_points),
                        constraints_config=constraints_config,
                    )
                    print(f"✅ Generated {len(sampled_data)} sampling points using k-Means")
                else:
                    # Map method names to SamplingMethodEnum values
                    method_map = {
                        'random': 'UNIFORM',
                        'latin_hypercube': 'LHS',
                        'sobol': 'SOBOL'
                    }
                    
                    method_key = method_map.get(sampling_method, 'LHS')
                    sampled_data = sampling(domain, method_key, int(nb_points))
                    print(f"✅ Generated {len(sampled_data)} sampling points using {method_key}")
            except Exception as e:
                import traceback
                print(f"Sampling error: {traceback.format_exc()}")
                alert = dbc.Alert(f"❌ Sampling failed: {str(e)}", color="danger")
                return no_update, no_update, alert, True
            
        # ===== 7. BUILD EXCEL DATAFRAME =====
        # Column order: Extra columns → Parameters → Objectives
        all_columns = []
        
        # Add extra columns
        for col in extra_columns:
            all_columns.append({
                'name': col['name'],
                'type': 'extra'
            })
        
        # Add parameters
        for param in parameters:
            all_columns.append({
                'name': param['name'],
                'type': 'parameter',
                'data': param
            })
        
        # Add objectives
        for obj in objectives:
            all_columns.append({
                'name': obj['name'],
                'type': 'objective'
            })
        
        # Create DataFrame
        if sampled_data is not None and not sampled_data.empty:
            num_rows = len(sampled_data)
            df_excel = pd.DataFrame(index=range(num_rows))
            
            # Fill columns
            for col_info in all_columns:
                col_name = col_info['name']
                
                if col_info['type'] == 'extra':
                    if col_name == 'Point type':
                        df_excel[col_name] = 'Init'
                    else:
                        df_excel[col_name] = ''
                
                elif col_info['type'] == 'parameter':
                    if col_name in sampled_data.columns:
                        values = sampled_data[col_name].values
                        
                        # Round floats
                        param_def = col_info.get('data', {})
                        if param_def.get('type') == 'float':
                            df_excel[col_name] = [round(v, 2) if pd.notna(v) else v for v in values]
                        else:
                            df_excel[col_name] = values
                    else:
                        df_excel[col_name] = ''
                
                elif col_info['type'] == 'objective':
                    df_excel[col_name] = ''
        
        else:
            # No sampling - create empty row
            headers = [col['name'] for col in all_columns]
            df_excel = pd.DataFrame(columns=headers)
            
            empty_row = {}
            for col_info in all_columns:
                if col_info['name'] == 'Point type':
                    empty_row[col_info['name']] = 'BO'
                else:
                    empty_row[col_info['name']] = ''
            
            df_excel = pd.concat([df_excel, pd.DataFrame([empty_row])], ignore_index=True)
        
        # ===== 8. SAVE EXCEL FILE =====
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Experiments')
            
            # Format headers
            from openpyxl.styles import Font, PatternFill, Alignment
            worksheet = writer.sheets['Experiments']
            
            for i, cell in enumerate(worksheet[1]):
                cell.font = Font(bold=True, color="FFFFFF")
                cell.alignment = Alignment(horizontal='center', vertical='center')
                
                col_info = all_columns[i]
                if col_info['type'] == 'extra':
                    if col_info['name'] == 'Point type':
                        cell.fill = PatternFill(start_color="FF6B35", end_color="FF6B35", fill_type="solid")
                    else:
                        cell.fill = PatternFill(start_color="6C757D", end_color="6C757D", fill_type="solid")
                elif col_info['type'] == 'parameter':
                    cell.fill = PatternFill(start_color="007BFF", end_color="007BFF", fill_type="solid")
                elif col_info['type'] == 'objective':
                    cell.fill = PatternFill(start_color="28A745", end_color="28A745", fill_type="solid")
        
        print(f"✅ Excel file saved: {file_path}")
        
        # ===== 9. SAVE DOMAIN =====
        success, message = DomainStorage.save_domain(
            excel_name=excel_name,
            domain=domain,
            parameters=parameters,
            objectives=objectives,
            extra_columns=extra_columns,
            metadata={
                'sampling_method': sampling_method or 'none',
                'nb_points': nb_points if nb_points else 0,
                'column_order': [col['name'] for col in all_columns],
                'parameter_names': [p['name'] for p in parameters],
                'objective_names': [o['name'] for o in objectives],
                'extra_column_names': [c['name'] for c in extra_columns],
                'solvent_config': solvent_config,
                'base_config': base_config,
                'constraints_config': constraints_config,
            }
        )
        
        if not success:
            alert = dbc.Alert(f"❌ Domain save failed: {message}", color="danger")
            return no_update, no_update, alert, True
        
        print("✅ Domain saved successfully")
        
        # ===== 10. UPDATE TRACKING =====
        if os.path.exists(TRACKING_FILE):
            df_track = pd.read_excel(TRACKING_FILE, engine='openpyxl')
        else:
            df_track = pd.DataFrame(columns=['filename'])
        
        if excel_name not in df_track['filename'].values:
            df_track = pd.concat([df_track, pd.DataFrame([{'filename': excel_name}])], ignore_index=True)
            df_track.to_excel(TRACKING_FILE, index=False, engine='openpyxl')
        
        # ===== 11. SUCCESS - REDIRECT =====
        alert = dbc.Alert([
            html.I(className="bi bi-check-circle-fill me-2"),
            "✅ Domain and Excel created successfully! Redirecting..."
        ], color="success")
        
        return excel_name, '/Opt-run', alert, True
    
    except Exception as e:
        import traceback
        print(f"💥 Error in domain creation:")
        print(traceback.format_exc())
        
        alert = dbc.Alert([
            html.H6("❌ Creation Failed", className="alert-heading"),
            html.P(str(e))
        ], color="danger")
        
        return no_update, no_update, alert, True