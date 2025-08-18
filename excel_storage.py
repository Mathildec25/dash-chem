import os
import dash
from dash import dcc, html, Input, Output, State, callback, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
import datetime

from config_path import EXCEL_FOLDER, TRACKING_FILE, TRACKING_FILENAME, DOMAIN_TRACKING_FILENAME, EXCLUDED_FILES
from domain_storage import DomainStorage, check_domain_availability

# Valid extensions
valid_extensions = ('.xlsx', '.xls', '.csv')

def get_existing_files():
    """Get existing files excluding tracking files"""
    if not os.path.exists(EXCEL_FOLDER):
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        return []
    
    return [
        f for f in os.listdir(EXCEL_FOLDER)
        if f.lower().endswith(valid_extensions)
        and f not in EXCLUDED_FILES
        and os.path.isfile(os.path.join(EXCEL_FOLDER, f))
    ]

def get_uploaded_excel_files():
    """Get Excel files from tracking file, excluding tracking files"""
    try:
        if os.path.exists(TRACKING_FILE):
            df = pd.read_excel(TRACKING_FILE, engine='openpyxl')
            if 'filename' in df.columns:
                # Filter out tracking files and ensure only Excel files
                excel_files = df["filename"][
                    df["filename"].str.lower().str.endswith(('.xlsx', '.xls')) &
                    (~df["filename"].isin(EXCLUDED_FILES))
                ].tolist()
                return excel_files
    except Exception as e:
        print(f"Error reading tracking file: {e}")
    
    # Fallback to direct file listing
    return [f for f in get_existing_files() if f.lower().endswith(('.xlsx', '.xls'))]

def update_tracking_file(filename):
    """Update tracking file with new filename"""
    allowed_extensions = ('.csv', '.xls', '.xlsx')
    
    # Don't track tracking files
    if filename in EXCLUDED_FILES:
        return dbc.Alert(
            f"Skipping tracking file: {filename}",
            color="info",
            is_open=True,
            duration=4000,
        )
    
    if not filename.lower().endswith(allowed_extensions):
        return dbc.Alert(
            f"Skipping unsupported file type: {filename}",
            color="warning",
            is_open=True,
            duration=4000,
        )
    
    try:
        # Ensure save folder exists
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        
        # Create or load tracking file
        if os.path.exists(TRACKING_FILE):
            df = pd.read_excel(TRACKING_FILE, engine='openpyxl')
        else:
            df = pd.DataFrame(columns=["filename"])

        # Add filename if not already present
        if filename not in df["filename"].values:
            new_row = pd.DataFrame([{"filename": filename}])
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_excel(TRACKING_FILE, index=False, engine='openpyxl')
            
        return None  # Success
    except Exception as e:
        return dbc.Alert(
            f"Failed to update tracking: {e}",
            color="danger",
            is_open=True,
            duration=4000,
        )

def parse_contents(contents, filename):
    """Parse uploaded file contents"""
    allowed_extensions = ('.csv', '.xls', '.xlsx')
    
    # Check if filename is a tracking file
    if filename in EXCLUDED_FILES:
        return dbc.Alert(
            f'Cannot upload tracking file: {filename}',
            color="danger", 
            is_open=True, 
            duration=4000
        )
    
    if not filename.lower().endswith(allowed_extensions):
        return dbc.Alert(
            'Unsupported file format. Please upload .xlsx, .xls, or .csv files.',
            color="danger", 
            is_open=True, 
            duration=4000
        )
    
    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        filepath = os.path.join(EXCEL_FOLDER, filename)

        # Check if file already exists
        if os.path.exists(filepath):
            return dbc.Alert(
                f"A file named '{filename}' already exists. Please rename or delete the existing file first.",
                color="warning", 
                is_open=True, 
                duration=6000
            )
        
        # Save the file
        os.makedirs(EXCEL_FOLDER, exist_ok=True)
        with open(filepath, 'wb') as f:
            f.write(decoded)

        # Validate file by trying to read it
        try:
            if filename.endswith('.csv'):
                pd.read_csv(io.StringIO(decoded.decode('utf-8')))
            else:
                pd.read_excel(io.BytesIO(decoded), engine='openpyxl')
        except Exception as e:
            # Remove the invalid file
            if os.path.exists(filepath):
                os.remove(filepath)
            return dbc.Alert(
                f'Error processing file: {e}', 
                color="danger", 
                is_open=True, 
                duration=4000
            )

        # Update tracking file
        tracking_result = update_tracking_file(filename)
        if tracking_result:  # Error occurred
            return tracking_result
            
        return html.Div([
            dbc.Alert(
                f"✅ Successfully uploaded: {filename}",
                color="success",
                is_open=True,
                duration=4000,
            ),
        ])

    except Exception as e:
        return dbc.Alert(
            f'Upload failed: {e}', 
            color="danger", 
            is_open=True, 
            duration=4000
        )

def get_excel_dropdown_options():
    """Get basic dropdown options for Excel files"""
    excel_files = get_uploaded_excel_files()
    return [{"label": f, "value": f} for f in excel_files]

def get_excel_dropdown_options_with_domain_status():
    """Get dropdown options with domain availability indicators"""
    excel_files = get_uploaded_excel_files()
    domain_availability = check_domain_availability()
    
    options = []
    for file in excel_files:
        has_domain = domain_availability.get(file, False)
        if has_domain:
            label = f"🔒 {file} (Domain Ready)"
        else:
            label = f"❌ {file} (No Domain)"
        options.append({"label": label, "value": file})
    
    return options

def cleanup_orphaned_domains():
    """Remove domain entries for Excel files that no longer exist"""
    try:
        # Get current Excel files
        current_excel_files = set(get_uploaded_excel_files())
        
        # Get tracked domains
        domains_df = DomainStorage.list_domains()
        
        if domains_df.empty:
            return []
        
        orphaned_domains = []
        for _, row in domains_df.iterrows():
            excel_file = row['excel_file']
            if excel_file not in current_excel_files and excel_file not in EXCLUDED_FILES:
                # This domain's Excel file no longer exists
                success, message = DomainStorage.delete_domain(excel_file)
                if success:
                    orphaned_domains.append(excel_file)
        
        return orphaned_domains
    except Exception as e:
        print(f"Error during cleanup: {e}")
        return []

def validate_excel_structure(file_path, expected_structure=None):
    """Validate Excel file structure against expected format"""
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        
        validation_result = {
            'valid': True,
            'message': 'File structure is valid',
            'columns': list(df.columns),
            'rows': len(df),
            'issues': []
        }
        
        # Check for empty file
        if df.empty:
            validation_result['issues'].append('File is empty')
        
        # Check for unnamed columns
        unnamed_cols = [col for col in df.columns if 'Unnamed:' in str(col)]
        if unnamed_cols:
            validation_result['issues'].append(f'Found unnamed columns: {unnamed_cols}')
        
        # If expected structure is provided, validate against it
        if expected_structure:
            expected_cols = expected_structure.get('columns', [])
            missing_cols = [col for col in expected_cols if col not in df.columns]
            extra_cols = [col for col in df.columns if col not in expected_cols]
            
            if missing_cols:
                validation_result['issues'].append(f'Missing expected columns: {missing_cols}')
            if extra_cols:
                validation_result['issues'].append(f'Extra columns found: {extra_cols}')
        
        # Set overall validity
        validation_result['valid'] = len(validation_result['issues']) == 0
        
        return validation_result
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'Validation failed: {str(e)}',
            'columns': [],
            'rows': 0,
            'issues': [str(e)]
        }

def get_file_info(filename):
    """Get detailed information about an Excel file"""
    try:
        file_path = os.path.join(EXCEL_FOLDER, filename)
        
        if not os.path.exists(file_path):
            return {'error': f'File not found: {filename}'}
        
        # Get file stats
        stat = os.stat(file_path)
        file_size = stat.st_size
        file_modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get Excel info
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            sheets = ['CSV Data']
        else:
            with pd.ExcelFile(file_path, engine='openpyxl') as xls:
                sheets = xls.sheet_names
                df = pd.read_excel(file_path, sheet_name=sheets[0], engine='openpyxl')
        
        # Check domain availability
        has_domain = DomainStorage.domain_exists(filename)
        domain_info = None
        
        if has_domain:
            success, domain, metadata = DomainStorage.load_domain(filename)
            if success:
                domain_info = {
                    'created_date': metadata.get('created_date'),
                    'parameters': len(metadata.get('parameters', [])),
                    'objectives': len(metadata.get('objectives', [])),
                    'extra_columns': len(metadata.get('extra_columns', []))
                }
        
        return {
            'filename': filename,
            'file_size': file_size,
            'file_modified': file_modified,
            'sheets': sheets,
            'columns': list(df.columns),
            'rows': len(df),
            'has_domain': has_domain,
            'domain_info': domain_info,
            'sample_data': df.head(3).to_dict('records') if not df.empty else []
        }
        
    except Exception as e:
        return {'error': f'Failed to get file info: {str(e)}'}

def create_file_summary_card(file_info):
    """Create a summary card for file information"""
    if 'error' in file_info:
        return dbc.Alert(file_info['error'], color="danger")
    
    # File basic info
    file_size_mb = file_info['file_size'] / (1024 * 1024)
    
    card_content = [
        html.H6(f"📄 {file_info['filename']}", className="card-title"),
        html.P([
            html.Small([
                f"Size: {file_size_mb:.2f} MB | ",
                f"Modified: {file_info['file_modified']} | ",
                f"Rows: {file_info['rows']}"
            ], className="text-muted")
        ]),
    ]
    
    # Domain status
    if file_info['has_domain']:
        domain_info = file_info['domain_info']
        card_content.append(
            dbc.Badge([
                "🔒 Domain Ready - ",
                f"P:{domain_info['parameters']} | O:{domain_info['objectives']}"
            ], color="success", className="mb-2")
        )
    else:
        card_content.append(
            dbc.Badge("❌ No Domain", color="warning", className="mb-2")
        )
    
    # Columns info
    columns_text = ", ".join(file_info['columns'][:5])
    if len(file_info['columns']) > 5:
        columns_text += f"... (+{len(file_info['columns']) - 5} more)"
    
    card_content.append(
        html.P([
            html.Strong("Columns: "),
            html.Small(columns_text, className="text-muted")
        ], className="mb-1")
    )
    
    return dbc.Card(
        dbc.CardBody(card_content),
        className="mb-2"
    )