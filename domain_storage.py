"""
Domain Storage - Save and load optimization domains
"""

import os
import json
import pickle
from config_path import DOMAIN_FOLDER


class DomainStorage:
    """Handle saving and loading of optimization domains"""
    
    @staticmethod
    def get_domain_path(excel_name):
        """Get the path for domain storage based on excel filename"""
        base_name = excel_name.replace('.xlsx', '').replace('.xls', '')
        return os.path.join(DOMAIN_FOLDER, f"{base_name}_domain.pkl")
    
    @staticmethod
    def get_metadata_path(excel_name):
        """Get the path for metadata storage"""
        base_name = excel_name.replace('.xlsx', '').replace('.xls', '')
        return os.path.join(DOMAIN_FOLDER, f"{base_name}_metadata.json")
    
    @staticmethod
    def save_domain(excel_name, domain, parameters, objectives, extra_columns=None, metadata=None):
        """
        Save domain and associated data
        
        Args:
            excel_name: Name of the Excel file
            domain: BoFire domain object
            parameters: List of parameter definitions
            objectives: List of objective definitions
            extra_columns: Optional list of extra column definitions
            metadata: Optional additional metadata
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            os.makedirs(DOMAIN_FOLDER, exist_ok=True)
            
            # Save domain object with pickle
            domain_path = DomainStorage.get_domain_path(excel_name)
            with open(domain_path, 'wb') as f:
                pickle.dump(domain, f)
            
            # Save metadata as JSON
            meta_path = DomainStorage.get_metadata_path(excel_name)
            meta_data = {
                'excel_name': excel_name,
                'parameters': parameters,
                'objectives': objectives,
                'extra_columns': extra_columns or [],
                'metadata': metadata or {}
            }
            
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)
            
            return True, "Domain saved successfully"
        
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def load_domain(excel_name):
        """
        Load domain and associated data
        
        Args:
            excel_name: Name of the Excel file
        
        Returns:
            dict with domain, parameters, objectives, etc. or None if not found
        """
        try:
            domain_path = DomainStorage.get_domain_path(excel_name)
            meta_path = DomainStorage.get_metadata_path(excel_name)
            
            if not os.path.exists(meta_path):
                return None
            
            # Load metadata
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Load domain object
            if os.path.exists(domain_path):
                with open(domain_path, 'rb') as f:
                    data['domain'] = pickle.load(f)
            else:
                data['domain'] = None
            
            return data
        
        except Exception as e:
            print(f"Error loading domain: {e}")
            return None
    
    @staticmethod
    def delete_domain(excel_name):
        """Delete domain files"""
        try:
            domain_path = DomainStorage.get_domain_path(excel_name)
            meta_path = DomainStorage.get_metadata_path(excel_name)
            
            if os.path.exists(domain_path):
                os.remove(domain_path)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            
            return True
        except:
            return False
    
    @staticmethod
    def list_domains():
        """List all saved domains"""
        domains = []
        
        if not os.path.exists(DOMAIN_FOLDER):
            return domains
        
        for file in os.listdir(DOMAIN_FOLDER):
            if file.endswith('_metadata.json'):
                try:
                    path = os.path.join(DOMAIN_FOLDER, file)
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    domains.append(data.get('excel_name', file))
                except:
                    pass
        
        return domains


def check_domain_availability(excel_name):
    """
    Check if a domain exists for a given Excel file
    
    Args:
        excel_name: Name of the Excel file
    
    Returns:
        bool: True if domain exists, False otherwise
    """
    meta_path = DomainStorage.get_metadata_path(excel_name)
    return os.path.exists(meta_path)