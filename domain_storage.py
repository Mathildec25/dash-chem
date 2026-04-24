"""Persistence helpers for saving and loading optimization domains."""

import json
import os
import pickle

from config_path import DOMAIN_FOLDER


class DomainStorage:
    """Save / load BoFire domains and their metadata next to each Excel file."""

    @staticmethod
    def get_domain_path(excel_name):
        """Return the pickle path used to store the domain for ``excel_name``."""
        base_name = excel_name.replace(".xlsx", "").replace(".xls", "")
        return os.path.join(DOMAIN_FOLDER, f"{base_name}_domain.pkl")

    @staticmethod
    def get_metadata_path(excel_name):
        """Return the JSON path used to store the metadata for ``excel_name``."""
        base_name = excel_name.replace(".xlsx", "").replace(".xls", "")
        return os.path.join(DOMAIN_FOLDER, f"{base_name}_metadata.json")

    @staticmethod
    def save_domain(excel_name, domain, parameters, objectives, extra_columns=None, metadata=None):
        """
        Pickle ``domain`` and write the companion metadata JSON.

        Returns:
            ``(success: bool, message: str)``.
        """
        try:
            os.makedirs(DOMAIN_FOLDER, exist_ok=True)

            with open(DomainStorage.get_domain_path(excel_name), "wb") as f:
                pickle.dump(domain, f)

            meta_data = {
                "excel_name": excel_name,
                "parameters": parameters,
                "objectives": objectives,
                "extra_columns": extra_columns or [],
                "metadata": metadata or {},
            }
            with open(DomainStorage.get_metadata_path(excel_name), "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)

            return True, "Domain saved successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def load_domain(excel_name):
        """
        Load the domain+metadata for ``excel_name``.

        Returns a dict with keys ``domain``, ``parameters``, ``objectives``,
        ``extra_columns``, ``metadata`` — or ``None`` if the metadata file is
        missing. ``domain`` is set to ``None`` when only metadata exists.
        """
        try:
            meta_path = DomainStorage.get_metadata_path(excel_name)
            if not os.path.exists(meta_path):
                return None

            with open(meta_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            domain_path = DomainStorage.get_domain_path(excel_name)
            if os.path.exists(domain_path):
                with open(domain_path, "rb") as f:
                    data["domain"] = pickle.load(f)
            else:
                data["domain"] = None

            return data
        except Exception as e:
            print(f"Error loading domain: {e}")
            return None

    @staticmethod
    def update_metadata(excel_name, key, value):
        """
        Set ``metadata[key] = value`` in the companion JSON without touching
        the domain pickle. ``value`` must be JSON-serialisable.

        Returns:
            ``(success: bool, message: str)``.
        """
        try:
            meta_path = DomainStorage.get_metadata_path(excel_name)
            if not os.path.exists(meta_path):
                return False, f"Metadata file not found: {meta_path}"

            with open(meta_path, "r", encoding="utf-8") as f:
                meta_data = json.load(f)

            meta_data[key] = value

            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, indent=2, ensure_ascii=False)

            return True, f"Metadata key '{key}' updated successfully"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def delete_domain(excel_name):
        """Delete the domain and metadata files for ``excel_name``."""
        try:
            for path in (
                DomainStorage.get_domain_path(excel_name),
                DomainStorage.get_metadata_path(excel_name),
            ):
                if os.path.exists(path):
                    os.remove(path)
            return True
        except Exception:
            return False

    @staticmethod
    def list_domains():
        """Return the ``excel_name`` of every saved domain found in DOMAIN_FOLDER."""
        domains = []
        if not os.path.exists(DOMAIN_FOLDER):
            return domains

        for file in os.listdir(DOMAIN_FOLDER):
            if not file.endswith("_metadata.json"):
                continue
            try:
                with open(os.path.join(DOMAIN_FOLDER, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                domains.append(data.get("excel_name", file))
            except Exception:
                continue
        return domains


def check_domain_availability(excel_name):
    """Return True if a metadata file exists for ``excel_name``."""
    return os.path.exists(DomainStorage.get_metadata_path(excel_name))
