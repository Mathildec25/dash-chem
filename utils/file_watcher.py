"""
Module de surveillance de fichier pour intégration automatique des résultats
dans la GUI d'optimisation bayésienne.

À placer dans : utils/file_watcher.py
"""

import os
import time
from datetime import datetime
from pathlib import Path
import json
import re
from typing import Optional, Dict, Any


class ResultFileWatcher:
    """
    Surveille un fichier texte contenant les résultats d'analyses
    et extrait automatiquement les valeurs pour mise à jour de la GUI.
    
    Usage:
        watcher = ResultFileWatcher("./results.txt")
        result = watcher.check_for_updates()
        if result:
            print(f"Nouvelle conversion: {result['conversion']}")
    """
    
    def __init__(self, file_path: str, check_interval: int = 2):
        """
        Initialise le surveillant de fichier.
        
        Args:
            file_path: Chemin vers le fichier texte à surveiller
            check_interval: Intervalle de vérification en secondes (non utilisé ici)
        """
        self.file_path = Path(file_path)
        self.check_interval = check_interval
        self.last_modified = 0
        self.last_content = ""
        
    def check_for_updates(self) -> Optional[Dict[str, Any]]:
        """
        Vérifie si le fichier a été modifié et extrait les nouvelles données.
        
        Returns:
            Dictionnaire avec les résultats si modification détectée, None sinon
            Exemple: {'conversion': 85.5, 'TON': 42.3, 'timestamp': '...'}
        """
        if not self.file_path.exists():
            return None
        
        # Vérifier si le fichier a été modifié
        current_modified = os.path.getmtime(self.file_path)
        
        if current_modified <= self.last_modified:
            return None
        
        self.last_modified = current_modified
        
        # Lire et parser le contenu
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Éviter de traiter le même contenu deux fois
            if content == self.last_content:
                return None
            
            self.last_content = content
            
            # Extraire les résultats du fichier
            result = self.parse_result_file(content)
            
            if result:
                result['timestamp'] = datetime.now().isoformat()
                result['source_file'] = str(self.file_path)
                
            return result
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return None
    
    def parse_result_file(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Parse le contenu du fichier texte pour extraire les résultats.
        Supporte plusieurs formats de fichiers texte.
        
        Formats supportés:
        - "Conversion: 85.5%"
        - "conversion = 72.3"
        - JSON: {"conversion": 88.4}
        - Et plus...
        
        Args:
            content: Contenu du fichier texte
            
        Returns:
            Dictionnaire avec les résultats extraits
        """
        results = {}
        content_lower = content.lower()
        
        # === PATTERN 1: Conversion/Yield ===
        conversion_patterns = [
            r'conversion[:\s]+([0-9.]+)\s*%?',
            r'yield[:\s]+([0-9.]+)\s*%?',
            r'conversion\s*=\s*([0-9.]+)',
            r'yield\s*=\s*([0-9.]+)',
            r'conv[:\s]+([0-9.]+)\s*%?',
        ]
        
        for pattern in conversion_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    conversion = float(match.group(1))
                    results['conversion'] = conversion
                    break
                except ValueError:
                    continue
        
        # === PATTERN 2: TON (Turnover Number) ===
        ton_patterns = [
            r'ton[:\s]+([0-9.]+)',
            r'turnover\s+number[:\s]+([0-9.]+)',
            r'ton\s*=\s*([0-9.]+)',
        ]
        
        for pattern in ton_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    ton = float(match.group(1))
                    results['TON'] = ton
                    break
                except ValueError:
                    continue
        
        # === PATTERN 3: Sélectivité ===
        selectivity_patterns = [
            r'selectivity[:\s]+([0-9.]+)\s*%?',
            r'selectivite[:\s]+([0-9.]+)\s*%?',
            r'sel[:\s]+([0-9.]+)\s*%?',
        ]
        
        for pattern in selectivity_patterns:
            match = re.search(pattern, content_lower)
            if match:
                try:
                    selectivity = float(match.group(1))
                    results['selectivity'] = selectivity
                    break
                except ValueError:
                    continue
        
        # === PATTERN 4: Format JSON ===
        try:
            json_data = json.loads(content)
            if isinstance(json_data, dict):
                # Chercher les clés communes
                for key in ['conversion', 'yield', 'Conversion', 'Yield']:
                    if key in json_data:
                        results['conversion'] = float(json_data[key])
                
                for key in ['TON', 'ton', 'turnover_number']:
                    if key in json_data:
                        results['TON'] = float(json_data[key])
                
                for key in ['selectivity', 'Selectivity']:
                    if key in json_data:
                        results['selectivity'] = float(json_data[key])
        except json.JSONDecodeError:
            pass
        
        # === PATTERN 5: Format clé-valeur (key=value ou key: value) ===
        for line in content.split('\n'):
            line = line.strip()
            if '=' in line or ':' in line:
                parts = re.split('[=:]', line, 1)
                if len(parts) == 2:
                    key = parts[0].strip().lower()
                    value = parts[1].strip().rstrip('%')
                    
                    # Essayer de convertir en float
                    try:
                        float_value = float(value)
                        
                        if 'conversion' in key or 'yield' in key or 'conv' in key:
                            results['conversion'] = float_value
                        elif 'ton' in key or 'turnover' in key:
                            results['TON'] = float_value
                        elif 'selectivity' in key or 'sel' in key:
                            results['selectivity'] = float_value
                    except ValueError:
                        pass
        
        return results if results else None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retourne le statut actuel du watcher.
        
        Returns:
            Dictionnaire avec les informations de statut
        """
        return {
            'file_path': str(self.file_path),
            'exists': self.file_path.exists(),
            'last_modified': datetime.fromtimestamp(self.last_modified).isoformat() 
                            if self.last_modified > 0 else None,
            'monitoring': True
        }
    
    def reset(self):
        """Réinitialise le watcher (utile pour forcer une nouvelle lecture)."""
        self.last_modified = 0
        self.last_content = ""


# === FONCTIONS UTILITAIRES ===

def test_parser():
    """Fonction de test pour vérifier le parsing de différents formats."""
    
    test_cases = [
        ("Simple", "Conversion: 85.5%"),
        ("Avec TON", "Conversion = 91.2%\nTON: 45.6"),
        ("JSON", '{"conversion": 88.4, "TON": 52.1}'),
        ("Détaillé", """
            === RÉSULTATS ===
            Conversion: 76.8%
            Turnover number: 38.9
            Selectivity: 92.3%
        """),
        ("Format clé=valeur", """
            conversion = 82.5
            ton = 41.2
            selectivity = 95.1
        """),
    ]
    
    watcher = ResultFileWatcher("dummy.txt")
    
    print("🧪 Test du parser de résultats:\n")
    for name, test_content in test_cases:
        result = watcher.parse_result_file(test_content)
        print(f"Test '{name}':")
        print(f"   Input: {test_content[:50]}...")
        print(f"   Résultat: {result}\n")


if __name__ == "__main__":
    # Exécuter les tests
    test_parser()
    
    # Exemple d'utilisation
    print("\n" + "="*60)
    print("📝 EXEMPLE D'UTILISATION")
    print("="*60 + "\n")
    
    # Créer un fichier de test
    with open("test_results.txt", "w") as f:
        f.write("Conversion: 87.3%\nTON: 45.2\n")
    
    # Utiliser le watcher
    watcher = ResultFileWatcher("test_results.txt")
    result = watcher.check_for_updates()
    
    if result:
        print(f"✅ Résultats détectés:")
        for key, value in result.items():
            print(f"   {key}: {value}")
    
    # Nettoyer
    import os
    os.remove("test_results.txt")