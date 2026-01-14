from dash import callback, Input, Output, State, no_update, html, ALL
import dash_bootstrap_components as dbc
from utils.auto_fill_manager import AutoFillManager, format_alert_message
import base64
import os

# Instance globale du manager
auto_fill_manager = None


# ==================== CALLBACK 1 : GESTION DU MODAL ====================

@callback(
    Output("autofill-modal", "is_open"),
    [Input("open-autofill-modal", "n_clicks"),
     Input("close-autofill-modal", "n_clicks")],
    State("autofill-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_modal(open_clicks, close_clicks, is_open):
    """Ouvre/ferme le modal de configuration."""
    return not is_open


# ==================== CALLBACK 2 : UPLOAD DE FICHIER ====================

@callback(
    Output('result-file-path', 'value'),
    Input('upload-result-file', 'contents'),
    State('upload-result-file', 'filename'),
    prevent_initial_call=True
)
def handle_file_upload(contents, filename):
    """
    Gère l'upload du fichier de résultats.
    Le fichier est sauvegardé dans ./uploaded_results/
    """
    if contents is None:
        return no_update
    
    try:
        # Créer le dossier s'il n'existe pas
        upload_dir = "./uploaded_results"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Décoder le contenu
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)
        
        # Sauvegarder le fichier
        file_path = os.path.join(upload_dir, filename)
        with open(file_path, 'wb') as f:
            f.write(decoded)
        
        return file_path
    
    except Exception as e:
        print(f"❌ Error during upload: {e}")
        return no_update


# ==================== CALLBACK 3 : UPDATE INTERVALLE ====================

@callback(
    Output('file-check-interval', 'interval'),
    Output('file-check-interval', 'disabled'),
    Input('check-interval-input', 'value'),
    Input('auto-fill-switch', 'value'),
)
def update_interval_settings(check_interval, is_enabled):
    """Met à jour l'intervalle de vérification et active/désactive la surveillance."""
    if check_interval is None or check_interval < 1:
        check_interval = 2
    
    interval_ms = check_interval * 1000
    disabled = not is_enabled
    
    return interval_ms, disabled


# ==================== CALLBACK 4 : STATUT DE SURVEILLANCE ====================

@callback(
    Output('auto-fill-status', 'children'),
    Input('result-file-path', 'value'),
    Input('auto-fill-switch', 'value'),
)
def update_auto_fill_status(file_path, is_enabled):
    """Affiche le statut de la surveillance."""
    global auto_fill_manager
    
    if not is_enabled:
        return html.Span("⏸️ Disabled", className="text-secondary")
    
    if not file_path or file_path == "":
        return html.Span("⚠️ No file selected", className="text-warning")
    
    # Initialiser ou mettre à jour le manager
    try:
        if auto_fill_manager is None:
            auto_fill_manager = AutoFillManager(file_path)
        else:
            auto_fill_manager.update_file_path(file_path)
        
        status = auto_fill_manager.get_status()
        
        if not status['file_exists']:
            return html.Span([
                html.I(className="bi bi-exclamation-triangle me-1"),
                f"File not found"
            ], className="text-danger")
        
        return html.Span([
            html.I(className="bi bi-check-circle me-1"),
            "Active"
        ], className="text-success")
    
    except Exception as e:
        return html.Span(f"❌ Error: {str(e)}", className="text-danger")


# ==================== CALLBACK 5 : AUTO-FILL PRINCIPAL ====================

@callback(
    Output('experiment-datatable', 'data', allow_duplicate=True),
    Output('auto-fill-alert', 'children'),
    Output('auto-fill-alert', 'color'),
    Output('auto-fill-alert', 'is_open'),
    Input('file-check-interval', 'n_intervals'),
    State('experiment-datatable', 'data'),
    State({'type': 'objective-name', 'index': ALL}, 'value'),  # Pattern-matching pour les objectifs
    State('auto-fill-switch', 'value'),
    prevent_initial_call=True
)
def auto_fill_results(n_intervals, table_data, objective_names, is_enabled):
    """
    Callback principal qui remplit automatiquement les résultats.
    
    Cette version est adaptée à votre structure avec pattern-matching IDs.
    """
    global auto_fill_manager
    
    # Vérifications
    if not is_enabled or auto_fill_manager is None:
        return no_update, "", "info", False
    
    if not table_data:
        return no_update, "", "info", False
    
    # Extraire les noms des objectifs depuis le pattern-matching
    # Filtrer les None et les valeurs vides
    objective_columns = [name for name in objective_names if name]
    
    if not objective_columns:
        return no_update, "⚠️ No objectives defined", "warning", False
    
    # Vérifier et remplir
    try:
        update_info = auto_fill_manager.check_and_fill(table_data, objective_columns)
    except Exception as e:
        return no_update, f"❌ Error: {str(e)}", "danger", True
    
    if not update_info:
        return no_update, "", "info", False
    
    # Formater le message
    message, color, is_open = format_alert_message(update_info)
    
    if update_info['updated']:
        return update_info['new_data'], message, color, is_open
    else:
        return no_update, message, color, is_open


# ==================== CALLBACK 6 : RESET ====================

@callback(
    Output('auto-fill-status', 'children', allow_duplicate=True),
    Input('reset-autofill-btn', 'n_clicks'),
    prevent_initial_call=True
)
def reset_autofill(n_clicks):
    """Réinitialise le watcher (force une nouvelle lecture)."""
    global auto_fill_manager
    
    if auto_fill_manager:
        auto_fill_manager.reset()
        return html.Span([
            html.I(className="bi bi-arrow-clockwise me-1"),
            "Reset"
        ], className="text-info")
    
    return no_update


# ==================== CALLBACK 7 : INDICATEUR VISUEL SUR LE BOUTON ====================

@callback(
    Output('open-autofill-modal', 'color'),
    Output('open-autofill-modal', 'outline'),
    Input('auto-fill-switch', 'value'),
)
def update_button_appearance(is_enabled):
    """
    Change l'apparence du bouton selon l'état.
    
    - Activé : Bouton vert plein
    - Désactivé : Bouton gris outline
    """
    if is_enabled:
        return "success", False  # Bouton vert plein
    else:
        return "light", True     # Bouton gris outline
