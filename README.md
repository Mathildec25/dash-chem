Test_pages/
│
├── app.py                          # Point d'entrée principal de l'application
│
├── results.xlsx                    # Fichier Excel contenant les données expérimentales
│
├── pages/
│   └── dashboard.py               # Enregistrement de la page principale ("Dashboard")
│
├── components/
│   ├── layout_display.py          # Contient la fonction create_dashboard_layout()
│   ├── sidebar.py                 # Gère la construction de la sidebar dynamique
│   └── Figures.py                 # Fonctions de visualisation : graph_scatter, graph_pie
│
├── callbacks/
│   ├── app_callbacks.py           # Callbacks globaux (toggle sidebar, sélection feuille)
│   ├── table_callbacks.py         # Callbacks de gestion du tableau interactif
│   └── graph_callbacks.py         # Callbacks de génération de graphiques (scatter/pie)
│
├── utils/
│   └── data_handling.py           # Fonctions de lecture / filtrage / colonnes du fichier Excel