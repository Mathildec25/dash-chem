"""
Gestionnaire d'auto-fill AMÉLIORÉ - Version flexible
Fonctionne avec N'IMPORTE QUELS noms d'objectifs

À placer dans : utils/auto_fill_manager.py (REMPLACER l'ancien)
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import pandas as pd
from utils.file_watcher import ResultFileWatcher


class AutoFillManager:
    """
    Gestionnaire centralisé pour l'auto-fill des résultats d'expériences.
    
    VERSION AMÉLIORÉE avec mapping flexible :
    - Matching intelligent par mots-clés
    - Fallback : remplissage dans l'ordre
    - Fonctionne avec n'importe quels noms d'objectifs
    """
    
    def __init__(self, file_path: str):
        """
        Initialise le gestionnaire d'auto-fill.
        
        Args:
            file_path: Chemin vers le fichier de résultats à surveiller
        """
        self.watcher = ResultFileWatcher(file_path)
        self.last_result = None
        
    def update_file_path(self, file_path: str):
        """
        Met à jour le chemin du fichier surveillé.
        
        Args:
            file_path: Nouveau chemin du fichier
        """
        self.watcher = ResultFileWatcher(file_path)
        self.last_result = None
    
    def check_and_fill(
        self, 
        table_data: List[Dict[str, Any]],
        objective_columns: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Vérifie s'il y a de nouveaux résultats et remplit automatiquement 
        la première ligne vide du tableau.
        
        Args:
            table_data: Liste de dictionnaires représentant les lignes du tableau
            objective_columns: Liste des noms de colonnes d'objectifs
            
        Returns:
            Dict avec les infos de mise à jour, ou None si pas de changement
        """
        # Vérifier s'il y a de nouveaux résultats
        new_result = self.watcher.check_for_updates()
        
        if new_result is None:
            return None
        
        # Éviter les doublons
        if self._is_duplicate(new_result):
            return None
        
        self.last_result = new_result
        
        # Trouver la première ligne avec des objectifs vides
        row_to_fill = self._find_empty_row(table_data, objective_columns)
        
        if row_to_fill is None:
            return {
                'updated': False,
                'new_data': table_data,
                'result': new_result,
                'message': 'No empty row found'
            }
        
        # Remplir les résultats dans la ligne
        updated_data = self._fill_row(
            table_data, 
            row_to_fill, 
            new_result, 
            objective_columns
        )
        
        return {
            'updated': True,
            'row_index': row_to_fill,
            'new_data': updated_data,
            'result': new_result,
            'message': f'Row {row_to_fill + 1} filled successfully'
        }
    
    def _is_duplicate(self, new_result: Dict[str, Any]) -> bool:
        """Vérifie si le résultat est un doublon du dernier traité."""
        if self.last_result is None:
            return False
        
        return self.last_result.get('timestamp') == new_result.get('timestamp')
    
    def _find_empty_row(
        self, 
        table_data: List[Dict[str, Any]], 
        objective_columns: List[str]
    ) -> Optional[int]:
        """Trouve l'index de la première ligne avec tous les objectifs vides."""
        if not table_data or not objective_columns:
            return None
        
        for i, row in enumerate(table_data):
            # Vérifier si tous les objectifs sont vides
            all_empty = all(
                self._is_empty_value(row.get(col))
                for col in objective_columns
            )
            
            if all_empty:
                return i
        
        return None
    
    def _is_empty_value(self, value: Any) -> bool:
        """Vérifie si une valeur est considérée comme vide."""
        if value is None:
            return True
        if value == '':
            return True
        if isinstance(value, str) and value.lower() in ['nan', 'none', 'null']:
            return True
        if isinstance(value, float):
            import math
            return math.isnan(value)
        return False
    
    def _fill_row(
        self,
        table_data: List[Dict[str, Any]],
        row_index: int,
        results: Dict[str, Any],
        objective_columns: List[str]
    ) -> List[Dict[str, Any]]:
        """Remplit une ligne du tableau avec les résultats."""
        # Mapper les résultats aux colonnes
        result_mapping = self._map_results_to_columns(results, objective_columns)
        
        # Remplir la ligne
        for col_name, value in result_mapping.items():
            if col_name in table_data[row_index]:
                table_data[row_index][col_name] = value
        
        return table_data
    
    def _map_results_to_columns(
        self,
        results: Dict[str, Any],
        objective_columns: List[str]
    ) -> Dict[str, float]:
        """
        MAPPING FLEXIBLE AMÉLIORÉ
        
        Stratégie à 3 niveaux :
        1. Matching intelligent par mots-clés (insensible à la casse)
        2. Correspondance exacte (insensible à la casse)
        3. Fallback : Remplissage dans l'ordre
        
        Args:
            results: Résultats parsés du fichier (ex: {'conversion': 85.5, 'TON': 42.3})
            objective_columns: Noms des colonnes d'objectifs (ex: ['Yield (%)', 'Space-Time Yield'])
            
        Returns:
            Dictionnaire {nom_colonne: valeur}
        """
        mapping = {}
        used_results = set()  # Pour tracker quels résultats ont été utilisés
        
        # === NIVEAU 1 : MATCHING INTELLIGENT PAR MOTS-CLÉS ===
        
        keyword_mappings = {
            # Conversion / Yield
            'conversion': ['conversion', 'conv', 'yield'],
            'yield': ['yield', 'conversion', 'conv'],
            
            # TON / Turnover
            'TON': ['ton', 'turnover', 'turn'],
            'turnover': ['ton', 'turnover', 'turn'],
            
            # Selectivity
            'selectivity': ['selectivity', 'selectivite', 'sel'],
            
            # Purity
            'purity': ['purity', 'purete', 'pure'],
            
            # STY (Space-Time Yield)
            'sty': ['sty', 'space', 'time', 'yield'],
            'space_time_yield': ['sty', 'space', 'time', 'yield'],
            
            # Rate
            'rate': ['rate', 'vitesse', 'speed'],
            
            # Productivity
            'productivity': ['productivity', 'productivite', 'prod'],
            
            # Ee (Enantiomeric Excess)
            'ee': ['ee', 'enantiomeric', 'excess'],
            
            # Dr (Diastereomeric Ratio)
            'dr': ['dr', 'diastereomeric', 'ratio'],
        }
        
        for col_name in objective_columns:
            col_lower = col_name.lower()
            
            # Chercher dans les résultats
            for result_key, result_value in results.items():
                if result_key in used_results:
                    continue
                
                result_lower = result_key.lower()
                
                # Vérifier si on a un mapping de mots-clés pour ce résultat
                keywords_to_check = keyword_mappings.get(result_lower, [result_lower])
                
                # Vérifier si un des mots-clés est dans le nom de la colonne
                for keyword in keywords_to_check:
                    if keyword in col_lower:
                        if isinstance(result_value, (int, float)):
                            mapping[col_name] = round(result_value, 2)
                            used_results.add(result_key)
                            break
                
                if col_name in mapping:
                    break
        
        # === NIVEAU 2 : CORRESPONDANCE EXACTE (insensible à la casse) ===
        
        for col_name in objective_columns:
            if col_name in mapping:
                continue  # Déjà mappé au niveau 1
            
            col_lower = col_name.lower().strip()
            
            for result_key, result_value in results.items():
                if result_key in used_results:
                    continue
                
                result_lower = result_key.lower().strip()
                
                # Correspondance exacte
                if col_lower == result_lower:
                    if isinstance(result_value, (int, float)):
                        mapping[col_name] = round(result_value, 2)
                        used_results.add(result_key)
                        break
        
        # === NIVEAU 3 : FALLBACK - REMPLISSAGE DANS L'ORDRE ===
        
        # Si certains objectifs n'ont pas été mappés, remplir dans l'ordre
        unmapped_columns = [col for col in objective_columns if col not in mapping]
        unused_results = [
            (key, val) for key, val in results.items() 
            if key not in used_results and isinstance(val, (int, float))
        ]
        
        for i, col_name in enumerate(unmapped_columns):
            if i < len(unused_results):
                result_key, result_value = unused_results[i]
                mapping[col_name] = round(result_value, 2)
                used_results.add(result_key)
                print(f"📋 Fallback mapping: {result_key} → {col_name}")
        
        return mapping
    
    def get_status(self) -> Dict[str, Any]:
        """Retourne le statut actuel de l'auto-fill."""
        watcher_status = self.watcher.get_status()
        return {
            'file_path': watcher_status['file_path'],
            'file_exists': watcher_status['exists'],
            'last_modified': watcher_status['last_modified'],
            'last_result': self.last_result,
            'monitoring': True
        }
    
    def reset(self):
        """Réinitialise le gestionnaire."""
        self.watcher.reset()
        self.last_result = None


# === FONCTION UTILITAIRE POUR DASH ===

def format_alert_message(update_info: Dict[str, Any]) -> tuple:
    """Formate le message d'alerte pour Dash."""
    if not update_info:
        return "", "info", False
    
    if not update_info['updated']:
        return f"⚠️ {update_info['message']}", "warning", True
    
    # Construire le message de succès
    result = update_info['result']
    row_num = update_info['row_index'] + 1
    
    parts = []
    for key, value in result.items():
        if key not in ['timestamp', 'source_file'] and isinstance(value, (int, float)):
            parts.append(f"{key}: {value:.1f}")
    
    result_text = ", ".join(parts) if parts else "Results"
    message = f"✅ Row {row_num} filled: {result_text}"
    
    return message, "success", True


# === TESTS ===

if __name__ == "__main__":
    print("🧪 Test du AutoFillManager AMÉLIORÉ\n")
    
    # Créer un fichier de test
    with open("test_results.txt", "w") as f:
        f.write("Yield: 87.3%\nSpace-Time Yield: 45.2\n")
    
    # Initialiser le manager
    manager = AutoFillManager("test_results.txt")
    
    # Simuler des données de tableau avec des noms d'objectifs différents
    table_data = [
        {'Exp': 1, 'Temp': 120, 'Time': 30, 'Yield (%)': None, 'STY (g/L/h)': None},
        {'Exp': 2, 'Temp': 140, 'Time': 45, 'Yield (%)': None, 'STY (g/L/h)': None},
    ]
    
    objective_columns = ['Yield (%)', 'STY (g/L/h)']
    
    # Tester l'auto-fill
    print("📊 Tableau avant:")
    for row in table_data:
        print(f"   {row}")
    
    print("\n🔄 Vérification de nouveaux résultats...")
    update_info = manager.check_and_fill(table_data, objective_columns)
    
    if update_info and update_info['updated']:
        print(f"\n✅ {update_info['message']}")
        print("\n📊 Tableau après:")
        for row in update_info['new_data']:
            print(f"   {row}")
        
        message, color, is_open = format_alert_message(update_info)
        print(f"\n💬 Message d'alerte: {message}")
    else:
        print("\n⚠️ Aucun résultat détecté ou aucune ligne vide")
    
    # Nettoyer
    import os
    os.remove("test_results.txt")
    
    print("\n✅ Test terminé!")
    print("\n📋 EXEMPLES DE MAPPINGS SUPPORTÉS :")
    print("   Fichier → Colonne tableau")
    print("   'conversion' → 'Conversion', 'Conv', 'Yield'")
    print("   'TON' → 'TON', 'Turnover Number'")
    print("   'selectivity' → 'Selectivity (%)', 'Sel'")
    print("   'yield' → 'Yield (%)', 'Conversion'")
    print("   'sty' → 'STY', 'Space-Time Yield'")
    print("   'purity' → 'Purity (%)', 'Pure'")
    print("   + FALLBACK : Remplissage dans l'ordre si pas de correspondance")