import json
import os
from pathlib import Path

class ContactsService:
    def __init__(self, json_path=None):
        if json_path is None:
            # Default to the contacts file in the sow_components directory
            json_path = Path(__file__).parent.parent / "contacts_data.json"
        
        with open(json_path, "r") as f:
            self.data = json.load(f)

    def get_client_contact(self, company_name):
        """Get client contact by company name (case-insensitive)"""
        for name, details in self.data["clients"].items():
            if name.lower() == company_name.lower():
                return details
        return None

    def get_contractor_contact(self, company_name):
        """Get contractor contact by company name (case-insensitive)"""
        for name, details in self.data["contractors"].items():
            if name.lower() == company_name.lower():
                return details
        return None
    
    def get_all_clients(self):
        """Get all available client companies"""
        return list(self.data["clients"].keys())
    
    def get_all_contractors(self):
        """Get all available contractor companies"""
        return list(self.data["contractors"].keys())