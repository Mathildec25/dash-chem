# --- IMPORTS PRINCIPAUX ---
import dash
import dash_bootstrap_components as dbc
from dash import Input, Output, dcc, html, dash_table, State
from dash.dash_table.Format import Format
import pandas as pd

# --- IMPORTS LOCAUX ---
from callbacks.app_callbacks import register_app_callbacks    
from components.sidebar import generate_sidebar 
from callbacks import table_callbacks, graph_callbacks
               

# --- INITIALISATION DE L'APPLICATION DASH ---
app = dash.Dash(
    __name__,
    use_pages=True,                     
    suppress_callback_exceptions=True   
)

# Exposition du serveur Flask sous-jacent pour déploiement (ex: avec Gunicorn)
server = app.server

# --- CHARGEMENT DES FEUILLES EXCEL DISPONIBLES ---
excel_file = "results.xlsx"
sheets_names = pd.ExcelFile(excel_file).sheet_names  # Liste les noms de feuilles (expériences) à afficher dans le menu déroulant


# --- GÉNÉRATION DE LA BARRE LATÉRALE DYNAMIQUE ---
# Elle contient : un dropdown de sélection de feuille + des liens de navigation vers les pages
sidebar = generate_sidebar(sheets_names)

# --- CALLBACKS GLOBAUX ---
# Enregistre les callbacks liés à l’UI globale (changement de feuille, toggle du menu)
register_app_callbacks(app)


# --- LAYOUT PRINCIPAL ---
app.layout = dbc.Container([

    # Stockage local de la feuille Excel sélectionnée, accessible par toutes les pages
    dcc.Store(id="selected-sheet-store", storage_type='session'),

    # Gère l’URL de la page courante
    dcc.Location(id="url"),

    # Conteneur principal structuré en deux colonnes : sidebar + contenu de page
    dbc.Row(id="main-row", children=[
        
        # --- COLONNE 1 : BARRE LATÉRALE ---
        dbc.Col(
            id="sidebar-col",
            children=[sidebar],
            width='auto',  # S’adapte automatiquement à la largeur du contenu
        ),

        # --- COLONNE 2 : CONTENU PRINCIPAL ---
        dbc.Col(
            children=[
                # Bouton pour replier/déplier la sidebar
                html.Div([
                    dbc.Button("☰", id="toggle-btn", n_clicks=0, className="mb-2")
                ], style={"marginTop": "6px", "marginBottom": "0px"}),

                # Conteneur pour charger dynamiquement les pages Dash enregistrées
                dash.page_container
            ],
            width=True  # Prend le reste de la largeur disponible
        )
    ], style={
        "display": "flex",
        "flex-wrap": "nowrap",
        "height": "100vh",
        "margin-right": "12rem"  # Marge utilisée pour que le contenu ne chevauche pas la sidebar
    })
], fluid=True)  # `fluid=True` permet au conteneur de prendre toute la largeur de l'écran


# --- LANCEMENT DU SERVEUR LOCAL ---
if __name__ == '__main__':
    app.run(debug=True)

### Changements à apporter pour le déploiement :
